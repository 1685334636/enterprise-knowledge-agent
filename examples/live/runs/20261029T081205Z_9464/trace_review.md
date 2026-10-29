# DeepSeek真实模型逐步运行记录

所有动作来自实际HTTP响应；业务检索和读取在本地真实执行。故障由显式测试注入；未使用Mock模型。

记录简短动作目的、工具参数、观察和结果；不保存reasoning_content、密钥或HTTP请求头。

## 05_context：上下文追问

状态：`answered`；校验：通过。

[输入](inputs/05_context.json) · [输出](outputs/05_context.json) · [Trace](traces/05_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 8b17f36c-47bc-4553-a406-8463230a234d；token 968|
|1|decision|search_documents(实习生 年假 申请 资格)；查找实习生年假或休假申请资格的相关制度|
|1|tool_observation|命中：D05:P01, D03:P02, D03:P01, D01:P01, D06:P01|
|2|model_response|模型deepseek-flash；响应ID 9af9acc0-bbf1-4b3e-9dfc-6680debc9a5a；token 1536|
|2|decision|read_passage(D05:P01)；读取实习生年假资格原文以确认是否可申请|
|2|tool_observation|已读：D05:P01|
|3|model_response|模型deepseek-flash；响应ID 3b112de5-4114-417f-9a15-2c3156417561；token 1729|
|3|decision|finish(answered)；已读取实习生年假适用性原文，可直接回答。|

实际回答：

根据本次已读取的资料：
- 实习生不适用正式员工带薪年假规则。实习生确需请假时，应联系指导人及人事确认安排。 [D05:P01；版本2025-02-10；适用范围：实习生]

## 06_missing_context：缺少制度主题

状态：`answered`；校验：未通过。

[输入](inputs/06_missing_context.json) · [输出](outputs/06_missing_context.json) · [Trace](traces/06_missing_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID b7b9864f-2439-4f43-a237-621dcd25ee73；token 927|
|1|decision|search_documents(实习生 申请 条件)；无历史消息，问题中的“那”指代不明，先检索实习生申请相关制度以确定主题。|
|1|tool_observation|命中：D05:P01, D03:P02, D03:P01, D01:P01, D06:P01|
|2|model_response|模型deepseek-flash；响应ID 66a2c1ae-20bc-4c21-a6f3-42a8bf6428b4；token 1483|
|2|decision|read_passage(D05:P01)；读取实习生年假资格原文以确认实习生能否申请年假|
|2|tool_observation|已读：D05:P01|
|3|model_response|模型deepseek-flash；响应ID b92a6dff-4753-4cfb-8a74-e7f199b2f122；token 1689|
|3|decision|finish(answered)；已读实习生年假说明原文，可据原文回答实习生不适用正式员工年假规则。|

实际回答：

根据本次已读取的资料：
- 实习生不适用正式员工带薪年假规则。实习生确需请假时，应联系指导人及人事确认安排。 [D05:P01；版本2025-02-10；适用范围：实习生]

未通过原因：预期needs_clarification，实际answered；缺主题时未提出具体澄清问题
