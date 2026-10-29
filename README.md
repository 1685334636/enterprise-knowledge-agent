# 企业知识问答 Agent

选择题号：**第3题**。帮助员工查询制度与产品资料，输出可核验原文；资料冲突时并列引用并澄清，缺资料或工具失败时明确返回未完成。

本轮交付为 **本地CLI + 可替换合成语料 + 有界动作循环 + 测试 + 实际运行Trace**。已在hj13环境接入 **DeepSeek / deepseek-flash**；Mock和真实模型的验收结果分别记录，真实运行包含原始失败与修复后的复测。已通过60项自动测试、13组Mock案例和13组真实模型案例。

公开交付仓库：[1685334636/enterprise-knowledge-agent](https://github.com/1685334636/enterprise-knowledge-agent)。题号、审阅入口与提交SHA查询方法见[公开提交说明](docs/07-github-submission.md)。

## 先看这些文件

|审阅目标|入口|
|---|---|
|文档规范、题目选择和任务规划|[docs/00-plan.md](docs/00-plan.md)|
|用户、范围、需求与A01–A11验收矩阵|[docs/01-requirements.md](docs/01-requirements.md)|
|流程、动态动作、技术选择和证据边界|[docs/02-solution.md](docs/02-solution.md)|
|实际测试、场景结果、失败及限制|[docs/03-evaluation.md](docs/03-evaluation.md)|
|AI辅助范围及个人工作待补记部分|[docs/04-ai-usage.md](docs/04-ai-usage.md)|
|难点、实际修复和下一步|[docs/05-retrospective.md](docs/05-retrospective.md)|
|逐步运行对照与JSONL原始记录|[examples/trace_review.md](examples/trace_review.md)|
|机器可读结果、版本、计时范围和源码指纹|[examples/summary.json](examples/summary.json)|
|真实模型请求、用量、动态路径及结果|[examples/live/summary.json](examples/live/summary.json)|
|提交规范逐项核对快照|[docs/06-submission-checklist.md](docs/06-submission-checklist.md)|
|公开仓库与提交说明|[docs/07-github-submission.md](docs/07-github-submission.md)|

以上规范、需求和方案在实现代码之前创建。数据完全合成；项目不包含原始试题截图、企业资料、真实密钥或发布操作。

## 环境和安装

实际使用 `hj13`，Python 3.13.7；兼容Python 3.10及以上。Windows PowerShell：

```powershell
conda activate hj13
Set-Location -LiteralPath 'E:\研究生\短波预测matlab\qzjl\证件\radio\agent_test'
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps --no-build-isolation
```

当前hj13已有所有运行依赖，已安装本项目的可编辑包。也可直接使用解释器：

```powershell
& 'D:\anaconda\envs\hj13\python.exe' -m knowledge_agent '正式员工年假最小可以请多久？' --mode mock
```

本地一键检查并重建样例：

```powershell
powershell -ExecutionPolicy Bypass -File .\run_local.ps1
```

逐步执行：

```powershell
python -m pytest -q --junitxml=examples/test-results.xml
python scripts/run_examples.py
```

安装依赖后，Mock运行、检索、读取和评估无需网络。脚本会重建 `examples/inputs`、`outputs`、`traces`、`fixtures` 以及评估文档，不覆盖 `data/corpus.json`。

## 运行案例

普通查询并落盘结果、Trace：

```powershell
python -m knowledge_agent '正式员工年假最小可以请多久？' --mode mock --output examples/manual/result.json --trace examples/manual/trace.jsonl
```

报销期限冲突：

```powershell
python -m knowledge_agent '报销申请的提交期限是多久？' --mode mock
```

输出状态为 `conflict`，列出D01的“30个自然日”和D02的“15个自然日”，并询问适用制度；不按较新日期直接选择15天。

上下文追问，历史文件由实际正常案例结果生成：

```powershell
python -m knowledge_agent '那实习生可以申请吗？' --history-file examples/inputs/context_history.json
```

注入一次检索失败，观察调整查询后再读取原文：

```powershell
python -m knowledge_agent '正式员工年假最小可以请多久？' --fail-once search_documents --trace examples/manual/failure_trace.jsonl
```

持续失败和上限检查：

```powershell
python -m knowledge_agent '年假最小单位？' --always-fail search_documents
python -m knowledge_agent '年假最小单位？' --max-steps 1
python -m knowledge_agent '年假最小单位？' --max-tool-calls 1
```

这几条返回退出码2及明确的失败/未完成状态，属于预期验证结果。`conflict`、`needs_clarification`、`insufficient_evidence`是业务终态，CLI退出码0，但`complete=false`；只有`answered`的`complete=true`。

## 结果与Trace

最终JSON包括：`status`、`question`、`answer`、`citations`、`gaps`、`clarification`、`decision_steps`、`tool_calls`、`model_mode`、`complete`、`elapsed_ms`和模式边界。

每条引用含文档ID、片段ID、标题、版本日期、适用范围和精确原文。答案由已校验引文组合，不接受模型另写无依据的制度结论。

JSONL事件包括：

- `run_start`：输入、模式、上限。
- `decision`：动作、参数和一句简短目的。
- `model_response`：真实接口响应ID、模型名、HTTP状态、token用量和耗时；不记录内部思维内容。
- `tool_observation`：工具成功/失败、命中或原文。
- `policy_observation`：引用或冲突约束拒绝，供下一步适配器补查。
- `run_end`：实际最终状态及结果。

完整Trace不包含API密钥、请求头或隐藏思维链。可直接对照 [明确答案](examples/traces/01_clear.jsonl)、[制度冲突](examples/traces/02_conflict.jsonl)、[故障恢复](examples/traces/07_tool_recovery.jsonl) 和 [资料外问题](examples/traces/03_outside.jsonl)。

HTTP传输层最多尝试2次，仅重试网络错误或429/502/503/504；每次尝试均记录在`model_response.metadata.attempts`中。401/402等错误、截断或不合法模型动作不自动重试。这里的传输恢复不替代业务工具观察后的模型决策。

## 为什么有动态循环

`Agent.run`在每一步把实际工具观察送给适配器，再执行其返回的一个动作。正常查询只需读一条；冲突需要读两条并澄清；无结果改写查询；故障可调整查询或停止。框架只负责执行和校验，不在工具里隐式重试或预先写好成功日志。

`MockBackend`以有限的规则模拟这些决策，用来验证工程流程。它不是模型，不能据其动作序列宣称已经满足真实模型决策效果要求。`LiveBackend`使用完全相同的循环和边界，由实际接口逐步给出动作。真实模型运行证据和失败归档见`examples/live/runs/`，候选人在提交前可根据评估表逐例检查。

## DeepSeek真实模型运行

当前API密钥仍保留在项目外的用户文件中，运行时只读入内存，不复制到仓库。PowerShell中可直接运行：

```powershell
$env:AGENT_BASE_URL = 'https://api.deepseek.com'
$env:AGENT_MODEL = 'deepseek-flash'
python -m knowledge_agent '报销申请的提交期限是多久？' --mode live --api-key-file '../api.txt' --output examples/live/manual/conflict.json --trace examples/live/manual/conflict.jsonl
```

重新执行完整真实验收（会调用计费API，不在默认离线测试中隐式执行）：

```powershell
python scripts/run_live_examples.py --api-key-file '../api.txt'
python scripts/run_examples.py
python scripts/audit_submission.py --api-key-file '../api.txt'
```

每次真实运行创建独立归档目录，保留实际输入、输出和Trace；失败不会被成功记录覆盖。全套结果写入`examples/live/summary.json`，部分定向复测只写自己的归档与`latest_attempt.json`，不会伪装成完整验收。

DeepSeek接入依据官方[首次调用说明](https://api-docs.deepseek.com/)、[JSON输出](https://api-docs.deepseek.com/guides/json_mode/)和[Thinking模式](https://api-docs.deepseek.com/guides/thinking_mode/)。实际模型列表也已通过账号接口查询；本项目为结构化动作显式关闭DeepSeek thinking，不保存reasoning_content。

## 其他兼容接口配置

本轮不需要密钥；配置真实模型时复制 `.env.example` 为本地 `.env`，填入兼容Chat Completions接口的基础地址（如带`/v1`）、模型名和密钥：

```text
AGENT_BASE_URL=https://your-provider.example/v1
AGENT_MODEL=your-model-name
AGENT_API_KEY=your-local-secret
AGENT_TIMEOUT_SECONDS=45
AGENT_JSON_MODE=true
```

本机无鉴权兼容接口可留空密钥。真实接口请求路径为 `{AGENT_BASE_URL}/chat/completions`；若提供商不支持JSON模式可设`AGENT_JSON_MODE=false`，但模型正文仍须返回合法动作JSON。不同提供商的字段兼容性尚待实测。

```powershell
python -m knowledge_agent '报销申请的提交期限是多久？' --mode live --output examples/live/conflict.json --trace examples/live/conflict.jsonl
```

真实接口不可用、动作JSON无效、输出被token上限截断或配置缺失时明确失败，**不自动切换成Mock**。更换接口后应重跑验收。`examples/live/`中的脱敏输入/输出/Trace纳入提交范围，`examples/live/private/`、`.env`及密钥文件被gitignore排除。

## 数据与工具

`data/corpus.json`保存6份合成文档及8个片段。每个片段有`fact_key`和出现在原文里的`fact_value`，用于有限域冲突及引文检查；不是从问题里硬编码答案。修改原文时必须同步事实标注，工具会拒绝与原文不符的标注。

`data/aliases.json`是显式召回归一表。FTS5采用中文双字切分和BM25，不调用嵌入模型。`search_documents`仅返回候选与短摘要；`read_passage`只能按登记ID读取原文，不能读取路径或执行资料内容。

声明`insufficient_evidence`之前必须至少成功搜索一次，不能在未查资料时声称知识库没有答案；无效结束请求作为policy_observation返回模型，供其补查。

可换语料继续测试：

```powershell
python -m knowledge_agent '报销申请期限？' --corpus examples/fixtures/single_policy.json
python -m knowledge_agent '报销申请期限？' --corpus examples/fixtures/changed_policy.json
```

前者移除了冲突D02，应答30天；后者进一步把D01改为21天，应答21天。对应实际输出已落盘。未知新领域需要真实模型或扩充Mock意图，不能把Mock当作通用问答能力。

## 代码组织

```text
src/knowledge_agent/
  models.py       输入、资料、动作及结果契约
  store.py        FTS5检索、受限读取、显式故障注入
  backends.py     离线Mock与可配置真实HTTP适配器
  agent.py        有界决策→工具→观察循环和Trace
  policy.py       已读引文、事实值、候选和冲突约束
  cli.py          CLI、环境配置、JSON输出
tests/            验收、边界、CLI与HTTP模拟契约测试
scripts/          实际样例生成与评估材料汇总
data/             合成资料与别名表
examples/         输入、输出、Trace、测试XML与汇总
docs/             规范、需求、方案、评估、AI记录、复盘
```

依赖与职责：Pydantic 2.12.2做契约校验；httpx 0.28.1仅用于可选真实HTTP接口；python-dotenv 1.1.1只在live模式加载配置；pytest 8.4.2执行测试；SQLite FTS5来自Python标准库。未采用第三方Agent框架。

## 已知限制

当前原文摘录、事实标注和候选核对提供可审计边界，但不能证明任意问题的语义相关性、检索完整性或所有未标注冲突。Mock只覆盖合成演示域；真实模型的单轮场景验收不等于随机重复稳定性。企业权限、资料生命周期和生产部署未实现。个人手工审阅与贡献记录仍由候选人按实际操作补记。
