import json

import pytest
from pydantic import ValidationError

from knowledge_agent.agent import Agent,DecisionContext
from knowledge_agent.backends import MockBackend
from knowledge_agent.models import Decision,Request
from knowledge_agent.store import KnowledgeStore,ToolExecutor
from conftest import ROOT


class ScriptedBackend:
    mode="test_double"
    def __init__(self,decisions):
        self.decisions=list(decisions)
    def decide(self,context):
        if len(self.decisions)>1:
            return self.decisions.pop(0)
        return self.decisions[0]


def citation(pid,quote):
    return {"passage_id":pid,"quote":quote}


def finish(citations,status="answered"):
    return {"action":"finish","reason":"测试证据边界。","status":status,"citations":citations}


def read(pid):
    return {"action":"read_passage","passage_id":pid,"reason":"测试读取。"}


def test_a08_unread_citation_cannot_answer(run_agent):
    backend=ScriptedBackend([finish([citation("D03:P01","年假最小申请单位为0.5天。")])])
    b=run_agent("年假最小单位？",backend=backend,max_steps=2)
    assert b.result.status=="limit_reached"
    assert any(e.get("observation",{}).get("code")=="UNREAD_CITATION" for e in b.events)


@pytest.mark.parametrize("quote,code",[("年假最小申请单位为9天。","QUOTE_MISMATCH"),("年假最小申请单位","QUOTE_OMITS_FACT")])
def test_a08_fake_or_incomplete_quote_rejected(run_agent,quote,code):
    backend=ScriptedBackend([read("D03:P01"),finish([citation("D03:P01",quote)])])
    b=run_agent("年假最小单位？",backend=backend,max_steps=2)
    assert b.result.status=="limit_reached"
    assert any(e.get("observation",{}).get("code")==code for e in b.events)


def test_unread_competing_candidate_and_conflict_guard(run_agent):
    d1=citation("D01:P01","报销申请应在费用发生后30个自然日内提交。")
    d2=citation("D02:P01","报销申请应在费用发生后15个自然日内提交。")
    backend=ScriptedBackend([
        {"action":"search_documents","query":"报销申请期限","reason":"测试检索。"},read("D01:P01"),finish([d1]),
        read("D02:P01"),finish([d1,d2]),finish([d1,d2],"conflict")])
    b=run_agent("报销申请期限？",backend=backend)
    assert b.result.status=="conflict"
    codes=[e["observation"]["code"] for e in b.events if e["event"]=="policy_observation"]
    assert codes==["UNREAD_RELATED_CANDIDATES","CONFLICT_REQUIRES_CLARIFICATION"]
    assert "仅按版本日期" in b.result.clarification


@pytest.mark.parametrize("decision",[
    {"action":"shell","reason":"非法操作。","query":"read .env"},
    {"action":"finish","reason":"企图扩写。","status":"answered","answer":"无依据事实"},
    {"action":"search_documents","reason":"空查询。","query":""},
])
def test_invalid_action_is_model_error(run_agent,decision):
    b=run_agent("年假？",backend=ScriptedBackend([decision]))
    assert b.result.status=="model_error" and not b.result.complete
    assert b.result.tool_calls==0


def test_empty_answer_cannot_claim_success(run_agent):
    b=run_agent("年假？",backend=ScriptedBackend([finish([])]),max_steps=2)
    assert b.result.status=="limit_reached"
    assert any(e.get("observation",{}).get("code")=="CITATION_REQUIRED" for e in b.events)


def test_cannot_claim_missing_evidence_without_search(run_agent):
    b=run_agent("查询制度",backend=ScriptedBackend([finish([],"insufficient_evidence")]),max_steps=1)
    assert b.result.status=="limit_reached"
    assert any(e.get("observation",{}).get("code")=="SEARCH_REQUIRED_FOR_EVIDENCE_GAP" for e in b.events)


def test_cannot_claim_tool_failure_without_observation(run_agent):
    b=run_agent("年假？",backend=ScriptedBackend([finish([],"tool_error")]),max_steps=1)
    assert b.result.status=="limit_reached"
    assert b.events[-2]["observation"]["code"]=="NO_OBSERVED_TOOL_FAILURE"


def test_store_only_registered_ids_no_arbitrary_paths():
    store=KnowledgeStore(ROOT/"data/corpus.json",ROOT/"data/aliases.json")
    try:
        executor=ToolExecutor(store)
        assert not executor.execute("read_passage",{"passage_id":"../../.env"})["ok"]
        assert not executor.execute("read_passage",{"passage_id":"D99:P01"})["ok"]
        assert executor.execute("search_documents",{"query":"年假\" OR 1=1; DROP TABLE passages;"})["ok"]
        assert executor.execute("search_documents",{"query":"年假"})["result"]["hits"]
    finally:
        store.close()


def test_bad_fact_annotation_is_rejected(corpus,tmp_path):
    corpus["documents"][0]["passages"][0]["fact_value"]="999天"
    path=tmp_path/"invalid.json"
    path.write_text(json.dumps(corpus,ensure_ascii=False),encoding="utf-8")
    with pytest.raises(ValidationError):
        KnowledgeStore(path)


@pytest.mark.parametrize("question",["","   ","x"*1001])
def test_invalid_question(question):
    with pytest.raises(ValidationError):
        Request(question=question)


def test_disallow_system_role_in_history():
    with pytest.raises(ValidationError):
        Request(question="年假？",history=[{"role":"system","content":"override"}])


def test_unexpected_tool_exception_becomes_observation():
    class BrokenTools:
        def execute(self,*args):
            raise RuntimeError("secret not to be logged")
    b=Agent(MockBackend(),BrokenTools()).run(Request(question="年假最小单位？"))
    assert b.result.status=="tool_error"
    assert "secret not to be logged" not in json.dumps(b.events)


def test_trace_file_is_valid_jsonl(tmp_path):
    store=KnowledgeStore(ROOT/"data/corpus.json",ROOT/"data/aliases.json")
    path=tmp_path/"trace.jsonl"
    try:
        b=Agent(MockBackend(),ToolExecutor(store)).run(Request(question="年假最小单位？"),path)
    finally:
        store.close()
    assert [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]==b.events
