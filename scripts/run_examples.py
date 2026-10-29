"""生成真实执行的离线输入、输出和Trace；不生成伪造的真实模型验证材料。"""
import copy
import csv
import hashlib
import json
import platform
import sys
import time
from datetime import datetime,timezone
import xml.etree.ElementTree as ET
from importlib.metadata import version
from pathlib import Path

from knowledge_agent.agent import Agent
from knowledge_agent.backends import MockBackend
from knowledge_agent.cli import write_json
from knowledge_agent.models import Request
from knowledge_agent.store import KnowledgeStore,ToolExecutor


ROOT=Path(__file__).resolve().parents[1]


def run_all():
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    started=time.perf_counter()
    examples=ROOT/"examples"
    for folder in ("inputs","outputs","traces","fixtures"):
        (examples/folder).mkdir(parents=True,exist_ok=True)
    base=json.loads((ROOT/"data/corpus.json").read_text(encoding="utf-8"))
    single=copy.deepcopy(base)
    single["documents"]=[d for d in single["documents"] if d["doc_id"]!="D02"]
    changed=copy.deepcopy(single)
    passage=next(d for d in changed["documents"] if d["doc_id"]=="D01")["passages"][0]
    passage["text"]=passage["text"].replace("30个自然日","21个自然日")
    passage["fact_value"]="21个自然日"
    write_json(examples/"fixtures/single_policy.json",single)
    write_json(examples/"fixtures/changed_policy.json",changed)
    cases=[
        {"id":"01_clear","label":"明确答案","question":"正式员工年假最小可以请多久？","expected":"answered","requirements":["A01"]},
        {"id":"02_conflict","label":"制度冲突","question":"报销申请的提交期限是多久？","expected":"conflict","requirements":["A02"]},
        {"id":"03_outside","label":"资料外问题","question":"火星基地今天的氧气库存是多少？","expected":"insufficient_evidence","requirements":["A03"]},
        {"id":"04_paraphrase","label":"改写问法","question":"我想休半天年假，制度允许吗？","expected":"answered","requirements":["A04"]},
        {"id":"05_context","label":"上下文追问","question":"那实习生可以申请吗？","expected":"answered","requirements":["A05"],"use_history":True},
        {"id":"06_missing_context","label":"缺少制度主题","question":"那实习生可以申请吗？","expected":"needs_clarification","requirements":["A05"]},
        {"id":"07_tool_recovery","label":"检索失败后换查询","question":"正式员工年假最小可以请多久？","expected":"answered","requirements":["A06"],"fail_once":"search_documents"},
        {"id":"08_tool_failure","label":"工具持续失败","question":"正式员工年假最小可以请多久？","expected":"tool_error","requirements":["A06"],"always_fail":"search_documents"},
        {"id":"09_read_recovery","label":"原文读取临时失败","question":"正式员工年假最小可以请多久？","expected":"answered","requirements":["A06"],"fail_once":"read_passage"},
        {"id":"10_step_limit","label":"步数上限","question":"正式员工年假最小可以请多久？","expected":"limit_reached","requirements":["A07"],"max_steps":1},
        {"id":"11_call_limit","label":"工具调用上限","question":"正式员工年假最小可以请多久？","expected":"limit_reached","requirements":["A07"],"max_tool_calls":1},
        {"id":"12_single_policy","label":"移除冲突文档","question":"报销申请的提交期限是多久？","expected":"answered","requirements":["A09"],"corpus":"examples/fixtures/single_policy.json"},
        {"id":"13_changed_policy","label":"替换为21天制度","question":"报销申请的提交期限是多久？","expected":"answered","requirements":["A09"],"corpus":"examples/fixtures/changed_policy.json"},
    ]
    rows=[]
    bundles={}
    for case in cases:
        history=[]
        if case.get("use_history"):
            history=[{"role":"user","content":cases[0]["question"]},
                     {"role":"assistant","content":bundles["01_clear"].result.answer}]
            write_json(examples/"inputs/context_history.json",history)
        request=Request(question=case["question"],history=history)
        corpus_relative=case.get("corpus","data/corpus.json")
        inputs={"request":request.model_dump(),"mode":"mock","corpus":corpus_relative,
                "max_steps":case.get("max_steps",8),"max_tool_calls":case.get("max_tool_calls",6),
                "fail_once":case.get("fail_once"),"always_fail":case.get("always_fail")}
        write_json(examples/"inputs"/f"{case['id']}.json",inputs)
        store=KnowledgeStore(ROOT/corpus_relative,ROOT/"data/aliases.json")
        try:
            tools=ToolExecutor(store,inputs["fail_once"],inputs["always_fail"])
            bundle=Agent(MockBackend(),tools,inputs["max_steps"],inputs["max_tool_calls"]).run(
                request,examples/"traces"/f"{case['id']}.jsonl")
        finally:
            store.close()
        bundles[case["id"]]=bundle
        result=bundle.result
        write_json(examples/"outputs"/f"{case['id']}.json",result.model_dump())
        decisions=[e["decision"] for e in bundle.events if e["event"]=="decision"]
        passed=result.status==case["expected"]
        if case["id"]=="02_conflict":
            passed=passed and {c.doc_id for c in result.citations}=={"D01","D02"} and bool(result.clarification)
        if case["id"]=="07_tool_recovery":
            search=[e for e in bundle.events if e["event"]=="tool_observation" and e["tool"]=="search_documents"]
            passed=passed and len(search)==2 and search[0]["arguments"]!=search[1]["arguments"] and not search[0]["observation"]["ok"]
        if case["id"]=="13_changed_policy":
            passed=passed and "21个自然日" in result.answer and "30个自然日" not in result.answer
        rows.append({"id":case["id"],"label":case["label"],"requirements":case["requirements"],
                     "expected_status":case["expected"],"actual_status":result.status,"passed":passed,
                     "decision_steps":result.decision_steps,"tool_calls":result.tool_calls,
                     "action_sequence":[d["action"] for d in decisions],"model_mode":result.model_mode,
                     "input":f"inputs/{case['id']}.json","output":f"outputs/{case['id']}.json",
                     "trace":f"traces/{case['id']}.jsonl","elapsed_ms":result.elapsed_ms})
        print(f"{case['id']}: {result.status}, steps={result.decision_steps}, calls={result.tool_calls}, passed={passed}")
    test_record={"status":"not_recorded"}
    test_path=examples/"test-results.xml"
    if test_path.exists():
        suites=ET.parse(test_path).getroot()
        totals={key:sum(int(s.get(key,0)) for s in suites.iter("testsuite")) for key in ("tests","failures","errors","skipped")}
        test_record={"status":"passed" if totals["failures"]+totals["errors"]==0 else "failed",**totals,"source":"test-results.xml"}
    tracked=list((ROOT/"src").rglob("*.py"))+list((ROOT/"tests").glob("*.py"))+list((ROOT/"data").glob("*.json"))+list((ROOT/"scripts").glob("*.py"))
    plan_stat=(ROOT/"docs/00-plan.md").stat()
    first_artifact_time=getattr(plan_stat,"st_birthtime",plan_stat.st_mtime)
    summary={"mode":"offline_mock","live_model_validated":False,
             "corpus":{"documents":len(base["documents"]),"passages":sum(len(d["passages"]) for d in base["documents"])},
             "scope":"本文件仅汇总离线Mock；真实模型实际结果单独见live/summary.json，不能混记两种模式。",
             "total":len(rows),"passed":sum(r["passed"] for r in rows),"cases":rows,"tests":test_record,
             "execution_seconds":round(time.perf_counter()-started,4),
             "timing_scope":"仅统计本脚本生成并验证案例的执行时间，不代表项目开发用时或笔试平台计时。",
             "implementation_window":{"first_plan_file_created_utc":datetime.fromtimestamp(first_artifact_time,timezone.utc).isoformat(),
                                      "verification_finished_utc":datetime.now(timezone.utc).isoformat(),
                                      "seconds":round(max(0,time.time()-first_artifact_time),2),
                                      "scope":"首份规划文档创建至本次验证结束的本地文件实现窗口；不含此前阅读讨论，非完整答题用时或平台计时。"},
             "runtime":{"executable":sys.executable,"python":platform.python_version(),
                        "dependencies":{name:version(name) for name in ("pydantic","httpx","python-dotenv","pytest")}},
             "source_sha256":{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}}
    previous_path=examples/"summary.json"
    if previous_path.exists():
        previous=json.loads(previous_path.read_text(encoding="utf-8"))
        if previous.get("implementation_window"):
            summary["implementation_window"]=previous["implementation_window"]
    summary["verification_finished_utc"]=datetime.now(timezone.utc).isoformat()
    summary["live_results"]="live/summary.json" if (examples/"live/summary.json").exists() else None
    write_json(previous_path,summary)
    with (examples/"cases.csv").open("w",encoding="utf-8-sig",newline="") as f:
        writer=csv.writer(f)
        writer.writerow(["case","expected","actual","passed","steps","tool_calls","mode"])
        for r in rows:
            writer.writerow([r["id"],r["expected_status"],r["actual_status"],r["passed"],r["decision_steps"],r["tool_calls"],r["model_mode"]])
    render_review(examples,rows,bundles)
    render_evaluation(rows,summary)
    if summary["passed"]!=summary["total"] or test_record["status"]=="failed":
        raise SystemExit("存在未通过案例或测试，未标记验收完成。")
    print(f"Saved {len(rows)} actual Mock runs. Live results are evaluated separately.")


