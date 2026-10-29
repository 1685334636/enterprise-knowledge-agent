# 评估与验证记录

本文保留上传前生成的本地验证快照；后续公开交付入口与提交查询方法见[公开提交说明](07-github-submission.md)。

## 本轮结论

13类离线场景实际执行：13/13符合预期。pytest记录：60项，失败0项、错误0项、跳过0项。

使用hj13环境；具体解释器、依赖版本、源码SHA-256、计时范围见 [summary.json](../examples/summary.json)。

**真实模型已接入并完成本地场景验证：DeepSeek / deepseek-flash，13/13通过。** 模型决策请求39次、HTTP尝试39次，已返回的用量合计52401 token；这是单轮场景结果，不代表随机重复稳定性。

## 离线验收与材料对应

|案例 / 验收点|预期 / 实际|步数 / 工具次数|材料|
|---|---|---|---|
|明确答案 / A01|answered / answered|3 / 2|[输入](../examples/inputs/01_clear.json) · [输出](../examples/outputs/01_clear.json) · [Trace](../examples/traces/01_clear.jsonl)|
|制度冲突 / A02|conflict / conflict|4 / 3|[输入](../examples/inputs/02_conflict.json) · [输出](../examples/outputs/02_conflict.json) · [Trace](../examples/traces/02_conflict.jsonl)|
|资料外问题 / A03|insufficient_evidence / insufficient_evidence|3 / 2|[输入](../examples/inputs/03_outside.json) · [输出](../examples/outputs/03_outside.json) · [Trace](../examples/traces/03_outside.jsonl)|
|改写问法 / A04|answered / answered|3 / 2|[输入](../examples/inputs/04_paraphrase.json) · [输出](../examples/outputs/04_paraphrase.json) · [Trace](../examples/traces/04_paraphrase.jsonl)|
|上下文追问 / A05|answered / answered|3 / 2|[输入](../examples/inputs/05_context.json) · [输出](../examples/outputs/05_context.json) · [Trace](../examples/traces/05_context.jsonl)|
|缺少制度主题 / A05|needs_clarification / needs_clarification|1 / 0|[输入](../examples/inputs/06_missing_context.json) · [输出](../examples/outputs/06_missing_context.json) · [Trace](../examples/traces/06_missing_context.jsonl)|
|检索失败后换查询 / A06|answered / answered|4 / 3|[输入](../examples/inputs/07_tool_recovery.json) · [输出](../examples/outputs/07_tool_recovery.json) · [Trace](../examples/traces/07_tool_recovery.jsonl)|
|工具持续失败 / A06|tool_error / tool_error|3 / 2|[输入](../examples/inputs/08_tool_failure.json) · [输出](../examples/outputs/08_tool_failure.json) · [Trace](../examples/traces/08_tool_failure.jsonl)|
|原文读取临时失败 / A06|answered / answered|4 / 3|[输入](../examples/inputs/09_read_recovery.json) · [输出](../examples/outputs/09_read_recovery.json) · [Trace](../examples/traces/09_read_recovery.jsonl)|
|步数上限 / A07|limit_reached / limit_reached|1 / 1|[输入](../examples/inputs/10_step_limit.json) · [输出](../examples/outputs/10_step_limit.json) · [Trace](../examples/traces/10_step_limit.jsonl)|
|工具调用上限 / A07|limit_reached / limit_reached|2 / 1|[输入](../examples/inputs/11_call_limit.json) · [输出](../examples/outputs/11_call_limit.json) · [Trace](../examples/traces/11_call_limit.jsonl)|
|移除冲突文档 / A09|answered / answered|3 / 2|[输入](../examples/inputs/12_single_policy.json) · [输出](../examples/outputs/12_single_policy.json) · [Trace](../examples/traces/12_single_policy.jsonl)|
|替换为21天制度 / A09|answered / answered|3 / 2|[输入](../examples/inputs/13_changed_policy.json) · [输出](../examples/outputs/13_changed_policy.json) · [Trace](../examples/traces/13_changed_policy.jsonl)|

## 真实模型验收与材料对应

模型：deepseek-flash；核验时间UTC：2026-10-29T08:29:43.504542+00:00。

[真实汇总](../examples/live/summary.json) · [逐步审阅](../examples/live/runs/20261029T082758Z_8d0c/trace_review.md)

|场景 / 验收点|预期 / 实际|模型请求 / 工具调用|材料|
|---|---|---|---|
|明确答案 / A01|answered / answered|3 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/01_clear.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/01_clear.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/01_clear.jsonl)|
|制度冲突 / A02|conflict / conflict|4 / 3|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/02_conflict.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/02_conflict.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/02_conflict.jsonl)|
|资料外问题 / A03|insufficient_evidence / insufficient_evidence|4 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/03_outside.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/03_outside.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/03_outside.jsonl)|
|改写问法 / A04|answered / answered|3 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/04_paraphrase.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/04_paraphrase.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/04_paraphrase.jsonl)|
|上下文追问 / A05|answered / answered|3 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/05_context.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/05_context.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/05_context.jsonl)|
|缺少制度主题 / A05|needs_clarification / needs_clarification|1 / 0|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/06_missing_context.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/06_missing_context.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/06_missing_context.jsonl)|
|检索失败后换查询 / A06|answered / answered|4 / 3|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/07_tool_recovery.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/07_tool_recovery.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/07_tool_recovery.jsonl)|
|工具持续失败 / A06|tool_error / tool_error|3 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/08_tool_failure.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/08_tool_failure.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/08_tool_failure.jsonl)|
|原文读取临时失败 / A06|answered / answered|4 / 3|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/09_read_recovery.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/09_read_recovery.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/09_read_recovery.jsonl)|
|步数上限 / A07|limit_reached / limit_reached|1 / 1|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/10_step_limit.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/10_step_limit.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/10_step_limit.jsonl)|
|工具调用上限 / A07|limit_reached / limit_reached|2 / 1|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/11_call_limit.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/11_call_limit.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/11_call_limit.jsonl)|
|移除冲突文档 / A09|answered / answered|3 / 2|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/12_single_policy.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/12_single_policy.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/12_single_policy.jsonl)|
|替换为21天制度 / A09|answered / answered|4 / 3|[输入](../examples/live/runs/20261029T082758Z_8d0c/inputs/13_changed_policy.json) · [输出](../examples/live/runs/20261029T082758Z_8d0c/outputs/13_changed_policy.json) · [Trace](../examples/live/runs/20261029T082758Z_8d0c/traces/13_changed_policy.jsonl)|

