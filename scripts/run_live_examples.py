"""逐例调用真实接口；所有尝试原样归档，不用Mock替换失败结果。"""
import argparse
import hashlib
import json
import platform
import sys
import time
from datetime import datetime,timezone
from pathlib import Path
from uuid import uuid4

from knowledge_agent.agent import Agent
from knowledge_agent.backends import LiveBackend,LiveConfig
from knowledge_agent.cli import write_json
from knowledge_agent.credentials import read_api_key_file
from knowledge_agent.models import Request
from knowledge_agent.store import KnowledgeStore,ToolExecutor


ROOT=Path(__file__).resolve().parents[1]


def evaluate_case(case_id,result,events,expected):
    errors=[]
    if result.status!=expected:
        errors.append(f"预期{expected}，实际{result.status}")
    if result.model_mode!="live":
        errors.append("不是live模式")
    metadata=[e["metadata"] for e in events if e["event"]=="model_response"]
    if len(metadata)!=result.decision_steps or any(m.get("http_status")!=200 or not m.get("response_id") for m in metadata):
        errors.append("真实模型HTTP响应证据不完整")
    reads={e["observation"]["result"]["passage_id"]:e["observation"]["result"]
           for e in events if e["event"]=="tool_observation" and e["tool"]=="read_passage" and e["observation"]["ok"]}
    for citation in result.citations:
        if citation.passage_id not in reads or citation.quote not in reads[citation.passage_id]["text"]:
            errors.append("引用不是本轮已读原文")
    cited={c.passage_id for c in result.citations}
    if case_id in {"01_clear","04_paraphrase","07_tool_recovery","09_read_recovery"}:
        if "D03:P01" not in cited or "0.5天" not in result.answer:
            errors.append("未依据年假最小单位原文回答")
    if case_id=="02_conflict":
        if not {"D01:P01","D02:P01"}.issubset(cited) or not result.clarification or result.complete:
            errors.append("冲突双方引用、待确认状态或澄清问题不完整")
    if case_id=="03_outside" and (result.citations or result.complete or not result.gaps):
        errors.append("资料外问题未正确保留证据缺口")
    if case_id=="03_outside" and not any(e["event"]=="tool_observation" and e["tool"]=="search_documents" and e["observation"]["ok"] for e in events):
        errors.append("没有实际检索就声称资料不足")
    if case_id=="05_context" and ("D05:P01" not in cited or "不适用" not in result.answer):
        errors.append("上下文追问未依据实习生年假说明")
    if case_id=="06_missing_context" and not result.clarification:
        errors.append("缺主题时未提出具体澄清问题")
    if case_id=="07_tool_recovery":
        searches=[e for e in events if e["event"]=="tool_observation" and e["tool"]=="search_documents"]
        if len(searches)<2 or searches[0]["observation"]["ok"] or not any(e["observation"]["ok"] for e in searches[1:]):
            errors.append("没有观察故障后恢复检索的路径")
        elif searches[0]["arguments"]["query"]==searches[1]["arguments"]["query"]:
            errors.append("故障后没有调整查询")
    if case_id in {"08_tool_failure","10_step_limit","11_call_limit"} and (result.complete or not result.gaps):
        errors.append("失败或上限未返回明确未完成状态")
    if case_id in {"12_single_policy","13_changed_policy"}:
        value="30个自然日" if case_id=="12_single_policy" else "21个自然日"
        if "D01:P01" not in cited or value not in result.answer or "D02:P01" in cited:
            errors.append("答案没有随实际资料变更")
    return errors,metadata


def render_review(folder,rows,bundles):
    lines=["# DeepSeek真实模型逐步运行记录","", "所有动作来自实际HTTP响应；业务检索和读取在本地真实执行。故障由显式测试注入；未使用Mock模型。",
           "", "记录简短动作目的、工具参数、观察和结果；不保存reasoning_content、密钥或HTTP请求头。"]
    for row in rows:
        bundle=bundles[row["id"]]
        lines += ["",f"## {row['id']}：{row['label']}","",f"状态：`{row['actual_status']}`；校验：{'通过' if row['passed'] else '未通过'}。",
                  "",f"[输入]({row['input']}) · [输出]({row['output']}) · [Trace]({row['trace']})","",
                  "|步骤|动作或观察|内容|","|---:|---|---|"]
        for e in bundle.events:
            if e["event"]=="model_response":
                m=e["metadata"]
                text=f"模型{m.get('returned_model')}；响应ID {m.get('response_id')}；token {m.get('usage',{}).get('total_tokens','未提供')}"
            elif e["event"]=="decision":
                d=e["decision"]
                text=f"{d['action']}({d.get('query') or d.get('passage_id') or d.get('status')})；{d['reason']}"
            elif e["event"]=="tool_observation":
                obs=e["observation"]
                text=("失败："+obs["error"]["code"] if not obs["ok"] else
                      "命中："+(", ".join(h["passage_id"] for h in obs["result"]["hits"]) or "无")
                      if e["tool"]=="search_documents" else "已读："+obs["result"]["passage_id"])
            elif e["event"]=="policy_observation":
                text=e["observation"]["code"]+"："+e["observation"]["message"]
            else:
                continue
            lines.append(f"|{e['step']}|{e['event']}|{text.replace('|','/')}|")
        lines += ["","实际回答：","",bundle.result.answer]
        if row["errors"]:
            lines += ["","未通过原因："+"；".join(row["errors"])]
    (folder/"trace_review.md").write_text("\n".join(lines)+"\n",encoding="utf-8")


