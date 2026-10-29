import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import ValidationError

from .agent import Agent
from .backends import BackendError,LiveBackend,LiveConfig,MockBackend
from .credentials import read_api_key_file
from .models import Request
from .store import KnowledgeStore,ToolExecutor


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def write_json(path,value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary = path.with_name(path.name+".tmp")
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    temporary.replace(path)


def parser():
    p = argparse.ArgumentParser(description="企业知识问答 Agent：附原文引用、有界循环、明确失败状态")
    p.add_argument("question",help="非空问题")
    p.add_argument("--mode",choices=["mock","live"],default="mock")
    p.add_argument("--corpus",type=Path,default=PROJECT_ROOT/"data/corpus.json")
    p.add_argument("--aliases",type=Path,default=PROJECT_ROOT/"data/aliases.json")
    p.add_argument("--history-file",type=Path,help="用户/助手消息数组JSON")
    p.add_argument("--trace",type=Path,help="JSONL事件文件；不含密钥或思维链")
    p.add_argument("--output",type=Path,help="最终JSON文件；同时仍输出到标准输出")
    p.add_argument("--max-steps",type=int,default=8)
    p.add_argument("--max-tool-calls",type=int,default=6)
    p.add_argument("--env-file",type=Path,default=PROJECT_ROOT/".env")
    p.add_argument("--api-key-file",type=Path,help="从项目外的单行文本文件读取密钥，仅在当前进程内使用")
    p.add_argument("--fail-once",choices=["search_documents","read_passage"],help="显式故障注入，仅用于验证")
    p.add_argument("--always-fail",choices=["search_documents","read_passage"],help="持续故障注入，仅用于验证")
    return p


def main(argv=None):
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,"reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args(argv)
    store = None
    try:
        history = json.loads(args.history_file.read_text(encoding="utf-8")) if args.history_file else []
        request = Request(question=args.question,history=history)
        if args.mode=="live":
            load_dotenv(args.env_file,override=False)
            if args.api_key_file:
                os.environ["AGENT_API_KEY"]=read_api_key_file(args.api_key_file)
            backend = LiveBackend(LiveConfig.from_env())
        else:
            backend = MockBackend()
        store = KnowledgeStore(args.corpus,args.aliases)
        tools = ToolExecutor(store,fail_once=args.fail_once,always_fail=args.always_fail)
        bundle = Agent(backend,tools,args.max_steps,args.max_tool_calls).run(request,args.trace)
        value = bundle.result.model_dump()
        if args.output:
            write_json(args.output,value)
        print(json.dumps(value,ensure_ascii=False,indent=2))
        return 2 if value["status"] in {"model_error","tool_error","limit_reached"} else 0
    except (BackendError,ValueError,ValidationError,OSError):
        # 不回显异常消息、原始模型正文、路径或请求头，避免把配置中的密钥带到日志。
        print(json.dumps({"status":"configuration_error","complete":False,
                          "message":"输入、资料或模型配置无效；请核对命令、JSON文件及.env.example。", "requested_mode":args.mode},ensure_ascii=False),file=sys.stderr)
        return 2
    finally:
        if store is not None:
            store.close()


if __name__=="__main__":
    raise SystemExit(main())
