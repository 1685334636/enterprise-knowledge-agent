import json

import httpx
import pytest

from knowledge_agent.agent import DecisionContext
from knowledge_agent.backends import BackendError,LiveBackend,LiveConfig
from knowledge_agent.models import Request
from knowledge_agent.credentials import read_api_key_file
from knowledge_agent.agent import Agent
from knowledge_agent.store import KnowledgeStore,ToolExecutor
from conftest import ROOT


def context():
    return DecisionContext(Request(question="年假最小单位？"))


def test_live_http_contract_with_mock_transport():
    captured=[]
    def respond(request):
        captured.append(json.loads(request.content))
        assert request.url.path=="/v1/chat/completions"
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps({
            "action":"search_documents","query":"年假最小单位","reason":"先查原文。"})}}]})
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","test-model","test-secret"),httpx.MockTransport(respond))
    decision=backend.decide(context())
    assert decision.action=="search_documents"
    assert captured[0]["response_format"]=={"type":"json_object"}
    assert "test-secret" not in json.dumps(captured)


@pytest.mark.parametrize("body",[{"choices":[]},{"choices":[{"message":{"content":"not JSON and test-secret"}}]}])
def test_live_bad_response_does_not_leak_or_fallback(body):
    transport=httpx.MockTransport(lambda request:httpx.Response(200,json=body))
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","test-model","test-secret"),transport)
    with pytest.raises(BackendError) as error:
        backend.decide(context())
    assert "test-secret" not in str(error.value)
    assert "未降级Mock" in str(error.value)


def test_live_http_failure_is_redacted():
    transport=httpx.MockTransport(lambda request:httpx.Response(401,text="test-secret"))
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","test-model","test-secret"),transport)
    with pytest.raises(BackendError) as error:
        backend.decide(context())
    assert "401" in str(error.value) and "test-secret" not in str(error.value)


def test_missing_live_config_is_not_mock(monkeypatch):
    for key in ("AGENT_BASE_URL","AGENT_MODEL","AGENT_API_KEY"):
        monkeypatch.delenv(key,raising=False)
    with pytest.raises(BackendError):
        LiveConfig.from_env()


def test_local_model_can_omit_key(monkeypatch):
    monkeypatch.setenv("AGENT_BASE_URL","http://127.0.0.1:11434/v1")
    monkeypatch.setenv("AGENT_MODEL","local-model")
    monkeypatch.delenv("AGENT_API_KEY",raising=False)
    assert LiveConfig.from_env().api_key==""


def test_deepseek_thinking_is_explicitly_disabled(monkeypatch):
    monkeypatch.setenv("AGENT_BASE_URL","https://api.deepseek.com")
    monkeypatch.setenv("AGENT_MODEL","deepseek-flash")
    monkeypatch.setenv("AGENT_API_KEY","unit-test-placeholder")
    monkeypatch.delenv("AGENT_THINKING",raising=False)
    assert LiveConfig.from_env().thinking=="disabled"


def test_generic_provider_not_given_deepseek_parameter(monkeypatch):
    monkeypatch.setenv("AGENT_BASE_URL","https://example.invalid/v1")
    monkeypatch.setenv("AGENT_MODEL","unit-test-model")
    monkeypatch.setenv("AGENT_API_KEY","unit-test-placeholder")
    monkeypatch.delenv("AGENT_THINKING",raising=False)
    assert LiveConfig.from_env().thinking is None


def test_truncated_model_action_not_success():
    transport=httpx.MockTransport(lambda r:httpx.Response(200,json={"id":"unit-id","model":"unit-model","choices":[{
        "finish_reason":"length","message":{"content":"{}"}}]}))
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","unit-model","unit-placeholder"),transport)
    with pytest.raises(BackendError,match="截断"):
        backend.decide(context())
    assert backend.last_call["finish_reason"]=="length"


