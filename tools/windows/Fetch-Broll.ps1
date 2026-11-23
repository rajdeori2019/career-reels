# Career Reels: fetch B-roll on the laptop (ChatGPT's sandbox has no internet).
# ChatGPT (or Claude) writes <Reel>_shots.json; put it in  D:\Prafulla Goal\Career Reels\B-roll\_queue\
# then double-click Fetch-Broll.cmd. Uses your own B-roll first, then Pexels, then Pixabay (keys in broll.env,
# never printed or uploaded). Output: B-roll\<Reel>\clips\*.mp4 + picks.png + credits.txt -> upload to ChatGPT.
param([string]$Shots)
$ErrorActionPreference = 'Stop'
$root = 'D:\Prafulla Goal\Career Reels'
$editor = Join-Path $root 'tools\broll.py'
$keys = Join-Path $root 'broll.env'
foreach ($c in 'python','ffmpeg','ffprobe') { if (!(Get-Command $c -ErrorAction SilentlyContinue)) { throw "$c is missing from PATH." } }
if (!(Test-Path $keys)) { throw "broll.env not found in $root" }
if (!$Shots) {
  $q = Join-Path $root 'B-roll\_queue'; New-Item -ItemType Directory -Force -Path $q | Out-Null
  $f = Get-ChildItem $q -Filter '*shots*.json' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (!$f) { throw "No *_shots.json in $q. Save the file ChatGPT gave you there." }
  $Shots = $f.FullName
}
$name = [IO.Path]::GetFileNameWithoutExtension($Shots) -replace '_?shots$',''
$work = Join-Path $root "B-roll\$name"
New-Item -ItemType Directory -Force -Path $work | Out-Null
Copy-Item $Shots (Join-Path $work 'shots.json') -Force
$env:BROLL_KEYS = $keys
Write-Host "Shots: $Shots"; Write-Host "Work:  $work"
& python $editor search (Join-Path $work 'shots.json') $work --own (Join-Path $root 'B-roll')
if ($LASTEXITCODE -ne 0) { throw 'search failed' }
& python $editor fetch $work;   if ($LASTEXITCODE -ne 0) { throw 'fetch failed' }
& python $editor sheet $work;   if ($LASTEXITCODE -ne 0) { throw 'sheet failed' }
& python $editor credits $work
Compress-Archive -Force -Path (Join-Path $work 'clips\*'), (Join-Path $work 'picks.png'), (Join-Path $work 'credits.txt') -DestinationPath (Join-Path $work "$name`_broll.zip")
Write-Host ""; Write-Host "DONE. Upload this to ChatGPT: $work\$name`_broll.zip"
Start-Process explorer.exe $work
