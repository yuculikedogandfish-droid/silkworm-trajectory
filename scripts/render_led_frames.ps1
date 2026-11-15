# 离线逐帧渲染 + 编码（LED 母版）
# 用法示例（在仓库根目录执行）：
#   powershell -ExecutionPolicy Bypass -File scripts\render_led_frames.ps1 `
#     -Native "2419x1360" -Frames 900 -Fps 30 -Cfg "<从 weave-lab 复制的 cfg>"
#
# 原理：weave-lab.html 支持 ?native=1&frame=N&total=M&cfg=...，
#       该模式下隐藏全部 UI、画布固定为原生像素、按 frame 确定性重绘。
#       本脚本用无头 Chrome 逐帧截图，再用 ffmpeg 合成母版。
#
# 注意：单帧 PNG 约 4–10 MB（取决于内容），900 帧约 4–9 GB，先确认目标盘剩余空间。

param(
  [string]$Html     = "prototype\weave-lab.html",
  [string]$Native   = "2419x1360",
  [int]$Frames      = 300,
  [int]$Fps         = 30,
  [string]$Cfg      = "",
  [string]$OutDir   = "G:\led-render\frames",
  [string]$Chrome   = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [switch]$Encode,
  [switch]$KeepProfile,
  [switch]$Resume
)

$ErrorActionPreference = "Stop"

# ---- 解析分辨率 ----
if ($Native -notmatch '^\s*(\d+)\s*[xX×]\s*(\d+)\s*$') {
  throw "Native 参数必须是 宽x高，例如 2419x1360"
}
$pxW = [int]$Matches[1]
$pxH = [int]$Matches[2]

if (-not (Test-Path -LiteralPath $Chrome)) {
  throw "找不到 Chrome：$Chrome"
}

# ---- 页面绝对路径 → file:// URL ----
if ([IO.Path]::IsPathRooted($Html)) {
  $htmlPath = [IO.Path]::GetFullPath($Html)
} else {
  $htmlPath = [IO.Path]::GetFullPath((Join-Path (Get-Location) $Html))
}
if (-not (Test-Path -LiteralPath $htmlPath)) { throw "找不到页面：$htmlPath" }
$fileUrl = "file:///" + ($htmlPath -replace '\\', '/')

# ---- 输出目录与空间检查 ----
if (-not (Test-Path -LiteralPath $OutDir)) {
  New-Item -ItemType Directory -Path $OutDir -Force | Out-Null
}
$outRoot = [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($OutDir))
$driveName = $outRoot.Substring(0, 1)
$freeGB = [math]::Round((Get-PSDrive -Name $driveName).Free / 1GB, 2)
$needGB = [math]::Round(($Frames * 8) / 1024, 2)
Write-Host "目标分辨率 : $pxW x $pxH ($([math]::Round(($pxW*$pxH)/1e6,2)) MP)"
Write-Host "帧数 / 帧率: $Frames / $Fps （约 $([math]::Round($Frames/$Fps,1)) 秒）"
Write-Host "输出目录   : $OutDir"
Write-Host "剩余空间   : $freeGB GB（预估需要 $needGB GB）"
if ($freeGB -lt $needGB) {
  throw "磁盘空间不足：需要约 $needGB GB，当前只剩 $freeGB GB。换一个盘或用 -Frames 先出小样。"
}

