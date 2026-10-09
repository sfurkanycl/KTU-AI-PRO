$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
py -3.12 -m venv .venv
if ($LASTEXITCODE -ne 0) { throw 'Python 3.12 kurulumu gerekiyor.' }
& '.\.venv\Scripts\python.exe' -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Paket kurulumu tamamlanamadi.' }
Write-Output 'Kurulum tamamlandi. Kendi anahtarlarinizi .env.example ornegine gore .env dosyasina girin.'
