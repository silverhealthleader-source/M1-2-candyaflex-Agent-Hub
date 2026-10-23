$ErrorActionPreference = 'Stop'
$projectDirectory = Split-Path -Parent $PSScriptRoot
$javaExecutable = Get-ChildItem -LiteralPath (Join-Path $projectDirectory '.local/tools') -Recurse -Filter 'java.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
if ($javaExecutable) {
    $env:JAVA_HOME = Split-Path -Parent (Split-Path -Parent $javaExecutable.FullName)
    $env:PATH = (Join-Path $env:JAVA_HOME 'bin') + [IO.Path]::PathSeparator + $env:PATH
}
$env:FIREBASE_CLI_DISABLE_UPDATE_CHECK = 'true'
Set-Location -LiteralPath $projectDirectory
$exportPath = Join-Path $projectDirectory '.local/firebase-export'
if (Test-Path -LiteralPath (Join-Path $exportPath 'firebase-export-metadata.json')) {
    firebase.cmd emulators:start --only firestore --project demo-candy-a-academy --import $exportPath --export-on-exit $exportPath
} else {
    firebase.cmd emulators:start --only firestore --project demo-candy-a-academy --export-on-exit $exportPath
}
