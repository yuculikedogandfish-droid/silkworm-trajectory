# github-push.ps1 —— 在 github.com 被 DNS 污染 / 连接被重置的环境里稳定推送
#
# 背景：本机 `github.com:443` 有时解析到一个不通的地址，git push 会报
#   `Recv failure: Connection was reset` / `Failed to connect to github.com port 443 after N ms`。
# 而 GitHub 的部分 IP（如 140.82.113.4）其实能连通。这个脚本：
#   1) 先照常 push，能通就直接结束（不多做任何事）；
#   2) 不通时，用一个 IP 测哪个 GitHub 地址是活的（curl --resolve，证书仍然按 github.com 校验）；
#   3) 起一个本地 CONNECT 隧道（tools/gh-tunnel.py），把 github.com 指到活 IP，再从隧道 push；
#   4) 推完立刻关掉隧道，不留后台进程、不改 hosts、不改全局 git 配置。
#
# 用法（仓库根目录或任意目录都行）：
#   pwsh -File tools\github-push.ps1                 # 推当前分支
#   pwsh -File tools\github-push.ps1 -Branch main
#   pwsh -File tools\github-push.ps1 -SkipFastPath   # 直接走隧道

param(
  [string]$Remote = "origin",
  [string]$Branch = "",
  [int]$TunnelPort = 8899,
  [switch]$SkipFastPath,
  [string[]]$Candidates = @("140.82.113.4", "140.82.112.4", "140.82.114.4", "140.82.121.4", "20.205.243.166", "20.27.177.113")
)

$ErrorCode = 0
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not $Branch) {
  $Branch = (& git rev-parse --abbrev-ref HEAD).Trim()
  if (-not $Branch -or $Branch -eq "HEAD") { Write-Host "无法判断当前分支，请用 -Branch 指定。"; exit 2 }
}

function Test-GitHubIp([string]$ip) {
  # --resolve 只影响这次连接：TLS 仍是 github.com 的证书，通不通看返回码
  $code = (& curl.exe -sS -o NUL --max-time 8 --resolve "github.com:443:$ip" -w "%{http_code}" https://github.com/ 2>$null)
  return ($LASTEXITCODE -eq 0 -and $code -and $code -match "^[23]")
}

Write-Host "== 1/3 先试直连 push（$Remote $Branch）"
if (-not $SkipFastPath) {
  & git -c "http.version=HTTP/1.1" push $Remote $Branch
  if ($LASTEXITCODE -eq 0) { Write-Host "直连可用，已经推送完成。"; exit 0 }
  Write-Host "直连不通（常见于 DNS 污染 / Connection reset），改走隧道。"
}

Write-Host "== 2/3 找可用的 GitHub IP"
$good = $null
foreach ($ip in $Candidates) {
  Write-Host ("  试 $ip ... ") -NoNewline
  if (Test-GitHubIp $ip) { Write-Host "通"; $good = $ip; break } else { Write-Host "不通" }
}
if (-not $good) {
  Write-Host "候选 IP 都不通：可能是整段被挡。可以用 -Candidates 再补几个 IP，或换网络。"
  exit 3
}
Write-Host "用 $good"

Write-Host "== 3/3 起隧道并推送"
$python = (Get-Command python -ErrorAction SilentlyContinue)
if (-not $python) { Write-Host "本机没有 python，无法起隧道（gh-tunnel.py 需要 Python 3）。"; exit 4 }

$tunnel = Start-Process -FilePath $python.Source -ArgumentList @("$PSScriptRoot\gh-tunnel.py", "--port", "$TunnelPort", "--map", "github.com=$good,api.github.com=$good") -WindowStyle Hidden -PassThru
try {
  Start-Sleep -Milliseconds 600
  $proxy = "http://127.0.0.1:$TunnelPort"
  & git -c "http.proxy=$proxy" -c "https.proxy=$proxy" -c "http.sslVerify=true" -c "http.version=HTTP/1.1" push $Remote $Branch
  if ($LASTEXITCODE -eq 0) {
    Write-Host "推送完成（经隧道 $good）。"
  } else {
    Write-Host "隧道里推送也失败（退出码 $LASTEXITCODE）。把完整输出发我，我再看。"
    $ErrorCode = 5
  }
} finally {
  if ($tunnel -and -not $tunnel.HasExited) { Stop-Process -Id $tunnel.Id -Force }
  Write-Host "隧道已关闭。"
}
exit $ErrorCode