# ---- 逐帧渲染 ----
$profileDir = Join-Path $env:TEMP ("_chrome-weave-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory -Path $profileDir -Force | Out-Null

$cfgEncoded = ""
if ($Cfg -ne "") { $cfgEncoded = [uri]::EscapeDataString($Cfg) }

$sw = [Diagnostics.Stopwatch]::StartNew()
$skipped = 0
for ($i = 0; $i -lt $Frames; $i++) {
  $frameFile = Join-Path $OutDir ("frame_{0:D4}.png" -f $i)
  if ($Resume -and (Test-Path -LiteralPath $frameFile) -and (Get-Item -LiteralPath $frameFile).Length -gt 0) {
    $skipped++
    continue
  }
  $query = "native=1&frame=$i&total=$Frames&w=$pxW&h=$pxH"
  if ($cfgEncoded -ne "") { $query += "&cfg=$cfgEncoded" }
  $url = "$fileUrl`?$query"

  $args = @(
    "--headless=new",
    "--no-first-run",
    "--no-default-browser-check",
    "--user-data-dir=$profileDir",
    "--disable-gpu",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
    "--window-size=$pxW,$pxH",
    "--virtual-time-budget=6000",
    "--screenshot=$frameFile",
    $url
  )
  $logErr = Join-Path $env:TEMP ("chrome-frame-" + $i + ".err.txt")
  $logOut = Join-Path $env:TEMP ("chrome-frame-" + $i + ".out.txt")
  $proc = Start-Process -FilePath $Chrome -ArgumentList $args -Wait -PassThru -WindowStyle Hidden -RedirectStandardError $logErr -RedirectStandardOutput $logOut
  if (-not (Test-Path -LiteralPath $frameFile)) {
    throw "第 $i 帧渲染失败：$frameFile"
  }
  if (($i + 1) % 25 -eq 0 -or $i -eq $Frames - 1) {
    $el = [math]::Round($sw.Elapsed.TotalSeconds, 1)
    Write-Host ("已渲染 {0}/{1} 帧，用时 {2}s" -f ($i + 1), $Frames, $el)
  }
}

if ($skipped -gt 0) { Write-Host "续渲：跳过已存在帧 $skipped 张" }
if (-not $KeepProfile) { Remove-Item -LiteralPath $profileDir -Recurse -Force -ErrorAction SilentlyContinue }

# 缺帧检查：不完整就拒绝编码，避免母版时间轴错位
$missing = @()
for ($i = 0; $i -lt $Frames; $i++) {
  $f = Join-Path $OutDir ("frame_{0:D4}.png" -f $i)
  if (-not (Test-Path -LiteralPath $f)) { $missing += $i }
}
if ($missing.Count -gt 0) {
  Write-Host "缺帧 $($missing.Count) 张（首个：$($missing[0])），先重跑 -Resume 补齐，已跳过编码。"
  exit 2
}
Write-Host "帧序列完成：$OutDir"

# ---- 编码 ----
$ffmpeg = (Get-Command ffmpeg -ErrorAction SilentlyContinue).Source
if (-not $ffmpeg) {
  # winget 装完新 shell 才刷新 PATH，这里兜底直接找包目录
  $wingetRoot = Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Packages"
  $found = Get-ChildItem -LiteralPath $wingetRoot -Recurse -Filter "ffmpeg.exe" -File -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($found) { $ffmpeg = $found.FullName }
}
$prores = Join-Path $OutDir "weave_master_prores.mov"
$h264   = Join-Path $OutDir "weave_playback_h264.mp4"
$cmdProres = "ffmpeg -y -framerate $Fps -start_number 0 -i `"$OutDir\frame_%04d.png`" -c:v prores_ks -profile:v 3 -pix_fmt yuv422p10le `"$prores`""
$cmdH264   = "ffmpeg -y -framerate $Fps -start_number 0 -i `"$OutDir\frame_%04d.png`" -c:v libx264 -crf 14 -preset slow -pix_fmt yuv420p `"$h264`""

if ($ffmpeg) {
  if ($Encode) {
    $logEnc = Join-Path $OutDir "encode.log"
    Write-Host "编码 ProRes 母版…"
    $a1 = @("-y", "-framerate", "$Fps", "-start_number", "0", "-i", (Join-Path $OutDir "frame_%04d.png"), "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", $prores)
    $p1 = Start-Process -FilePath $ffmpeg -ArgumentList $a1 -Wait -PassThru -WindowStyle Hidden -RedirectStandardError $logEnc -RedirectStandardOutput (Join-Path $OutDir "encode.out.txt")
    if ($p1.ExitCode -ne 0) { throw "ProRes 编码失败，见 $logEnc" }
    Write-Host "编码 H.264 播放版…"
    $a2 = @("-y", "-framerate", "$Fps", "-start_number", "0", "-i", (Join-Path $OutDir "frame_%04d.png"), "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-pix_fmt", "yuv420p", $h264)
    $p2 = Start-Process -FilePath $ffmpeg -ArgumentList $a2 -Wait -PassThru -WindowStyle Hidden -RedirectStandardError (Join-Path $OutDir "encode_h264.log") -RedirectStandardOutput (Join-Path $OutDir "encode_h264.out.txt")
    if ($p2.ExitCode -ne 0) { throw "H.264 编码失败，见 encode_h264.log" }
    Write-Host "完成：$prores / $h264"
  } else {
    Write-Host "已找到 ffmpeg，加 -Encode 可直接编码；否则手动执行："
    Write-Host $cmdProres
    Write-Host $cmdH264
  }
} else {
  Write-Host "未检测到 ffmpeg。安装：winget install Gyan.FFmpeg，然后重跑 -Encode；或把帧序列交给剪辑软件。"
  Write-Host $cmdProres
  Write-Host $cmdH264
}
