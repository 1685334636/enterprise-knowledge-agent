"""运行时证据约束；不把原文资料当作可执行指令。"""
from itertools import combinations

from .models import Citation


def conflicting_passages(passages):
    conflicts = []
    for a,b in combinations(passages,2):
        ambiguous_scope = a["scope"]==b["scope"] or "未说明" in (a["scope"],b["scope"])
        if a["fact_key"]==b["fact_key"] and a["fact_value"]!=b["fact_value"] and ambiguous_scope:
            conflicts.append((a,b))
    return conflicts


def inspect_finish(decision, context):
    """返回 (有效引用, 可供下一步适配器观察的拒绝信息)。"""
    read = context.read_passages
    if decision.status=="insufficient_evidence" and not any(
        o["kind"]=="tool" and o["action"]=="search_documents" and o["observation"]["ok"] for o in context.observations
    ):
        return [],{"code":"SEARCH_REQUIRED_FOR_EVIDENCE_GAP","message":"尚未成功检索本地资料，不能凭空声称知识库没有依据；请先检索，或在工具故障时明确失败。","passage_ids":[]}
    citations = []
    seen = set()
    for proposed in decision.citations:
        p = read.get(proposed.passage_id)
        if p is None:
            return [],{"code":"UNREAD_CITATION","message":"引用片段尚未由读取工具返回，请先读取原文。",
                       "passage_ids":[proposed.passage_id]}
        if proposed.quote not in p["text"]:
            return [],{"code":"QUOTE_MISMATCH","message":"引文不是已读原文的连续片段，禁止改写数字或伪造引文。",
                       "passage_ids":[proposed.passage_id]}
        if "".join(p["fact_value"].split()) not in "".join(proposed.quote.split()):
            return [],{"code":"QUOTE_OMITS_FACT","message":"引文没有包含该片段标注的完整事实值，请保留数字与单位。",
                       "passage_ids":[proposed.passage_id]}
        if proposed.passage_id not in seen:
            citations.append(Citation(**{k:p[k] for k in ("doc_id","passage_id","title","version_date","scope")},quote=proposed.quote))
            seen.add(proposed.passage_id)
    if decision.status in {"answered","conflict"} and not citations:
        return [],{"code":"CITATION_REQUIRED","message":"回答或冲突状态必须引用已读取的原文片段。","passage_ids":[]}
    selected_keys = {read[c.passage_id]["fact_key"] for c in citations}
    pending = [p["passage_id"] for p in context.search_hits.values()
               if p["fact_key"] in selected_keys and p["passage_id"] not in read]
    if pending:
        return [],{"code":"UNREAD_RELATED_CANDIDATES","message":"已检索到同主题未读候选，请补读后再决定是否存在冲突。",
                   "passage_ids":pending}
    relevant = [p for p in read.values() if p["fact_key"] in selected_keys]
    conflicts = conflicting_passages(relevant)
    if conflicts:
        required = {p["passage_id"] for pair in conflicts for p in pair}
        if decision.status!="conflict" or not required.issubset(seen):
            return [],{"code":"CONFLICT_REQUIRES_CLARIFICATION",
                       "message":"已读资料存在适用范围未决的冲突；必须同时引用双方并询问适用制度，不得仅选新版。",
                       "passage_ids":sorted(required)}
    elif decision.status=="conflict":
        return [],{"code":"NO_OBSERVED_CONFLICT","message":"尚无已读同主题冲突依据，不能声称已证实冲突。","passage_ids":[]}
    if decision.status=="tool_error" and not any(not o["observation"]["ok"] for o in context.observations if o["kind"]=="tool"):
        return [],{"code":"NO_OBSERVED_TOOL_FAILURE","message":"没有工具失败观察，不能声称工具故障。","passage_ids":[]}
    if decision.status=="needs_clarification" and not decision.clarification:
        return [],{"code":"CLARIFICATION_REQUIRED","message":"需要给出具体澄清问题。","passage_ids":[]}
    return citations,None


def compose_answer(status,citations,clarification=None):
    if status=="answered":
        heading = "根据本次已读取的资料："
    elif status=="conflict":
        heading = "已读取的制度存在冲突，当前不能确定统一答案："
    elif status=="needs_clarification":
        return "需要补充信息后才能继续。"+("\n"+clarification if clarification else "")
    elif status=="insufficient_evidence":
        return "现有资料不足以回答该问题，未生成无依据的事实答案。"
    elif status=="tool_error":
        return "工具执行失败，当前任务未完成。"
    elif status=="model_error":
        return "模型接口或动作输出异常，当前任务未完成。"
    else:
        return "已达到决策步数或工具调用上限，当前任务未完成。"
    lines = [heading]
    for c in citations:
        lines.append(f"- {c.quote} [{c.passage_id}；版本{c.version_date}；适用范围：{c.scope}]")
    if clarification:
        lines.append(clarification)
    return "\n".join(lines)
