import json
import os
import subprocess
import sys

import pytest


@pytest.mark.parametrize("question,extra,status,exit_code",[
    ("正式员工年假最小可以请多久？",[],"answered",0),
    ("报销申请期限？",[],"conflict",0),
    ("年假最小单位？",["--always-fail","search_documents"],"tool_error",2),
])
def test_cli_from_another_directory(tmp_path,question,extra,status,exit_code):
    output=tmp_path/"result.json"
    trace=tmp_path/"trace.jsonl"
    process=subprocess.run([sys.executable,"-m","knowledge_agent",question,"--output",str(output),
                            "--trace",str(trace),*extra],cwd=tmp_path,capture_output=True,text=True,encoding="utf-8")
    assert process.returncode==exit_code,process.stderr
    result=json.loads(process.stdout)
    assert result["status"]==status
    assert json.loads(output.read_text(encoding="utf-8"))==result
    assert json.loads(trace.read_text(encoding="utf-8").splitlines()[-1])["result"]==result


def test_cli_live_missing_config_does_not_execute_mock(tmp_path):
    environment={k:v for k,v in os.environ.items() if not k.startswith("AGENT_")}
    process=subprocess.run([sys.executable,"-m","knowledge_agent","年假最小单位？","--mode","live",
                            "--env-file",str(tmp_path/"missing.env")],cwd=tmp_path,env=environment,
                           capture_output=True,text=True,encoding="utf-8")
    assert process.returncode==2
    assert not process.stdout.strip()
    assert json.loads(process.stderr)["status"]=="configuration_error"
