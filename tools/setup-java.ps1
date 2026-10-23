$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$toolDirectory = Join-Path $projectDirectory '.local/tools'
New-Item -ItemType Directory -Path $toolDirectory -Force | Out-Null
$existingJava = Get-ChildItem -LiteralPath $toolDirectory -Recurse -Filter 'java.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($existingJava) {
    Write-Output $existingJava.FullName
    exit 0
}
$releases = Invoke-RestMethod -Uri 'https://api.adoptium.net/v3/assets/latest/21/hotspot?architecture=x64&image_type=jre&os=windows&vendor=eclipse'
$package = $releases[0].binary.package
if (-not $package.link.StartsWith('https://github.com/adoptium/')) {
    throw 'Expected an official Eclipse Adoptium release URL.'
}
$archivePath = Join-Path $toolDirectory 'temurin21-jre.zip'
Invoke-WebRequest -Uri $package.link -OutFile $archivePath
$actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualHash -ne $package.checksum.ToLowerInvariant()) {
    throw 'The Java runtime checksum does not match the official release.'
}
Expand-Archive -LiteralPath $archivePath -DestinationPath (Join-Path $toolDirectory 'java') -Force
Get-ChildItem -LiteralPath (Join-Path $toolDirectory 'java') -Recurse -Filter 'java.exe' | Select-Object -ExpandProperty FullName
