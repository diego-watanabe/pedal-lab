<#
.SYNOPSIS
    One-shot Windows setup for pedal-lab.

.DESCRIPTION
    Installs what's missing and gets the project ready to build:
      1. Git for Windows                          (winget)
      2. Visual Studio 2022 Community with C++,   (winget; skipped if a Visual Studio
         CMake/Ninja and Clang tools               with the C++ tools is already installed)
      3. A conda environment "pedal-lab" with the Python requirements
      4. The git history, unpacked from pedal-lab.bundle (if present)
      5. A first C++ build and test run

    Safe to run again: each step checks whether it's already done.
    Expect a few admin prompts (installers) and a long wait on Visual Studio.

    Run from PowerShell in the repo folder:
        powershell -ExecutionPolicy Bypass -File scripts\setup-windows.ps1

.PARAMETER SkipBuild
    Don't run the C++ build at the end.

.PARAMETER WithReaper
    Also install Reaper as a test host for plugins.
#>
[CmdletBinding()]
param(
    [switch]$SkipBuild,
    [switch]$WithReaper
)

$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

function Write-Step([string]$Text) { Write-Host "`n==> $Text" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "    $Text" -ForegroundColor Green }
function Write-Note([string]$Text) { Write-Host "    $Text" -ForegroundColor Yellow }

