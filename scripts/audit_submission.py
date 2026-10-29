"""本地交付核对：文件、真实运行证据、源码指纹、引用与密钥泄漏；不访问GitHub。"""
import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from knowledge_agent.cli import write_json
from knowledge_agent.credentials import read_api_key_file


ROOT=Path(__file__).resolve().parents[1]


def audit(key_file):
    failures=[]
    required=["README.md","requirements.txt","pyproject.toml",".env.example",*[f"docs/0{i}-{name}.md" for i,name in
              [(1,"requirements"),(2,"solution"),(3,"evaluation"),(4,"ai-usage"),(5,"retrospective")]]]
    for name in required:
        if not (ROOT/name).is_file():
            failures.append("缺少规定文件："+name)
    for name in ("src/knowledge_agent","tests","data","examples/inputs","examples/outputs","examples/traces"):
        if not (ROOT/name).is_dir() or not any((ROOT/name).iterdir()):
            failures.append("缺少规定目录或目录为空："+name)
    tests_root=ET.parse(ROOT/"examples/test-results.xml").getroot()
    tests={k:sum(int(s.get(k,0)) for s in tests_root.iter("testsuite")) for k in ("tests","failures","errors","skipped")}
    if not tests["tests"] or tests["failures"] or tests["errors"] or tests["skipped"]:
        failures.append("可执行测试未全部通过")
    offline=json.loads((ROOT/"examples/summary.json").read_text(encoding="utf-8"))
    live=json.loads((ROOT/"examples/live/summary.json").read_text(encoding="utf-8"))
    if offline["passed"]!=offline["total"] or offline["total"]<3:
        failures.append("离线场景没有完整通过")
    if not live.get("live_model_validated") or not live.get("full_suite") or live["passed"]!=live["total"]:
        failures.append("真实模型全套场景没有完整通过")
    if live["distinct_action_sequences"]<2:
        failures.append("缺少至少两条不同真实动作路径")
    folder=ROOT/"examples/live"/live["run_folder"]
    total_responses=0
    for case in live["cases"]:
        output=json.loads((folder/case["output"]).read_text(encoding="utf-8"))
        events=[json.loads(line) for line in (folder/case["trace"]).read_text(encoding="utf-8").splitlines()]
        if not events or events[-1].get("result")!=output or output["model_mode"]!="live":
            failures.append("真实Trace与结果不一致："+case["id"])
            continue
        responses=[e["metadata"] for e in events if e["event"]=="model_response"]
        total_responses+=len(responses)
        if len(responses)!=output["decision_steps"] or any(m.get("http_status")!=200 or not m.get("response_id") for m in responses):
            failures.append("真实HTTP证据不完整："+case["id"])
        read={e["observation"]["result"]["passage_id"]:e["observation"]["result"] for e in events
              if e["event"]=="tool_observation" and e["tool"]=="read_passage" and e["observation"]["ok"]}
        for c in output["citations"]:
            if c["passage_id"] not in read or c["quote"] not in read[c["passage_id"]]["text"]:
                failures.append("存在非本轮原文引用："+case["id"])
        if output["complete"]!=(output["status"]=="answered"):
            failures.append("完成状态与任务终态不一致："+case["id"])
    for label,summary in (("offline",offline),("live",live)):
        for name,digest in summary["source_sha256"].items():
            path=ROOT/name
            if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:
                failures.append(f"{label}记录源码已变化：{name}")
    broken=[]
    for path in [ROOT/"README.md",*ROOT.glob("docs/*.md"),ROOT/"examples/trace_review.md",folder/"trace_review.md"]:
        for target in re.findall(r"\]\(([^)]+)\)",path.read_text(encoding="utf-8")):
            if not target.startswith(("http:","https:","#")) and not (path.parent/target.split("#")[0]).exists():
                broken.append(f"{path.relative_to(ROOT)} -> {target}")
    failures.extend("文档链接无效："+name for name in broken)
    key=read_api_key_file(key_file).encode("utf-8")
    leaking=[]
    inspected=0
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        inspected+=1
        content=path.read_bytes()
        if key in content:
            leaking.append(path.relative_to(ROOT).as_posix())
    if leaking:
        failures.append("存在密钥内容泄漏，文件："+", ".join(leaking))
    if (ROOT/".env").exists() or (ROOT/"api.txt").exists():
        failures.append("项目根目录存在本地密钥配置文件，需移出交付范围")
    report={"local_ready":not failures,"tests":tests,"offline_cases":offline["passed"],"live_cases":live["passed"],
            "live_model":live["model"],"live_model_responses":total_responses,"distinct_live_paths":live["distinct_action_sequences"],
            "live_http_attempts":live.get("http_attempts",total_responses),
            "credential_scan":{"inspected_files":inspected,"leaks":len(leaking)},"failures":failures,
            "github_uploaded":False,"pending_submission_items":["等待用户上传指令","GitHub仓库URL","最终commit SHA","如选择私有仓库则配置评审只读权限"],
            "personal_review":"候选人个人手工修改与审阅尚未由本人补记，AI使用范围已如实说明。"}
    write_json(ROOT/"examples/submission_audit.json",report)
    lines=["# 本地交付与提交清单","",f"本地核对：**{'通过' if report['local_ready'] else '未通过'}**。本文件由scripts/audit_submission.py核对实际产物后生成，不执行上传。",
           "", "|要求|状态|证据|","|---|---|---|",
           "|题号及运行入口|已提供|[README](../README.md)|",
           "|src、tests、examples、data及docs|已提供|目录与规定文件逐项核对|",
           "|需求、方案、评估、AI记录及复盘|已提供|docs/01–05|",
           "|依赖及环境变量示例|已提供|requirements.txt、pyproject.toml、.env.example|",
           f"|可执行测试|{tests['tests']}项通过|[JUnit XML](../examples/test-results.xml)|",
           f"|离线输入/输出/Trace|{offline['passed']}/{offline['total']}通过|[离线汇总](../examples/summary.json)|",
           f"|真实模型输入/输出/Trace|{live['passed']}/{live['total']}通过|[真实汇总](../examples/live/summary.json)|",
           f"|至少两条真实动态路径|{live['distinct_action_sequences']}条不同动作序列|[逐步审阅](../examples/live/{live['run_folder']}/trace_review.md)|",
           "|工具失败及调用上限|已验证，保留未完成状态|真实案例07–11及边界测试|",
           "|文档原文引用及冲突|逐条核对本轮已读原文|真实案例01、02、05、12、13|",
           "|密钥及内部思维内容|未纳入提交材料|密钥文件留在项目外；Trace只记录安全元信息|",
           "|AI辅助范围与个人贡献|已如实说明，个人自审待本人补记|[AI记录](04-ai-usage.md)|",
           "|GitHub URL及最终commit SHA|等待用户上传命令|本轮没有创建远程仓库或推送|",
           "", "本地验收通过不等于已经完成平台提交。仓库地址、最终提交SHA以及必要的评审权限在后续上传时补齐。",
           "", "核对结果见 [submission_audit.json](../examples/submission_audit.json)。"]
    if failures:
        lines += ["","未通过项：",""]+["- "+f for f in failures]
    (ROOT/"docs/06-submission-checklist.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("local_ready","tests","offline_cases","live_cases","live_model_responses","credential_scan","github_uploaded","failures")},ensure_ascii=False,indent=2))
    return 0 if report["local_ready"] else 1


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--api-key-file",type=Path,required=True)
    raise SystemExit(audit(parser.parse_args().api_key_file))