Trace中的model_response只记录模型名、响应ID、HTTP状态、token用量及耗时；真实模型动作与工具观察相间出现。业务工具故障为明确注入，不冒充DeepSeek接口故障。

## 真实模型尝试记录（包含失败）

|归档|范围|实际通过|未通过案例|
|---|---|---|---|
|[原始汇总](../examples/live/runs/20261029T080720Z_b93c/summary.json)|全套|12/13|05_context|
|[原始汇总](../examples/live/runs/20261029T081205Z_9464/summary.json)|定向复测|1/2|06_missing_context|
|[原始汇总](../examples/live/runs/20261029T081844Z_8e9f/summary.json)|全套|12/13|06_missing_context|
|[原始汇总](../examples/live/runs/20261029T082053Z_9433/summary.json)|定向复测|2/2|无|
|[原始汇总](../examples/live/runs/20261029T082309Z_a3c1/summary.json)|全套|12/13|02_conflict|
|[原始汇总](../examples/live/runs/20261029T082758Z_8d0c/summary.json)|全套|13/13|无|

A08（引用校验）、A11（资料和工具边界）由tests/test_guards.py覆盖；A10的完整记录和路径差异由生成脚本及tests/test_acceptance.py核对。

## 路径差异

- 明确答案：检索 → 读取一条原文 → 摘录回答。
- 制度冲突：检索 → 读取两条期限制度 → 列双方引用并澄清。
- 资料外：检索无相关依据 → 改写查询 → 仍无依据则停止。
- 临时故障：第一次检索失败 → 改为短查询 → 读取 → 回答；没有工具内部自动重试。
- 持续故障：再次失败后返回tool_error，complete=false。
- 资料替换：去掉D02后答30天；将D01替换成21天后答案也变为21天。

可读逐步记录见 [Trace审阅](../examples/trace_review.md)。

## 实际发现和修复

第一轮测试44项中43项通过：英文annual leave能被检索别名召回，但Mock意图选择没有同样归一，导致错误返回资料不足。补齐适配器对该别名的处理后回归；中文改写、英文别名和资料替换均有专门测试。

测试还主动使用测试替身尝试引用未读文档、改写数字、只引用冲突的一方、声明不存在的工具故障以及发出shell动作；运行时应拒绝或返回明确未完成状态。这些是边界测试，不是假装真实模型进行了这些行为。

## 已知限制与未完成项

1. 已验证的真实模型结果只覆盖本次指定场景；随机重复稳定性、更广措辞和其他提供商兼容性未作完整评估。
2. FTS5和显式别名适合本例小语料；不保证开放域语义召回。Mock只认识演示领域的有限意图。
3. 冲突检查依赖人工事实标注及当前已检索/读取候选；遗漏的文档或未标注的语义冲突可能无法识别。
4. 原文摘录和事实值校验保证引用真实性，不自动证明对所有开放式问题的相关性或语义充分性。
5. 未做企业权限、文档生命周期和生产部署；未上传GitHub。
6. 候选人本人的手工审阅和修改仍待如实补记，不能把AI生成工作写成个人独立贡献。

## 真实模型问题及修复

第一轮完整真实调用为12/13：上下文追问被误判为缺少主题。原记录保留，没有改写失败。将历史从嵌套JSON调整为正式user/assistant消息，并把澄清条件改为结合历史后仍不能确定主题；增加HTTP消息结构回归测试，然后进行定向和全套真实复测。

只修复历史格式后，进一步观察到无历史时模型会凭实习生身份猜测年假主题；这一失败也保留在归档。随后明确区分适用对象与业务主题：身份不能充当申请对象；主题可从真实历史继承。两个相反边界一起复测，不通过放宽预期或修改输出解决问题。

另一轮真实运行遇到一次在收到HTTP响应前发生的连接失败，原model_error记录保留。传输层增加最多2次尝试，只对网络错误或429/502/503/504重试；鉴权/余额错误及无效模型动作不重试。每次尝试记录状态或异常类型，业务工具的失败恢复仍由模型独立决策。另增加证据约束：未成功搜索时不能断言资料库没有依据。

## 本地完成与提交的边界

本地材料是否齐备见docs/06-submission-checklist.md。GitHub URL、最终commit SHA及可能需要的私有仓库访问权限尚未生成，按用户指令等待后续上传命令。个人审阅记录只由候选人按实际操作补记。