def main():
    if hasattr(sys.stdout,"reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key-file",type=Path,required=True)
    parser.add_argument("--base-url",default="https://api.deepseek.com")
    parser.add_argument("--model",default="deepseek-flash")
    parser.add_argument("--cases",help="可选逗号分隔案例ID；省略则运行全部13例")
    parser.add_argument("--timeout",type=float,default=45)
    args=parser.parse_args()
    source=json.loads((ROOT/"examples/summary.json").read_text(encoding="utf-8"))
    selected=set(args.cases.split(",")) if args.cases else None
    cases=[c for c in source["cases"] if selected is None or c["id"] in selected]
    if not cases or (selected and selected!={c["id"] for c in cases}):
        parser.error("案例ID无效")
    key=read_api_key_file(args.api_key_file)
    tracked=list((ROOT/"src").rglob("*.py"))+list((ROOT/"tests").glob("*.py"))+list((ROOT/"data").glob("*.json"))+list((ROOT/"scripts").glob("*.py"))
    source_hashes={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in tracked}
    started=time.perf_counter()
    run_stamp=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"_"+uuid4().hex[:4]
    folder=ROOT/"examples/live/runs"/run_stamp
    for name in ("inputs","outputs","traces"):
        (folder/name).mkdir(parents=True,exist_ok=True)
    print("Real model validation started; archive:",folder.relative_to(ROOT),flush=True)
    rows,bundles=[],{}
    for case in cases:
        case_id=case["id"]
        inputs=json.loads((ROOT/"examples"/case["input"]).read_text(encoding="utf-8"))
        inputs["mode"]="live"
        inputs["model"]=args.model
        inputs["base_url"]=args.base_url
        if case_id=="05_context" and "01_clear" in bundles:
            inputs["request"]["history"]=[{"role":"user","content":bundles["01_clear"].result.question},
                                           {"role":"assistant","content":bundles["01_clear"].result.answer}]
        write_json(folder/"inputs"/f"{case_id}.json",inputs)
        request=Request.model_validate(inputs["request"])
        config=LiveConfig(args.base_url,args.model,key,args.timeout,True,"disabled")
        store=KnowledgeStore(ROOT/inputs["corpus"],ROOT/"data/aliases.json")
        try:
            bundle=Agent(LiveBackend(config),ToolExecutor(store,inputs["fail_once"],inputs["always_fail"]),
                         inputs["max_steps"],inputs["max_tool_calls"]).run(request,folder/"traces"/f"{case_id}.jsonl")
        finally:
            store.close()
        bundles[case_id]=bundle
        write_json(folder/"outputs"/f"{case_id}.json",bundle.result.model_dump())
        errors,metadata=evaluate_case(case_id,bundle.result,bundle.events,case["expected_status"])
        rows.append({"id":case_id,"label":case["label"],"requirements":case["requirements"],
                     "expected_status":case["expected_status"],"actual_status":bundle.result.status,"passed":not errors,"errors":errors,
                     "input":f"inputs/{case_id}.json","output":f"outputs/{case_id}.json","trace":f"traces/{case_id}.jsonl",
                     "decision_steps":bundle.result.decision_steps,"tool_calls":bundle.result.tool_calls,
                     "action_sequence":[e["decision"]["action"] for e in bundle.events if e["event"]=="decision"],
                     "model_requests":len(metadata),"total_tokens":sum(m.get("usage",{}).get("total_tokens",0) for m in metadata),
                     "http_attempts":sum(len(m.get("attempts",[])) or 1 for m in metadata),
                     "elapsed_ms":bundle.result.elapsed_ms})
        print(f"{case_id}: {bundle.result.status}; checks={'PASS' if not errors else 'FAIL'}; steps={bundle.result.decision_steps}; calls={bundle.result.tool_calls}",flush=True)
        if errors:
            print("  "+"；".join(errors),flush=True)
    paths={tuple(r["action_sequence"]) for r in rows}
    full_suite=len(cases)==len(source["cases"])
    passed=sum(r["passed"] for r in rows)
    summary={"mode":"live","provider":"DeepSeek","model":args.model,"base_url":args.base_url,
             "verified_at_utc":datetime.now(timezone.utc).isoformat(),"run_folder":folder.relative_to(ROOT/"examples/live").as_posix(),
             "full_suite":full_suite,"live_model_validated":full_suite and passed==len(cases) and len(paths)>=2,
             "total":len(rows),"passed":passed,"distinct_action_sequences":len(paths),"cases":rows,
             "model_requests":sum(r["model_requests"] for r in rows),"total_tokens":sum(r["total_tokens"] for r in rows),
             "http_attempts":sum(r["http_attempts"] for r in rows),
             "execution_seconds":round(time.perf_counter()-started,3),
             "runtime":{"executable":sys.executable,"python":platform.python_version()},
             "boundary":"真实模型单轮验收结果，不等于随机重复稳定性或生产质量保证；故障为本地业务工具显式注入。",
             "source_sha256":source_hashes}
    write_json(folder/"summary.json",summary)
    render_review(folder,rows,bundles)
    write_json(ROOT/"examples/live/latest_attempt.json",summary)
    if full_suite:
        write_json(ROOT/"examples/live/summary.json",summary)
    print(f"Actual live checks: {passed}/{len(rows)}. Requests={summary['model_requests']}. Tokens={summary['total_tokens']}.",flush=True)
    return 0 if passed==len(rows) else 1


if __name__=="__main__":
    raise SystemExit(main())
