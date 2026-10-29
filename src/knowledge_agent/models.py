from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Passage(StrictModel):
    passage_id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]*:P[0-9]+$")
    text: str = Field(min_length=1, max_length=4000)
    fact_key: str = Field(min_length=1, max_length=100)
    fact_value: str = Field(min_length=1, max_length=300)

    @model_validator(mode="after")
    def value_in_source(self):
        if "".join(self.fact_value.split()) not in "".join(self.text.split()):
            raise ValueError("事实标注值必须直接出现在原文中")
        return self


class Document(StrictModel):
    doc_id: str = Field(pattern=r"^[A-Z][A-Z0-9_-]*$")
    title: str = Field(min_length=1, max_length=200)
    version_date: date
    scope: str = Field(min_length=1, max_length=200)
    passages: list[Passage] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def id_consistency(self):
        if any(not p.passage_id.startswith(self.doc_id+":") for p in self.passages):
            raise ValueError("片段ID与文档ID不一致")
        return self


class Corpus(StrictModel):
    synthetic: bool
    description: str
    documents: list[Document] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def unique_ids(self):
        docs = [d.doc_id for d in self.documents]
        passages = [p.passage_id for d in self.documents for p in d.passages]
        if len(set(docs))!=len(docs) or len(set(passages))!=len(passages):
            raise ValueError("文档与片段ID必须唯一")
        return self


class HistoryMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=2000)


class Request(StrictModel):
    question: str = Field(min_length=1, max_length=1000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=12)

    @model_validator(mode="after")
    def nonblank(self):
        self.question = self.question.strip()
        if not self.question:
            raise ValueError("问题不能为空白")
        return self


FinishStatus = Literal["answered", "conflict", "needs_clarification", "insufficient_evidence", "tool_error"]
TaskStatus = Literal["answered", "conflict", "needs_clarification", "insufficient_evidence", "tool_error", "model_error", "limit_reached"]


class CitationChoice(StrictModel):
    passage_id: str = Field(min_length=1, max_length=80)
    quote: str = Field(min_length=1, max_length=4000)


class Decision(StrictModel):
    action: Literal["search_documents", "read_passage", "finish"]
    reason: str = Field(min_length=1, max_length=240)
    query: str | None = Field(default=None, max_length=500)
    top_k: int = Field(default=5, ge=1, le=8)
    passage_id: str | None = Field(default=None, max_length=80)
    status: FinishStatus | None = None
    citations: list[CitationChoice] = Field(default_factory=list, max_length=8)
    clarification: str | None = Field(default=None, max_length=400)
    gaps: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def valid_action(self):
        if self.action=="search_documents" and not (self.query and self.query.strip()):
            raise ValueError("检索动作必须提供query")
        if self.action=="read_passage" and not self.passage_id:
            raise ValueError("读取动作必须提供passage_id")
        if self.action=="finish" and self.status is None:
            raise ValueError("结束动作必须提供status")
        if any(len(g)>400 for g in self.gaps):
            raise ValueError("资料缺口说明过长")
        return self


class Citation(StrictModel):
    doc_id: str
    passage_id: str
    title: str
    version_date: str
    scope: str
    quote: str


class TaskResult(StrictModel):
    run_id: str
    status: TaskStatus
    question: str
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    clarification: str | None = None
    decision_steps: int
    tool_calls: int
    model_mode: str
    complete: bool
    elapsed_ms: float
    boundary: str
