# 本地交付与提交清单

本文是上传前的自动核对快照，其中等待上传的项目描述当时状态。后续公开仓库及提交说明见[公开提交说明](07-github-submission.md)。

本地核对：**通过**。本文件由scripts/audit_submission.py核对实际产物后生成，不执行上传。

|要求|状态|证据|
|---|---|---|
|题号及运行入口|已提供|[README](../README.md)|
|src、tests、examples、data及docs|已提供|目录与规定文件逐项核对|
|需求、方案、评估、AI记录及复盘|已提供|docs/01–05|
|依赖及环境变量示例|已提供|requirements.txt、pyproject.toml、.env.example|
|可执行测试|60项通过|[JUnit XML](../examples/test-results.xml)|
|离线输入/输出/Trace|13/13通过|[离线汇总](../examples/summary.json)|
|真实模型输入/输出/Trace|13/13通过|[真实汇总](../examples/live/summary.json)|
|至少两条真实动态路径|9条不同动作序列|[逐步审阅](../examples/live/runs/20261029T082758Z_8d0c/trace_review.md)|
|工具失败及调用上限|已验证，保留未完成状态|真实案例07–11及边界测试|
|文档原文引用及冲突|逐条核对本轮已读原文|真实案例01、02、05、12、13|
|密钥及内部思维内容|未纳入提交材料|密钥文件留在项目外；Trace只记录安全元信息|
|AI辅助范围与个人贡献|已如实说明，个人自审待本人补记|[AI记录](04-ai-usage.md)|
|GitHub URL及最终commit SHA|等待用户上传命令|本轮没有创建远程仓库或推送|

本地验收通过不等于已经完成平台提交。仓库地址、最终提交SHA以及必要的评审权限在后续上传时补齐。

核对结果见 [submission_audit.json](../examples/submission_audit.json)。
