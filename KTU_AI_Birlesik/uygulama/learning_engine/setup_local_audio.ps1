$ErrorActionPreference = 'Stop'
$ttsRoot = $PSScriptRoot
$ttsPython = Join-Path $ttsRoot '.venv-tts/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $ttsPython)) {
    python -m venv (Join-Path $ttsRoot '.venv-tts')
    if ($LASTEXITCODE -ne 0) { throw 'Python ortami olusturulamadi.' }
}
& $ttsPython -m pip install 'piper-tts==1.8.0'
if ($LASTEXITCODE -ne 0) { throw 'Piper kurulumu basarisiz.' }
& $ttsPython -m piper.download_voices --download-dir (Join-Path $ttsRoot 'local_models') tr_TR-dfki-medium
if ($LASTEXITCODE -ne 0) { throw 'Turkce model indirilemedi.' }
& $ttsPython (Join-Path $ttsRoot 'download_local_voice.py')
if ($LASTEXITCODE -ne 0) { throw 'Yeni Turkce ses modeli indirilemedi.' }
$femalePython = Join-Path $ttsRoot '.venv-female/Scripts/python.exe'
if (-not (Test-Path -LiteralPath $femalePython)) {
    python -m venv (Join-Path $ttsRoot '.venv-female')
    if ($LASTEXITCODE -ne 0) { throw 'Kadin sesi ortami olusturulamadi.' }
}
& $femalePython -m pip install 'onnxruntime-directml==1.24.4' numpy
if ($LASTEXITCODE -ne 0) { throw 'Kadin sesi motoru kurulamadi.' }
Write-Output 'Yerel Turkce ses hazir. Uygulamayi yeniden acabilirsin.'