# Runs a native command and stops the script if it fails.
function Invoke-Checked {
    param([string]$What, [scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) { throw "$What failed (exit code $LASTEXITCODE)." }
}

# Installers add to PATH in the registry; reload it so this session sees new tools.
function Update-SessionPath {
    $machine = [Environment]::GetEnvironmentVariable('Path', 'Machine')
    $user = [Environment]::GetEnvironmentVariable('Path', 'User')
    $env:Path = "$machine;$user"
}

function Test-Command([string]$Name) {
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WithWinget {
    param([string]$Id, [string]$Override)
    $wingetArgs = @('install', '--id', $Id, '--exact', '--accept-source-agreements', '--accept-package-agreements')
    if ($Override) { $wingetArgs += @('--override', $Override) }
    & winget @wingetArgs
    # winget returns a non-zero code when the package is already installed; check afterwards instead.
}

function Get-VisualStudioPath {
    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) { return $null }
    $path = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if ($path) { return $path.Trim() }
    return $null
}

function Get-CondaExe {
    $cmd = Get-Command conda -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -like '*.exe') { return $cmd.Source }
    $candidates = @(
        "$HOME\anaconda3\Scripts\conda.exe",
        "$HOME\miniconda3\Scripts\conda.exe",
        "$env:ProgramData\anaconda3\Scripts\conda.exe",
        "$env:ProgramData\miniconda3\Scripts\conda.exe",
        "$env:LOCALAPPDATA\anaconda3\Scripts\conda.exe"
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    return $null
}

Write-Host "pedal-lab Windows setup in $RepoRoot" -ForegroundColor White

# --- 0. winget -----------------------------------------------------------------
if (-not (Test-Command 'winget')) {
    throw "winget isn't available. Install 'App Installer' from the Microsoft Store, then run this again."
}

# --- 1. Git ----------------------------------------------------------------------
Write-Step 'Git for Windows'
if (Test-Command 'git') {
    Write-Ok "already installed: $(git --version)"
} else {
    Install-WithWinget -Id 'Git.Git'
    Update-SessionPath
    if (-not (Test-Command 'git')) { throw 'Git was not found after installing. Open a new terminal and run this script again.' }
    Write-Ok "installed: $(git --version)"
}

# --- 2. Visual Studio ------------------------------------------------------------
Write-Step 'Visual Studio with the C++ tools'
$vsPath = Get-VisualStudioPath
if ($vsPath) {
    Write-Ok "found: $vsPath"
} else {
    Write-Note 'Installing Visual Studio 2022 Community. This downloads several GB and can take 20+ minutes.'
    $components = @(
        '--add Microsoft.VisualStudio.Workload.NativeDesktop',
        '--add Microsoft.VisualStudio.Component.VC.CMake.Project',
        '--add Microsoft.VisualStudio.Component.VC.Llvm.Clang',
        '--includeRecommended'
    ) -join ' '
    Install-WithWinget -Id 'Microsoft.VisualStudio.2022.Community' -Override "--passive --wait --norestart $components"
    $vsPath = Get-VisualStudioPath
    if (-not $vsPath) {
        throw ('Visual Studio installed, but the C++ tools were not found. Open "Visual Studio Installer", ' +
               'choose Modify, tick "Desktop development with C++", then run this script again.')
    }
    Write-Ok "installed: $vsPath"
}
$clangFormat = Join-Path $vsPath 'VC\Tools\Llvm\x64\bin\clang-format.exe'
if (-not (Test-Path $clangFormat)) {
    Write-Note ('clang-format and clang-tidy are missing. To add them: Visual Studio Installer -> Modify -> ' +
                'Individual components -> "C++ Clang Compiler for Windows". Builds work without them.')
}

# --- 3. Python environment -------------------------------------------------------
Write-Step 'Python environment (conda, "pedal-lab")'
$conda = Get-CondaExe
if (-not $conda) {
    Write-Note 'conda not found. Installing Miniconda.'
    Install-WithWinget -Id 'Anaconda.Miniconda3'
    Update-SessionPath
    $conda = Get-CondaExe
    if (-not $conda) { throw 'conda was not found after installing Miniconda. Open a new terminal and run this script again.' }
}
Write-Ok "conda: $conda"

$envList = & $conda env list
if ($envList -match '(?m)^pedal-lab\s') {
    Write-Ok 'environment exists'
} else {
    Invoke-Checked 'Creating the conda environment' { & $conda create --name pedal-lab python=3.12 --yes }
}
Invoke-Checked 'Installing Python packages' {
    & $conda run --name pedal-lab --no-capture-output python -m pip install --quiet -r python\requirements.txt
}
Invoke-Checked 'Python tests' {
    & $conda run --name pedal-lab --no-capture-output --cwd python python -m pytest -q
}
Write-Ok 'Python packages installed and tests pass'

# --- 4. Git history --------------------------------------------------------------
Write-Step 'Git history'
if (Test-Path '.git') {
    Write-Ok 'repository already set up'
} elseif (Test-Path 'pedal-lab.bundle') {
    Invoke-Checked 'git init' { git init --initial-branch=main --quiet }
    Invoke-Checked 'Reading pedal-lab.bundle' { git fetch --quiet pedal-lab.bundle main }
    Invoke-Checked 'git reset' { git reset --quiet FETCH_HEAD }
    Invoke-Checked 'Restoring files from history' { git checkout -- . }
    Remove-Item 'pedal-lab.bundle'
    Write-Ok "history unpacked: $(git log --oneline -1)"
} else {
    Write-Note 'No .git folder and no pedal-lab.bundle: skipping.'
}
if (Test-Path '.git') {
    $gitName = git config --global user.name
    if (-not $gitName) {
        Write-Note 'Git doesn''t know who you are yet. Before your first commit, run:'
        Write-Note '  git config --global user.name "Your Name"'
        Write-Note '  git config --global user.email "you@example.com"'
    }
}

# --- 5. Optional: Reaper ---------------------------------------------------------
if ($WithReaper) {
    Write-Step 'Reaper'
    Install-WithWinget -Id 'Cockos.REAPER'
    Write-Ok 'Reaper installed (or already present)'
}

# --- 6. C++ build ----------------------------------------------------------------
if ($SkipBuild) {
    Write-Step 'C++ build skipped (-SkipBuild)'
} else {
    Write-Step 'C++ build (the first run downloads JUCE and Catch2)'
    New-Item -ItemType Directory -Force -Path "$env:LOCALAPPDATA\Programs\Common\VST3" | Out-Null
    & (Join-Path $PSScriptRoot 'dev-shell.ps1')
    Invoke-Checked 'CMake configure' { cmake --preset dev }
    Invoke-Checked 'Build' { cmake --build --preset dev }
    Invoke-Checked 'C++ tests' { ctest --preset dev }
    Write-Ok "built and tested; Lab Gain.vst3 copied to $env:LOCALAPPDATA\Programs\Common\VST3"
}

# --- Done --------------------------------------------------------------------------
Write-Host "`nSetup complete." -ForegroundColor Green
Write-Host @"

Still to do by hand:
  * Install RME's ASIO driver for the Babyface (rme-audio.de, Downloads).
  * In your DAW, add this folder to the VST3 scan paths and rescan:
      $env:LOCALAPPDATA\Programs\Common\VST3

Everyday use:
  Python:  conda activate pedal-lab   (Anaconda Prompt, or after 'conda init powershell')
           cd python;  python live.py --list-devices
  C++:     . .\scripts\dev-shell.ps1   (once per terminal), then
           cmake --build --preset dev;  ctest --preset dev
"@
