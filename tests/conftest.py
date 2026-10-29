import json
from pathlib import Path

import pytest

from knowledge_agent.agent import Agent
from knowledge_agent.backends import MockBackend
from knowledge_agent.models import Request
from knowledge_agent.store import KnowledgeStore,ToolExecutor


ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def corpus():
    return json.loads((ROOT/"data/corpus.json").read_text(encoding="utf-8"))


@pytest.fixture
def run_agent(tmp_path,corpus):
    stores=[]
    def run(question,history=None,data=None,fail_once=None,always_fail=None,max_steps=8,max_tool_calls=6,backend=None):
        path=tmp_path/f"corpus_{len(stores)}.json"
        path.write_text(json.dumps(data or corpus,ensure_ascii=False),encoding="utf-8")
        store=KnowledgeStore(path,ROOT/"data/aliases.json")
        stores.append(store)
        return Agent(backend or MockBackend(),ToolExecutor(store,fail_once,always_fail),max_steps,max_tool_calls).run(
            Request(question=question,history=history or []),tmp_path/f"trace_{len(stores)}.jsonl")
    yield run
    for store in stores:
        store.close()
