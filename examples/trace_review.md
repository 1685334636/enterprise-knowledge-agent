# 离线运行Trace审阅

以下记录均来自程序实际执行；模式offline_mock，不是真实模型决策证明。

重点比较01明确答案、02制度冲突、03资料外问题、07检索失败恢复的工具路径。完整事件含观察原文，见JSONL文件。

## 01_clear：明确答案

输入：正式员工年假最小可以请多久？

终态：`answered`；决策3步，工具2次。

[输入](inputs/01_clear.json) · [实际输出](outputs/01_clear.json) · [完整Trace](traces/01_clear.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D03:P01, D03:P02, D05:P01|
|2|decision|read_passage(D03:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D03:P01|
|3|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 02_conflict：制度冲突

输入：报销申请的提交期限是多久？

终态：`conflict`；决策4步，工具3次。

[输入](inputs/02_conflict.json) · [实际输出](outputs/02_conflict.json) · [完整Trace](traces/02_conflict.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(报销申请的提交期限是多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D06:P01, D01:P01, D02:P01, D03:P02, D03:P01|
|2|decision|read_passage(D01:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D01:P01|
|3|decision|read_passage(D02:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|3|tool_observation|已读：D02:P01|
|4|decision|finish(conflict)；两条已读制度的事实值冲突且范围未决，列出双方并请求确认。|

实际回答：

已读取的制度存在冲突，当前不能确定统一答案：
- 报销申请应在费用发生后30个自然日内提交。 [D01:P01；版本2025-03-01；适用范围：未说明]
- 报销申请应在费用发生后15个自然日内提交。 [D02:P01；版本2025-06-01；适用范围：未说明]
请确认适用的部门、制度及优先关系；现有资料未说明应采用哪一条期限。

## 03_outside：资料外问题

输入：火星基地今天的氧气库存是多少？

终态：`insufficient_evidence`；决策3步，工具2次。

[输入](inputs/03_outside.json) · [实际输出](outputs/03_outside.json) · [完整Trace](traces/03_outside.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(火星基地今天的氧气库存是多少？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：无|
|2|decision|search_documents(资料 火星基地今天的氧气库存是多少？)；未获得可回答的相关证据，改写查询再检索一次。|
|2|tool_observation|命中：D04:P01|
|3|decision|finish(insufficient_evidence)；补充检索后仍无相关证据，明确停止并说明资料缺口。|

实际回答：

现有资料不足以回答该问题，未生成无依据的事实答案。

## 04_paraphrase：改写问法

输入：我想休半天年假，制度允许吗？

终态：`answered`；决策3步，工具2次。

[输入](inputs/04_paraphrase.json) · [实际输出](outputs/04_paraphrase.json) · [完整Trace](traces/04_paraphrase.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(我想休半天年假，制度允许吗？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D03:P01, D02:P01, D01:P01, D03:P02, D05:P01|
|2|decision|read_passage(D03:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D03:P01|
|3|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 05_context：上下文追问

输入：那实习生可以申请吗？

终态：`answered`；决策3步，工具2次。

[输入](inputs/05_context.json) · [实际输出](outputs/05_context.json) · [完整Trace](traces/05_context.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(那实习生可以申请吗？ 正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D05:P01, D03:P01, D03:P02, D01:P01, D06:P01|
|2|decision|read_passage(D05:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D05:P01|
|3|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 实习生不适用正式员工带薪年假规则。 [D05:P01；版本2025-02-10；适用范围：实习生]

## 06_missing_context：缺少制度主题

输入：那实习生可以申请吗？

终态：`needs_clarification`；决策1步，工具0次。

[输入](inputs/06_missing_context.json) · [实际输出](outputs/06_missing_context.json) · [完整Trace](traces/06_missing_context.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|finish(needs_clarification)；仅提到员工身份而未指定制度，需要先澄清查询范围。|

实际回答：

需要补充信息后才能继续。
你想查询实习生的年假资格、请假流程，还是其他制度？请补充具体主题。

## 07_tool_recovery：检索失败后换查询

输入：正式员工年假最小可以请多久？

终态：`answered`；决策4步，工具3次。

[输入](inputs/07_tool_recovery.json) · [实际输出](outputs/07_tool_recovery.json) · [完整Trace](traces/07_tool_recovery.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|失败：TOOL_UNAVAILABLE|
|2|decision|search_documents(年假 最小 单位)；首次检索失败，调整为简短主题词后重新查询。|
|2|tool_observation|命中：D03:P01, D03:P02, D05:P01|
|3|decision|read_passage(D03:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|3|tool_observation|已读：D03:P01|
|4|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 08_tool_failure：工具持续失败

输入：正式员工年假最小可以请多久？

终态：`tool_error`；决策3步，工具2次。

[输入](inputs/08_tool_failure.json) · [实际输出](outputs/08_tool_failure.json) · [完整Trace](traces/08_tool_failure.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|失败：TOOL_UNAVAILABLE|
|2|decision|search_documents(年假 最小 单位)；首次检索失败，调整为简短主题词后重新查询。|
|2|tool_observation|失败：TOOL_UNAVAILABLE|
|3|decision|finish(tool_error)；已观察到多次工具失败，停止并保留失败状态。|

实际回答：

工具执行失败，当前任务未完成。

## 09_read_recovery：原文读取临时失败

输入：正式员工年假最小可以请多久？

终态：`answered`；决策4步，工具3次。

[输入](inputs/09_read_recovery.json) · [实际输出](outputs/09_read_recovery.json) · [完整Trace](traces/09_read_recovery.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D03:P01, D03:P02, D05:P01|
|2|decision|read_passage(D03:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|失败：TOOL_UNAVAILABLE|
|3|decision|read_passage(D03:P01)；原文读取发生临时错误，显式决定再读取一次；失败不会记为已读。|
|3|tool_observation|已读：D03:P01|
|4|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 年假最小申请单位为0.5天。 [D03:P01；版本2025-01-15；适用范围：中国大陆正式员工]

## 10_step_limit：步数上限

输入：正式员工年假最小可以请多久？

终态：`limit_reached`；决策1步，工具1次。

[输入](inputs/10_step_limit.json) · [实际输出](outputs/10_step_limit.json) · [完整Trace](traces/10_step_limit.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D03:P01, D03:P02, D05:P01|

实际回答：

已达到决策步数或工具调用上限，当前任务未完成。

## 11_call_limit：工具调用上限

输入：正式员工年假最小可以请多久？

终态：`limit_reached`；决策2步，工具1次。

[输入](inputs/11_call_limit.json) · [实际输出](outputs/11_call_limit.json) · [完整Trace](traces/11_call_limit.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(正式员工年假最小可以请多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D03:P01, D03:P02, D05:P01|
|2|decision|read_passage(D03:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|

实际回答：

已达到决策步数或工具调用上限，当前任务未完成。

## 12_single_policy：移除冲突文档

输入：报销申请的提交期限是多久？

终态：`answered`；决策3步，工具2次。

[输入](inputs/12_single_policy.json) · [实际输出](outputs/12_single_policy.json) · [完整Trace](traces/12_single_policy.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(报销申请的提交期限是多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D06:P01, D01:P01, D03:P02, D03:P01|
|2|decision|read_passage(D01:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D01:P01|
|3|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 报销申请应在费用发生后30个自然日内提交。 [D01:P01；版本2025-03-01；适用范围：未说明]

## 13_changed_policy：替换为21天制度

输入：报销申请的提交期限是多久？

终态：`answered`；决策3步，工具2次。

[输入](inputs/13_changed_policy.json) · [实际输出](outputs/13_changed_policy.json) · [完整Trace](traces/13_changed_policy.jsonl)

|步骤|事件|内容|
|---:|---|---|
|1|decision|search_documents(报销申请的提交期限是多久？)；先检索与问题及已有上下文相关的制度候选。|
|1|tool_observation|命中：D06:P01, D01:P01, D03:P02, D03:P01|
|2|decision|read_passage(D01:P01)；读取相关候选的完整原文，检索摘要不能作为最终引用。|
|2|tool_observation|已读：D01:P01|
|3|decision|finish(answered)；相关原文已读取，未观察到同主题冲突，使用原文摘录回答。|

实际回答：

根据本次已读取的资料：
- 报销申请应在费用发生后21个自然日内提交。 [D01:P01；版本2025-03-01；适用范围：未说明]
