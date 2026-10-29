# DeepSeek真实模型逐步运行记录

所有动作来自实际HTTP响应；业务检索和读取在本地真实执行。故障由显式测试注入；未使用Mock模型。

记录简短动作目的、工具参数、观察和结果；不保存reasoning_content、密钥或HTTP请求头。

## 01_clear：明确答案

状态：`answered`；校验：通过。

[输入](inputs/01_clear.json) · [输出](outputs/01_clear.json) · [Trace](traces/01_clear.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 109ad229-f69d-49a5-a605-d692ea348572；token 1013|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位|
|1|tool_observation|命中：D03:P01, D05:P01, D03:P02|
|2|model_response|模型deepseek-flash；响应ID bd7d28ee-a6da-435f-a2f8-17da448696f4；token 1386|
|2|decision|read_passage(D03:P01)；读取正式员工年假最小申请单位的完整原文以确认规则|
|2|tool_observation|已读：D03:P01|
|3|model_response|模型deepseek-flash；响应ID bc4f9765-a189-4d8e-9e50-4241d3811c9c；token 1569|
|3|decision|finish(answered)；已读取正式员工年假规范原文，明确最小申请单位。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。此规则适用于中国大陆正式员工。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 02_conflict：制度冲突

状态：`model_error`；校验：未通过。

[输入](inputs/02_conflict.json) · [输出](outputs/02_conflict.json) · [Trace](traces/02_conflict.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型None；响应ID None；token 未提供|

实际回答：

模型接口或动作输出异常，当前任务未完成。

未通过原因：预期conflict，实际model_error；真实模型HTTP响应证据不完整；冲突双方引用、待确认状态或澄清问题不完整

## 03_outside：资料外问题

状态：`insufficient_evidence`；校验：通过。

[输入](inputs/03_outside.json) · [输出](outputs/03_outside.json) · [Trace](traces/03_outside.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 13f2a7f3-423e-4e83-b81f-3eb38884490d；token 1037|
|1|decision|finish(insufficient_evidence)；问题涉及火星基地氧气库存，属企业知识库外主题，无历史可补全，无证据可检索。|

实际回答：

现有资料不足以回答该问题，未生成无依据的事实答案。

## 04_paraphrase：改写问法

状态：`answered`；校验：通过。

[输入](inputs/04_paraphrase.json) · [输出](outputs/04_paraphrase.json) · [Trace](traces/04_paraphrase.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID f605e687-2c4a-4486-b43c-90afc36c471d；token 1011|
|1|decision|search_documents(年假 半天 休假 制度)；查询年假半天休假制度规定|
|1|tool_observation|命中：D03:P01, D02:P01, D01:P01, D03:P02, D05:P01|
|2|model_response|模型deepseek-flash；响应ID a6f4bcb6-2d08-4673-9882-499851f4aec0；token 1572|
|2|decision|read_passage(D03:P01)；读取年假最小申请单位原文以确认半天是否允许|
|2|tool_observation|已读：D03:P01|
|3|model_response|模型deepseek-flash；响应ID a72e8a5d-1c8a-49ad-8b9a-4e6838d62721；token 1758|
|3|decision|finish(answered)；已读取年假最小申请单位原文，可直接回答半天年假是否允许|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。此规则适用于中国大陆正式员工。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 05_context：上下文追问

状态：`answered`；校验：通过。

[输入](inputs/05_context.json) · [输出](outputs/05_context.json) · [Trace](traces/05_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID cd6ac9fe-8258-44c5-9b12-be0aa014218d；token 1066|
|1|decision|search_documents(实习生 年假 申请 适用范围)；确认实习生是否适用年假申请规则|
|1|tool_observation|命中：D05:P01, D03:P02, D03:P01, D01:P01, D02:P01|
|2|model_response|模型deepseek-flash；响应ID 91c3c1e8-517d-427e-8e31-265ed5d5bbfc；token 1628|
|2|decision|read_passage(D05:P01)；读取实习生年假适用性原文以确认能否申请|
|2|tool_observation|已读：D05:P01|
|3|model_response|模型deepseek-flash；响应ID 491b73dd-c2b1-40fc-9b27-497a55d04660；token 1828|
|3|decision|finish(answered)；已读取实习生年假适用性原文，可据原文回答|

实际回答：

根据本次已读取的资料：
- 实习生不适用正式员工带薪年假规则。实习生确需请假时，应联系指导人及人事确认安排。 [D05:P01；版本2025-02-10；适用范围：实习生]

## 06_missing_context：缺少制度主题

状态：`needs_clarification`；校验：通过。

[输入](inputs/06_missing_context.json) · [输出](outputs/06_missing_context.json) · [Trace](traces/06_missing_context.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID ba1138dc-be16-4ffc-8e21-ec8255d857dc；token 1032|
|1|decision|finish(needs_clarification)；问题缺少申请对象，且无历史可补全业务主题|

实际回答：

需要补充信息后才能继续。
请问您指的是实习生申请什么？例如年假、报销或文档导入权限等，请补充具体业务主题。

## 07_tool_recovery：检索失败后换查询

状态：`answered`；校验：通过。

[输入](inputs/07_tool_recovery.json) · [输出](outputs/07_tool_recovery.json) · [Trace](traces/07_tool_recovery.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID f0d6ba02-e64f-40bb-80d8-4f8f6b710374；token 1013|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位|
|1|tool_observation|失败：TOOL_UNAVAILABLE|
|2|model_response|模型deepseek-flash；响应ID cbc00dda-8f97-4987-b2d8-7b68f169a78d；token 1097|
|2|decision|search_documents(年假 请假 最小单位)；首次检索工具故障，简化查询重试年假请假单位|
|2|tool_observation|命中：D03:P01, D05:P01, D03:P02|
|3|model_response|模型deepseek-flash；响应ID 7b18019f-eee4-4bc7-9d4a-bf5b8d2a7f58；token 1461|
|3|decision|read_passage(D03:P01)；读取正式员工年假最小申请单位的完整原文以确认规则|
|3|tool_observation|已读：D03:P01|
|4|model_response|模型deepseek-flash；响应ID 1907468c-ce0a-42d5-b8ac-0a2ead35a922；token 1644|
|4|decision|finish(answered)；已读取正式员工年假规范原文，明确最小申请单位。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。此规则适用于中国大陆正式员工。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 08_tool_failure：工具持续失败

状态：`tool_error`；校验：通过。

[输入](inputs/08_tool_failure.json) · [输出](outputs/08_tool_failure.json) · [Trace](traces/08_tool_failure.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID ff741df1-170f-44f7-9615-f03b650847be；token 1015|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位的相关制度|
|1|tool_observation|失败：TOOL_UNAVAILABLE|
|2|model_response|模型deepseek-flash；响应ID 9500bead-2673-40ec-a1ae-2cf3dfdd6800；token 1097|
|2|decision|search_documents(年假 请假 最小单位)；首次检索工具故障，简化查询重试年假请假单位|
|2|tool_observation|失败：TOOL_UNAVAILABLE|
|3|model_response|模型deepseek-flash；响应ID b065e2f1-fe44-48e1-8882-4f99412f211a；token 1199|
|3|decision|finish(tool_error)；同一检索工具连续两次故障，无替代证据，停止并报告工具错误|

实际回答：

工具执行失败，当前任务未完成。

## 09_read_recovery：原文读取临时失败

状态：`answered`；校验：通过。

[输入](inputs/09_read_recovery.json) · [输出](outputs/09_read_recovery.json) · [Trace](traces/09_read_recovery.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 49e2ddf5-e3b5-4e9d-b3ca-ec23e8fd960e；token 1015|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位的相关制度|
|1|tool_observation|命中：D03:P01, D05:P01, D03:P02|
|2|model_response|模型deepseek-flash；响应ID 7d73694e-18f6-407c-9e2e-88abe4e9d649；token 1386|
|2|decision|read_passage(D03:P01)；读取正式员工年假最小申请单位的完整原文以确认规则|
|2|tool_observation|失败：TOOL_UNAVAILABLE|
|3|model_response|模型deepseek-flash；响应ID c16ffe78-ef22-4666-93b7-d7564b3b48bf；token 1457|
|3|decision|read_passage(D03:P01)；读取正式员工年假最小申请单位的完整原文以确认引用|
|3|tool_observation|已读：D03:P01|
|4|model_response|模型deepseek-flash；响应ID e4912dc4-8134-4f35-8e72-0e90bded0a2f；token 1638|
|4|decision|finish(answered)；已读取正式员工年假规范原文，明确最小申请单位|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。此规则适用于中国大陆正式员工。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 10_step_limit：步数上限

状态：`limit_reached`；校验：通过。

[输入](inputs/10_step_limit.json) · [输出](outputs/10_step_limit.json) · [Trace](traces/10_step_limit.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 428ce785-ae28-43c3-a076-a0dbbdb3c6e1；token 1015|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位的相关制度|
|1|tool_observation|命中：D03:P01, D05:P01, D03:P02|

实际回答：

已达到决策步数或工具调用上限，当前任务未完成。

## 11_call_limit：工具调用上限

状态：`limit_reached`；校验：通过。

[输入](inputs/11_call_limit.json) · [输出](outputs/11_call_limit.json) · [Trace](traces/11_call_limit.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 2a74393e-5744-4a56-8b10-9f2a4852131f；token 1015|
|1|decision|search_documents(正式员工年假最小请假时长 请假单位)；查询正式员工年假最小请假单位的相关制度|
|1|tool_observation|命中：D03:P01, D05:P01, D03:P02|
|2|model_response|模型deepseek-flash；响应ID fed17708-af94-4475-8c11-e57ae85657f3；token 1386|
|2|decision|read_passage(D03:P01)；读取正式员工年假最小申请单位的完整原文以确认规则|

实际回答：

已达到决策步数或工具调用上限，当前任务未完成。

## 12_single_policy：移除冲突文档

状态：`answered`；校验：通过。

[输入](inputs/12_single_policy.json) · [输出](outputs/12_single_policy.json) · [Trace](traces/12_single_policy.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 140fe608-57b1-4ae6-9514-e8a156e2e22d；token 1005|
|1|decision|search_documents(报销申请 提交期限)；查询报销申请提交期限的制度原文|
|1|tool_observation|命中：D06:P01, D01:P01, D03:P02, D03:P01|
|2|model_response|模型deepseek-flash；响应ID f063ee18-09a0-402f-8e41-62871a4a9212；token 1473|
|2|decision|read_passage(D01:P01)；读取报销提交期限候选原文以确认完整规则|
|2|tool_observation|已读：D01:P01|
|3|model_response|模型deepseek-flash；响应ID 2e10988c-3825-4bd9-a7fa-79faa7955223；token 1666|
|3|decision|finish(answered)；已读取唯一相关原文，明确提交期限|

实际回答：

根据本次已读取的资料：
- 报销申请应在费用发生后30个自然日内提交。 [D01:P01；版本2025-03-01；适用范围：未说明]

## 13_changed_policy：替换为21天制度

状态：`answered`；校验：通过。

[输入](inputs/13_changed_policy.json) · [输出](outputs/13_changed_policy.json) · [Trace](traces/13_changed_policy.jsonl)

|步骤|动作或观察|内容|
|---:|---|---|
|1|model_response|模型deepseek-flash；响应ID 28db6d8c-d3db-4b45-8e6a-576c18b8b2eb；token 1005|
|1|decision|search_documents(报销申请 提交期限)；查询报销申请提交期限的制度原文|
|1|tool_observation|命中：D06:P01, D01:P01, D03:P02, D03:P01|
|2|model_response|模型deepseek-flash；响应ID c5df1bf8-b5c0-46c4-81ec-ebb9e2f7dc93；token 1473|
|2|decision|read_passage(D01:P01)；读取报销提交期限候选原文以确认完整规则|
|2|tool_observation|已读：D01:P01|
|3|model_response|模型deepseek-flash；响应ID c7526371-228d-4d5e-9258-88233579a6e5；token 1632|
|3|decision|search_documents(报销 提交期限 自然日 制度)；查找是否存在其他报销提交期限制度以核对冲突|
|3|tool_observation|命中：D01:P01, D06:P01|
|4|model_response|模型deepseek-flash；响应ID 913cd44f-54b9-4c9a-8915-a79c493d0e4f；token 1907|
|4|decision|read_passage(D06:P01)；补读D06原文，确认是否含提交期限或冲突信息|
|4|tool_observation|已读：D06:P01|
|5|model_response|模型deepseek-flash；响应ID 556e9274-4de6-4222-91a0-ebb8750b52a4；token 2127|
|5|decision|finish(answered)；已读取唯一规定提交期限的原文，D06明确不规定期限，无冲突|

实际回答：

根据本次已读取的资料：
- 报销申请应在费用发生后21个自然日内提交。此份材料未说明适用部门及与其他制度的优先关系。 [D01:P01；版本2025-03-01；适用范围：未说明]
