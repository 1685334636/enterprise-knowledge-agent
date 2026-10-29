import json
import time
from dataclasses import dataclass,field
from pathlib import Path
from uuid import uuid4

from pydantic import ValidationError

from .backends import BackendError
from .models import Decision,Request,TaskResult
from .policy import compose_answer,inspect_finish


@dataclass
class DecisionContext:
    request: Request
    observations: list = field(default_factory=list)
    read_passages: dict = field(default_factory=dict)
    search_hits: dict = field(default_factory=dict)
    steps_remaining: int = 0
    tool_calls_remaining: int = 0

    def payload(self):
        return {"request":self.request.model_dump(),"observations":self.observations,
                "steps_remaining":self.steps_remaining,"tool_calls_remaining":self.tool_calls_remaining}


@dataclass
class RunBundle:
    result: TaskResult
    events: list


class Trace:
    def __init__(self,run_id,path=None):
        self.events = []
        self.run_id = run_id
        self.stream = None
        if path:
            path = Path(path)
            path.parent.mkdir(parents=True,exist_ok=True)
            self.stream = path.open("w",encoding="utf-8")

    def emit(self,event,step,**values):
        record = {"seq":len(self.events)+1,"run_id":self.run_id,"event":event,"step":step,**values}
        self.events.append(record)
        if self.stream:
            self.stream.write(json.dumps(record,ensure_ascii=False)+"\n")
            self.stream.flush()

    def close(self):
        if self.stream:
            self.stream.close()


class Agent:
    def __init__(self,backend,tools,max_steps=8,max_tool_calls=6):
        if not 1<=max_steps<=30 or not 1<=max_tool_calls<=20:
            raise ValueError("max_steps必须为1至30，max_tool_calls必须为1至20")
        self.backend,self.tools = backend,tools
        self.max_steps,self.max_tool_calls = max_steps,max_tool_calls

    def run(self,request:Request,trace_path=None):
        started = time.perf_counter()
        run_id = uuid4().hex[:12]
        trace = Trace(run_id,trace_path)
        context = DecisionContext(request=request)
        calls,step = 0,0
        trace.emit("run_start",0,question=request.question,history=[m.model_dump() for m in request.history],
                   model_mode=self.backend.mode,max_steps=self.max_steps,max_tool_calls=self.max_tool_calls)

        def finish(status,citations=None,clarification=None,gaps=None):
            citations = citations or []
            if status=="conflict" and not clarification:
                clarification = "请确认适用制度、部门与优先关系；不能仅按版本日期选择。"
            result = TaskResult(run_id=run_id,status=status,question=request.question,
                                answer=compose_answer(status,citations,clarification),citations=citations,
                                gaps=gaps or [],clarification=clarification,decision_steps=step,
                                tool_calls=calls,model_mode=self.backend.mode,complete=status=="answered",
                                elapsed_ms=round((time.perf_counter()-started)*1000,3),
                                boundary=("离线规则Mock，仅验证流程和工程约束，不证明真实模型决策效果。"
                                          if self.backend.mode=="offline_mock" else
                                          "接口模式为live；引用校验通过不等于开放域语义正确性已获证明。"
                                          if self.backend.mode=="live" else "测试替身运行，不是实际语言模型效果证据。"))
            trace.emit("run_end",step,result=result.model_dump())
            return RunBundle(result,trace.events)

        try:
            for step in range(1,self.max_steps+1):
                context.steps_remaining = self.max_steps-step+1
                context.tool_calls_remaining = self.max_tool_calls-calls
                try:
                    decision = self.backend.decide(context)
                    if not isinstance(decision,Decision):
                        decision = Decision.model_validate(decision)
                except Exception:
                    if getattr(self.backend,"last_call",None):
                        trace.emit("model_response",step,metadata=self.backend.last_call)
                    trace.emit("model_error",step,message="模型连接或动作结构不合法；未切换到其他模式。")
                    return finish("model_error",gaps=["未获得有效模型动作，请检查接口配置和JSON格式。"])
                if getattr(self.backend,"last_call",None):
                    trace.emit("model_response",step,metadata=self.backend.last_call)
                trace.emit("decision",step,decision=decision.model_dump(exclude_none=True))
                if decision.action=="finish":
                    citations,problem = inspect_finish(decision,context)
                    if problem:
                        context.observations.append({"kind":"policy","observation":problem})
                        trace.emit("policy_observation",step,observation=problem)
                        continue
                    return finish(decision.status,citations,decision.clarification,decision.gaps)
                if calls>=self.max_tool_calls:
                    return finish("limit_reached",gaps=["工具调用次数已达上限，尚未完成证据核验。"])
                arguments = ({"query":decision.query,"top_k":decision.top_k} if decision.action=="search_documents"
                             else {"passage_id":decision.passage_id})
                try:
                    observation = self.tools.execute(decision.action,arguments)
                except Exception:
                    observation = {"ok":False,"error":{"code":"INTERNAL_TOOL_ERROR","message":"工具内部异常，未记录为成功。"},"result":None}
                calls += 1
                context.observations.append({"kind":"tool","action":decision.action,"arguments":arguments,
                                             "observation":observation})
                trace.emit("tool_observation",step,tool=decision.action,arguments=arguments,observation=observation)
                if observation["ok"]:
                    if decision.action=="search_documents":
                        for hit in observation["result"]["hits"]:
                            context.search_hits[hit["passage_id"]] = hit
                    else:
                        p = observation["result"]
                        context.read_passages[p["passage_id"]] = p
            return finish("limit_reached",gaps=["决策步数已达上限，尚未得到通过证据校验的最终答案。"])
        finally:
            trace.close()
