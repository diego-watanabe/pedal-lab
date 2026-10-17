<#
.SYNOPSIS
    Sets up the current PowerShell session for 64-bit C++ builds with Visual Studio.

.DESCRIPTION
    Puts cl, CMake and Ninja from Visual Studio on PATH, targeting x64. Run it
    "dot-sourced" (with a leading dot) so the changes stay in your terminal:

        . .\scripts\dev-shell.ps1
        cmake --build --preset dev

    Same effect as opening "x64 Native Tools Command Prompt for VS 2022", but in
    PowerShell and in the repo folder.
#>
# Runs in its own scope so dot-sourcing doesn't leave variables or settings behind;
# the environment changes (PATH and friends) are process-wide and do stay.
& {
    $ErrorActionPreference = 'Stop'

    $vswhere = Join-Path ${env:ProgramFiles(x86)} 'Microsoft Visual Studio\Installer\vswhere.exe'
    if (-not (Test-Path $vswhere)) { throw 'Visual Studio is not installed. Run scripts\setup-windows.ps1 first.' }
    $vsPath = & $vswhere -latest -products * -requires Microsoft.VisualStudio.Component.VC.Tools.x86.x64 -property installationPath
    if (-not $vsPath) { throw 'Visual Studio is installed without the C++ tools. Add "Desktop development with C++" in Visual Studio Installer.' }
    $vsPath = $vsPath.Trim()

    $here = Get-Location
    Import-Module (Join-Path $vsPath 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $vsPath -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64' | Out-Null
    Set-Location $here

    # clang-format and clang-tidy, if the Clang component is installed
    $llvmBin = Join-Path $vsPath 'VC\Tools\Llvm\x64\bin'
    if ((Test-Path $llvmBin) -and ($env:Path -notlike "*$llvmBin*")) { $env:Path = "$env:Path;$llvmBin" }

    Write-Host "Visual Studio x64 build environment ready ($vsPath)" -ForegroundColor Green
}
