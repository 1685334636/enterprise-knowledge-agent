# 公开提交说明

- 题号：第3题，企业知识问答 Agent。
- 公开仓库：[1685334636/enterprise-knowledge-agent](https://github.com/1685334636/enterprise-knowledge-agent)。
- 默认分支：main。
- 最新提交：[main分支提交记录](https://github.com/1685334636/enterprise-knowledge-agent/commits/main/)。正式填报时使用最终提交的完整SHA及其固定链接。

## 审阅入口

1. [README](../README.md)：环境、安装、CLI和审阅入口。
2. [产品需求](01-requirements.md)、[技术方案](02-solution.md)、[评估报告](03-evaluation.md)。
3. [真实模型汇总](../examples/live/summary.json)：DeepSeek 13/13，39次真实决策请求，含可追踪响应ID及token用量。
4. [离线汇总](../examples/summary.json)与[自动测试记录](../examples/test-results.xml)：13组离线案例、60项自动测试。
5. [AI使用记录](04-ai-usage.md)与[复盘](05-retrospective.md)：辅助范围、实际失败、修复和验证边界。

## 最终提交SHA

本地查询：

```powershell
git rev-parse HEAD
```

远程查询：

```powershell
gh api repos/1685334636/enterprise-knowledge-agent/commits/main --jq .sha
```

固定提交链接格式为 `https://github.com/1685334636/enterprise-knowledge-agent/commit/<完整SHA>`。

## 验证与公开范围

本次公开的是agent_test项目：源码、测试、合成资料、文档和脱敏运行记录。DeepSeek密钥保留在项目外，未纳入提交；`.env`、缓存及安装中间文件由gitignore排除。原试题截图及无关个人文件未纳入项目。

docs/03、docs/06和examples/submission_audit.json保留了上传前的本地验证快照，其中“等待上传”及`github_uploaded=false`描述的是当时的状态。公开交付入口以本文及仓库实际状态为准；本次发布没有修改已验证的运行源码、测试和合成数据。

公开仓库可以直接审阅，无需私有仓库评审授权。候选人个人手工修改与审阅只应按本人实际操作补记，不把AI生成和自动执行工作改写为个人独立贡献。
