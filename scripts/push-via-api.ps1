$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot\..

$owner = 'yuculikedogandfish-droid'
$repo = 'silkworm-trajectory'
$message = $args[0]
if (-not $message) { $message = 'Update files via API (base_tree)' }
$utf8 = New-Object System.Text.UTF8Encoding $false

function Write-JsonFile($path, $obj) {
  $json = $obj | ConvertTo-Json -Depth 8 -Compress
  [System.IO.File]::WriteAllText($path, $json, $utf8)
}

function Invoke-GhJson($endpoint, $bodyObj, [string]$method = 'POST') {
  $tmp = [System.IO.Path]::GetTempFileName()
  Write-JsonFile $tmp $bodyObj
  try {
    if ($method -eq 'POST') {
      return gh api $endpoint --method POST --input $tmp
    }
    return gh api $endpoint -X PATCH --input $tmp
  } finally {
    Remove-Item $tmp -ErrorAction SilentlyContinue
  }
}

$parentSha = gh api "repos/$owner/$repo/git/ref/heads/main" -q .object.sha
$parentCommit = gh api "repos/$owner/$repo/git/commits/$parentSha" | ConvertFrom-Json
$baseTree = $parentCommit.tree.sha

function New-GhBlob([string]$Path) {
  $full = (Resolve-Path $Path).Path
  $bytes = [System.IO.File]::ReadAllBytes($full)
  $b64 = [Convert]::ToBase64String($bytes)
  $resp = Invoke-GhJson "repos/$owner/$repo/git/blobs" @{ content = $b64; encoding = 'base64' }
  return ($resp | ConvertFrom-Json).sha
}

$paths = @(
  'FILES_FOR_GPT.md',
  'REPO_FOR_GPT.md',
  'editor/silkworm-tracer.html'
)
if ($args.Count -gt 1) {
  $paths = $args[1..($args.Count - 1)]
}

$tree = @()
foreach ($p in $paths) {
  $sha = New-GhBlob $p
  $tree += @{ path = $p; mode = '100644'; type = 'blob'; sha = $sha }
}

$treeResp = Invoke-GhJson "repos/$owner/$repo/git/trees" @{
  base_tree = $baseTree
  tree      = $tree
}
$treeSha = ($treeResp | ConvertFrom-Json).sha

$commitResp = Invoke-GhJson "repos/$owner/$repo/git/commits" @{
  message = $message
  tree    = $treeSha
  parents = @($parentSha)
}
$newSha = ($commitResp | ConvertFrom-Json).sha

Invoke-GhJson "repos/$owner/$repo/git/refs/heads/main" @{ sha = $newSha; force = $false } 'PATCH' | Out-Null
Write-Host "OK: $newSha"