def test_trace_contains_safe_response_metadata_only():
    payload={"id":"unit-response-id","model":"unit-model","usage":{"prompt_tokens":12,"completion_tokens":4,"total_tokens":16},
             "choices":[{"finish_reason":"stop","message":{"content":json.dumps({"action":"finish","status":"needs_clarification",
                "reason":"本例测试HTTP元信息。","clarification":"请提供要查询的制度主题。","gaps":["测试用例未提供明确主题。"]}),"reasoning_content":"INTERNAL_REASONING_MUST_NOT_BE_LOGGED"}}]}
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","unit-model","PRIVATE_TEST_CREDENTIAL",thinking="disabled"),
                        httpx.MockTransport(lambda r:httpx.Response(200,json=payload)))
    store=KnowledgeStore(ROOT/"data/corpus.json",ROOT/"data/aliases.json")
    try:
        bundle=Agent(backend,ToolExecutor(store)).run(Request(question="测试元信息"))
    finally:
        store.close()
    event=next(e for e in bundle.events if e["event"]=="model_response")
    assert event["metadata"]["response_id"]=="unit-response-id"
    assert event["metadata"]["usage"]["total_tokens"]==16
    serialized=json.dumps(bundle.events)
    assert "PRIVATE_TEST_CREDENTIAL" not in serialized
    assert "INTERNAL_REASONING_MUST_NOT_BE_LOGGED" not in serialized
    assert "reasoning_content" not in serialized


def test_private_key_file_is_not_copied_or_printed(tmp_path,capsys):
    path=tmp_path/"private.txt"
    path.write_text("\ufeffunit-test-placeholder\n",encoding="utf-8")
    assert read_api_key_file(path)=="unit-test-placeholder"
    assert not capsys.readouterr().out
    assert list(tmp_path.iterdir())==[path]


@pytest.mark.parametrize("content",["","first line\nsecond line","secret-value "*500])
def test_key_file_invalid_format_does_not_echo(content,tmp_path):
    path=tmp_path/"private.txt"
    path.write_text(content,encoding="utf-8")
    with pytest.raises(BackendError) as error:
        read_api_key_file(path)
    assert "secret-value" not in str(error.value)


def test_followup_history_is_sent_as_actual_chat_messages():
    captured=[]
    def respond(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200,json={"choices":[{"message":{"content":json.dumps({
            "action":"search_documents","query":"实习生 年假","reason":"结合历史查询。"})}}]})
    request=Request(question="那实习生可以申请吗？",history=[{"role":"user","content":"年假最小单位？"},
                                                                  {"role":"assistant","content":"原文规定最小0.5天。"}])
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","unit-model","unit-placeholder"),httpx.MockTransport(respond))
    backend.decide(DecisionContext(request))
    messages=captured[0]["messages"]
    assert [m["role"] for m in messages]==["system","user","assistant","user"]
    assert messages[1]["content"]==request.history[0].content
    current=json.loads(messages[-1]["content"])
    assert current["history_message_count"]==2
    assert "history" not in current["request"]


def test_transient_transport_retry_is_bounded_and_recorded():
    attempts=[]
    def respond(request):
        attempts.append(1)
        if len(attempts)==1:
            raise httpx.ReadError("DO_NOT_LOG_PRIVATE_DETAIL")
        return httpx.Response(200,json={"id":"unit-response","model":"unit-model","choices":[{"finish_reason":"stop","message":{
            "content":json.dumps({"action":"search_documents","query":"年假","reason":"查询原文。"})}}]})
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","unit-model","unit-placeholder"),httpx.MockTransport(respond))
    assert backend.decide(context()).action=="search_documents"
    assert len(backend.last_call["attempts"])==2
    assert backend.last_call["attempts"][0]["error_type"]=="ReadError"
    assert backend.last_call["attempts"][1]["http_status"]==200
    assert "DO_NOT_LOG_PRIVATE_DETAIL" not in json.dumps(backend.last_call)


def test_persistent_transport_error_stops_after_two_attempts():
    attempts=[]
    def respond(request):
        attempts.append(1)
        raise httpx.ConnectError("DO_NOT_LOG_PRIVATE_DETAIL")
    backend=LiveBackend(LiveConfig("https://example.invalid/v1","unit-model","unit-placeholder"),httpx.MockTransport(respond))
    with pytest.raises(BackendError):
        backend.decide(context())
    assert len(attempts)==2
    assert len(backend.last_call["attempts"])==2