def render_review(examples,rows,bundles):
    lines=["# 离线运行Trace审阅", "", "以下记录均来自程序实际执行；模式offline_mock，不是真实模型决策证明。",
           "", "重点比较01明确答案、02制度冲突、03资料外问题、07检索失败恢复的工具路径。完整事件含观察原文，见JSONL文件。"]
    for row in rows:
        bundle=bundles[row["id"]]
        lines += ["",f"## {row['id']}：{row['label']}","",f"输入：{bundle.result.question}","",
                  f"终态：`{bundle.result.status}`；决策{bundle.result.decision_steps}步，工具{bundle.result.tool_calls}次。",
                  "",f"[输入]({row['input']}) · [实际输出]({row['output']}) · [完整Trace]({row['trace']})","",
                  "|步骤|事件|内容|","|---:|---|---|"]
        for event in bundle.events:
            if event["event"]=="decision":
                d=event["decision"]
                arg=d.get("query") or d.get("passage_id") or d.get("status")
                text=f"{d['action']}({arg})；{d['reason']}"
            elif event["event"]=="tool_observation":
                obs=event["observation"]
                if not obs["ok"]:
                    text="失败："+obs["error"]["code"]
                elif event["tool"]=="search_documents":
                    text="命中："+(", ".join(h["passage_id"] for h in obs["result"]["hits"]) or "无")
                else:
                    text="已读："+obs["result"]["passage_id"]
            elif event["event"]=="policy_observation":
                text=event["observation"]["code"]
            else:
                continue
            lines.append(f"|{event['step']}|{event['event']}|{text.replace('|','/')}|")
        lines += ["","实际回答：", "",bundle.result.answer]
    (examples/"trace_review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def render_evaluation(rows,summary):
    tests=summary["tests"]
    test_line=(f"pytest记录：{tests['tests']}项，失败{tests['failures']}项、错误{tests['errors']}项、跳过{tests['skipped']}项。"
               if "tests" in tests else "尚无落盘pytest记录；请运行pytest并保存JUnit XML后重新生成。")
    live_path=ROOT/"examples/live/summary.json"
    live=json.loads(live_path.read_text(encoding="utf-8")) if live_path.exists() else None
    live_ok=bool(live and live.get("live_model_validated"))
    live_statement=(f"**真实模型已接入并完成本地场景验证：DeepSeek / {live['model']}，{live['passed']}/{live['total']}通过。** 模型决策请求{live['model_requests']}次、HTTP尝试{live.get('http_attempts',live['model_requests'])}次，已返回的用量合计{live['total_tokens']} token；这是单轮场景结果，不代表随机重复稳定性。"
                    if live_ok else "**真实模型尚未完整通过验收。** 当前通过情况见真实运行清单；Mock结果不能替代真实模型验证。")
    lines=["# 评估与验证记录","", "## 本轮结论","",
           f"13类离线场景实际执行：{summary['passed']}/{summary['total']}符合预期。{test_line}","",
           "使用hj13环境；具体解释器、依赖版本、源码SHA-256、计时范围见 [summary.json](../examples/summary.json)。",
           "",live_statement,
           "", "## 离线验收与材料对应","", "|案例 / 验收点|预期 / 实际|步数 / 工具次数|材料|","|---|---|---|---|"]
    for r in rows:
        links=f"[输入](../examples/{r['input']}) · [输出](../examples/{r['output']}) · [Trace](../examples/{r['trace']})"
        lines.append(f"|{r['label']} / {','.join(r['requirements'])}|{r['expected_status']} / {r['actual_status']}|{r['decision_steps']} / {r['tool_calls']}|{links}|")
    if live:
        prefix="../examples/live/"+live["run_folder"]+"/"
        lines += ["","## 真实模型验收与材料对应","",f"模型：{live['model']}；核验时间UTC：{live['verified_at_utc']}。",
                  "",f"[真实汇总](../examples/live/summary.json) · [逐步审阅]({prefix}trace_review.md)","",
                  "|场景 / 验收点|预期 / 实际|模型请求 / 工具调用|材料|","|---|---|---|---|"]
        for r in live["cases"]:
            links=f"[输入]({prefix}{r['input']}) · [输出]({prefix}{r['output']}) · [Trace]({prefix}{r['trace']})"
            lines.append(f"|{r['label']} / {','.join(r['requirements'])}|{r['expected_status']} / {r['actual_status']}|{r['model_requests']} / {r['tool_calls']}|{links}|")
        lines += ["","Trace中的model_response只记录模型名、响应ID、HTTP状态、token用量及耗时；真实模型动作与工具观察相间出现。业务工具故障为明确注入，不冒充DeepSeek接口故障。"]
        attempts=[]
        for p in sorted((ROOT/"examples/live/runs").glob("*/summary.json")):
            a=json.loads(p.read_text(encoding="utf-8"))
            attempts.append((p,a))
        lines += ["","## 真实模型尝试记录（包含失败）","","|归档|范围|实际通过|未通过案例|","|---|---|---|---|"]
        for p,a in attempts:
            link="../"+p.relative_to(ROOT).as_posix()
            failed=", ".join(r["id"] for r in a["cases"] if not r["passed"]) or "无"
            lines.append(f"|[原始汇总]({link})|{'全套' if a['full_suite'] else '定向复测'}|{a['passed']}/{a['total']}|{failed}|")
    lines += ["", "A08（引用校验）、A11（资料和工具边界）由tests/test_guards.py覆盖；A10的完整记录和路径差异由生成脚本及tests/test_acceptance.py核对。",
              "", "## 路径差异","",
              "- 明确答案：检索 → 读取一条原文 → 摘录回答。",
              "- 制度冲突：检索 → 读取两条期限制度 → 列双方引用并澄清。",
              "- 资料外：检索无相关依据 → 改写查询 → 仍无依据则停止。",
              "- 临时故障：第一次检索失败 → 改为短查询 → 读取 → 回答；没有工具内部自动重试。",
              "- 持续故障：再次失败后返回tool_error，complete=false。",
              "- 资料替换：去掉D02后答30天；将D01替换成21天后答案也变为21天。",
              "", "可读逐步记录见 [Trace审阅](../examples/trace_review.md)。",
              "", "## 实际发现和修复","",
              "第一轮测试44项中43项通过：英文annual leave能被检索别名召回，但Mock意图选择没有同样归一，导致错误返回资料不足。补齐适配器对该别名的处理后回归；中文改写、英文别名和资料替换均有专门测试。",
              "", "测试还主动使用测试替身尝试引用未读文档、改写数字、只引用冲突的一方、声明不存在的工具故障以及发出shell动作；运行时应拒绝或返回明确未完成状态。这些是边界测试，不是假装真实模型进行了这些行为。",
              "", "## 已知限制与未完成项","",
              "1. 已验证的真实模型结果只覆盖本次指定场景；随机重复稳定性、更广措辞和其他提供商兼容性未作完整评估。",
              "2. FTS5和显式别名适合本例小语料；不保证开放域语义召回。Mock只认识演示领域的有限意图。",
              "3. 冲突检查依赖人工事实标注及当前已检索/读取候选；遗漏的文档或未标注的语义冲突可能无法识别。",
              "4. 原文摘录和事实值校验保证引用真实性，不自动证明对所有开放式问题的相关性或语义充分性。",
              "5. 未做企业权限、文档生命周期和生产部署；未上传GitHub。",
              "6. 候选人本人的手工审阅和修改仍待如实补记，不能把AI生成工作写成个人独立贡献。",
              "", "## 真实模型问题及修复","",
              "第一轮完整真实调用为12/13：上下文追问被误判为缺少主题。原记录保留，没有改写失败。将历史从嵌套JSON调整为正式user/assistant消息，并把澄清条件改为结合历史后仍不能确定主题；增加HTTP消息结构回归测试，然后进行定向和全套真实复测。",
              "", "只修复历史格式后，进一步观察到无历史时模型会凭实习生身份猜测年假主题；这一失败也保留在归档。随后明确区分适用对象与业务主题：身份不能充当申请对象；主题可从真实历史继承。两个相反边界一起复测，不通过放宽预期或修改输出解决问题。",
              "", "另一轮真实运行遇到一次在收到HTTP响应前发生的连接失败，原model_error记录保留。传输层增加最多2次尝试，只对网络错误或429/502/503/504重试；鉴权/余额错误及无效模型动作不重试。每次尝试记录状态或异常类型，业务工具的失败恢复仍由模型独立决策。另增加证据约束：未成功搜索时不能断言资料库没有依据。",
              "", "## 本地完成与提交的边界","",
              "本地材料是否齐备见docs/06-submission-checklist.md。GitHub URL、最终commit SHA及可能需要的私有仓库访问权限尚未生成，按用户指令等待后续上传命令。个人审阅记录只由候选人按实际操作补记。"]
    (ROOT/"docs/03-evaluation.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


if __name__=="__main__":
    run_all()
