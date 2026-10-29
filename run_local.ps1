param([switch]$SkipTests)
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$taskPython = 'D:\anaconda\envs\hj13\python.exe'
if (-not (Test-Path -LiteralPath $taskPython)) { throw '找不到hj13解释器，请修改taskPython路径。' }
& $taskPython -m pip install -e . --no-deps --no-build-isolation
if ($LASTEXITCODE -ne 0) { throw '项目安装失败' }
if (-not $SkipTests) {
    & $taskPython -m pytest -q --junitxml=examples/test-results.xml
    if ($LASTEXITCODE -ne 0) { throw '测试失败' }
}
& $taskPython scripts/run_examples.py
if ($LASTEXITCODE -ne 0) { throw '案例验证失败' }
Write-Output '运行完成，查看 examples/trace_review.md 和 docs/03-evaluation.md。'
