# DeepSeek真实模型逐步运行记录

所有动作来自实际HTTP响应；业务检索和读取在本地真实执行。故障由显式测试注入；未使用Mock模型。

记录简短动作目的、工具参数、观察和结果；不保存reasoning_content、密钥或HTTP请求头。

## 05_context：上下文追问

状态：`answered`；校验：通过。

[输入](inputs/05_context.json) · [输出](outputs/05_context.json) · [Trace](traces/05_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID e5b3d2af-7e63-498b-a9e9-672b08c47b4f；token 1056|
|1|decision|search_documents(实习生 年假 申请)；查询实习生是否适用年假制度|
|1|tool_observation|命中：D05:P01, D03:P02, D03:P01, D01:P01, D06:P01|
|2|model_response|模型deepseek-flash；响应ID 260da309-2e6a-4e32-b70b-0514c4ff0171；token 1625|
|2|decision|read_passage(D05:P01)；读取实习生年假适用性原文以确认能否申请|
|2|tool_observation|已读：D05:P01|
|3|model_response|模型deepseek-flash；响应ID d31dd0db-b835-4d31-ae04-cc2ef655efe2；token 1817|
|3|decision|finish(answered)；已读取实习生年假适用性原文，可直接回答|

实际回答：

根据本次已读取的资料：
- 实习生不适用正式员工带薪年假规则。实习生确需请假时，应联系指导人及人事确认安排。 [D05:P01；版本2025-02-10；适用范围：实习生]

## 06_missing_context：缺少制度主题

状态：`needs_clarification`；校验：通过。

[输入](inputs/06_missing_context.json) · [输出](outputs/06_missing_context.json) · [Trace](traces/06_missing_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 9b7ddcca-27cc-4a89-95b0-6db97f5b1148；token 1032|
|1|decision|finish(needs_clarification)；问题缺少申请对象，且无历史可补全主题|

实际回答：

需要补充信息后才能继续。
请问您指的是实习生申请哪项事项？例如年假、报销或文档导入等，请补充具体业务主题。
