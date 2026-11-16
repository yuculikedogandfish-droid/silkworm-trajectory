# 离线逐帧渲染 + 编码（LED 母版）
# 用法示例（在仓库根目录执行）：
#   powershell -ExecutionPolicy Bypass -File scripts\render_led_frames.ps1 `
#     -Html docs\index.html -Scene led-scene.json -Native "2419x1360" -Frames 900 -Fps 30 -Encode
#
# 两种输入：
#   1) -Scene <led-scene.json>（主程序「母版导出」产出）：脚本把场景 JSON 注入页面副本，
#      逐帧以 ?native=1&frame=N&total=M 渲染，确定性、可续渲。
#   2) -Cfg "<weave-lab 的 cfg>"：老路径，走 prototype\weave-lab.html。
#
# 注意：单帧 PNG 约 4–10 MB（取决于内容），900 帧约 4–9 GB，先确认目标盘剩余空间。

param(
  [string]$Html     = "prototype\weave-lab.html",
  [string]$Native   = "",
  [int]$Frames      = 0,
  [int]$Fps         = 0,
  [string]$Scene    = "",
  [string]$Cfg      = "",
  [string]$OutDir   = "G:\led-render\frames",
  [string]$Chrome   = "C:\Program Files\Google\Chrome\Application\chrome.exe",
  [switch]$Encode,
  [switch]$KeepProfile,
  [switch]$Resume,
  # 单帧超时 + 自动重试：无头 Chrome 偶尔会整帧挂死（长跑 900 帧必踩），
  # 以前遇到就直接 throw 中断整条渲染，现在改成杀掉重来。
  [int]$FrameTimeoutSec = 90,
  [int]$FrameRetries = 2
)

$ErrorActionPreference = "Stop"

# ---- 读场景（可选）----
$sceneJson = ""
if ($Scene -ne "") {
  $scenePath = [IO.Path]::GetFullPath($Scene)
  if (-not (Test-Path -LiteralPath $scenePath)) { throw "找不到场景文件：$scenePath" }
  $sceneJson = [IO.File]::ReadAllText($scenePath, [Text.Encoding]::UTF8)
  if ($sceneJson -notmatch '"units"') { throw "场景文件里没有 units 字段，不是母版场景 JSON" }
  $sceneObj = $sceneJson | ConvertFrom-Json
  if ($Native -eq "" -and $sceneObj.px) { $Native = "$($sceneObj.px.w)x$($sceneObj.px.h)" }
  if ($Frames -le 0 -and $sceneObj.frames) { $Frames = [int]$sceneObj.frames }
  if ($Fps -le 0 -and $sceneObj.fps) { $Fps = [int]$sceneObj.fps }
  Write-Host "场景文件   : $scenePath（$($sceneObj.units.Count) 个织网单元）"
}
if ($Native -eq "") { $Native = "2419x1360" }
if ($Frames -le 0) { $Frames = 300 }
if ($Fps -le 0) { $Fps = 30 }

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

# ---- 场景模式：把 led-scene.json 注入页面副本，避免超长 URL ----
$tmpHtml = ""
if ($sceneJson -ne "") {
  $tmpHtml = Join-Path $env:TEMP ("led-scene-" + [guid]::NewGuid().ToString("N").Substring(0, 8) + ".html")
  $src = [IO.File]::ReadAllText($htmlPath, [Text.Encoding]::UTF8)
  $inject = "<script>window.__LED_SCENE=" + $sceneJson + ";</script>"
  $headEnd = $src.IndexOf("</head>")
  if ($headEnd -lt 0) { throw "页面里找不到 </head>，无法注入场景" }
  $src = $src.Insert($headEnd, $inject)
  [IO.File]::WriteAllText($tmpHtml, $src, (New-Object Text.UTF8Encoding($false)))
  $fileUrl = "file:///" + ($tmpHtml -replace '\\', '/')
}

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
  $ok = $false
  for ($try = 0; $try -le $FrameRetries -and -not $ok; $try++) {
    if ($try -gt 0) {
      # 上一轮留下的半截文件先删掉，否则截图会被误判为成功
      if (Test-Path -LiteralPath $frameFile) { Remove-Item -LiteralPath $frameFile -Force -ErrorAction SilentlyContinue }
      Write-Host ("  第 {0} 帧超时/失败，重试 {1}/{2}" -f $i, $try, $FrameRetries)
    }
    $proc = Start-Process -FilePath $Chrome -ArgumentList $args -PassThru -WindowStyle Hidden -RedirectStandardError $logErr -RedirectStandardOutput $logOut
    try {
      $proc | Wait-Process -Timeout $FrameTimeoutSec -ErrorAction Stop
    } catch {
      Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
      Get-Process chrome -ErrorAction SilentlyContinue |
        Where-Object { $_.StartTime -gt (Get-Date).AddSeconds(-$FrameTimeoutSec - 10) } |
        Stop-Process -Force -ErrorAction SilentlyContinue
      continue
    }
    if ((Test-Path -LiteralPath $frameFile) -and (Get-Item -LiteralPath $frameFile).Length -gt 0) { $ok = $true }
  }
  if (-not $ok) { throw "第 $i 帧渲染失败（已重试 $FrameRetries 次）：$frameFile" }
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
$cmdH264   = "ffmpeg -y -framerate $Fps -start_number 0 -i `"$OutDir\frame_%04d.png`" -c:v libx264 -crf 14 -preset slow -vf pad=ceil(iw/2)*2:ceil(ih/2)*2 -pix_fmt yuv420p `"$h264`""

if ($ffmpeg) {
  if ($Encode) {
    $logEnc = Join-Path $OutDir "encode.log"
    Write-Host "编码 ProRes 母版…"
    $a1 = @("-y", "-framerate", "$Fps", "-start_number", "0", "-i", (Join-Path $OutDir "frame_%04d.png"), "-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", $prores)
    $p1 = Start-Process -FilePath $ffmpeg -ArgumentList $a1 -Wait -PassThru -WindowStyle Hidden -RedirectStandardError $logEnc -RedirectStandardOutput (Join-Path $OutDir "encode.out.txt")
    if ($p1.ExitCode -ne 0) { throw "ProRes 编码失败，见 $logEnc" }
    Write-Host "编码 H.264 播放版…"
    $a2 = @("-y", "-framerate", "$Fps", "-start_number", "0", "-i", (Join-Path $OutDir "frame_%04d.png"), "-c:v", "libx264", "-crf", "14", "-preset", "slow", "-vf", "pad=ceil(iw/2)*2:ceil(ih/2)*2", "-pix_fmt", "yuv420p", $h264)
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
