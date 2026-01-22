#Requires -Version 5.1
<#
.SYNOPSIS
    Collectra GUI Installer for Windows

.DESCRIPTION
    Downloads and installs the Collectra GUI application.

.EXAMPLE
    # Run directly from GitHub:
    irm https://raw.githubusercontent.com/jamestq/collectra_gui/main/install.ps1 | iex

    # Or download and run:
    .\install.ps1

    # Install specific version:
    $env:COLLECTRA_VERSION = "v0.1.0"; .\install.ps1

    # Install to custom directory:
    $env:COLLECTRA_INSTALL_DIR = "C:\Tools"; .\install.ps1

.PARAMETER Action
    The action to perform: install (default) or uninstall

.NOTES
    Author: James Q
    Repository: https://github.com/jamestq/collectra_gui
#>

param(
    [ValidateSet("install", "uninstall")]
    [string]$Action = "install"
)

$ErrorActionPreference = "Stop"

$Repo = "jamestq/collectra_gui"
$BinaryName = "collectra_gui.exe"
$DefaultInstallDir = Join-Path $env:LOCALAPPDATA "collectra_gui"
$InstallDir = if ($env:COLLECTRA_INSTALL_DIR) { $env:COLLECTRA_INSTALL_DIR } else { $DefaultInstallDir }

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] " -ForegroundColor Green -NoNewline
    Write-Host $Message
}

function Write-Warn {
    param([string]$Message)
    Write-Host "[WARN] " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERROR] " -ForegroundColor Red -NoNewline
    Write-Host $Message
    exit 1
}

function Get-LatestVersion {
    try {
        $response = Invoke-RestMethod -Uri "https://api.github.com/repos/$Repo/releases/latest" -UseBasicParsing
        return $response.tag_name
    }
    catch {
        return $null
    }
}

function Install-CollectraGui {
    Write-Info "Installing Collectra GUI for Windows..."

    # Determine version
    $version = if ($env:COLLECTRA_VERSION) { $env:COLLECTRA_VERSION } else { Get-LatestVersion }
    if (-not $version) {
        Write-Err "Could not determine latest version. Set `$env:COLLECTRA_VERSION manually."
    }
    Write-Info "Installing version: $version"

    # Construct download URL
    $downloadUrl = "https://github.com/$Repo/releases/download/$version/collectra_gui-windows-x86_64.exe"
    Write-Info "Downloading from: $downloadUrl"

    # Create install directory
    if (-not (Test-Path $InstallDir)) {
        New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    }

    $targetPath = Join-Path $InstallDir $BinaryName

    # Download binary
    try {
        $ProgressPreference = 'SilentlyContinue'
        Invoke-WebRequest -Uri $downloadUrl -OutFile $targetPath -UseBasicParsing
    }
    catch {
        Write-Err "Failed to download binary: $_"
    }

    Write-Info "Installed to: $targetPath"

    # Add to PATH if not already there
    $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($currentPath -notlike "*$InstallDir*") {
        Write-Info "Adding $InstallDir to user PATH..."
        $newPath = "$currentPath;$InstallDir"
        [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
        $env:Path = "$env:Path;$InstallDir"
        Write-Info "Added to PATH. You may need to restart your terminal."
    }

    Write-Host ""
    Write-Info "Installation complete!"
    Write-Host ""
    Write-Host "Run 'collectra_gui start' to launch the application."
    Write-Host ""
    Write-Host "Note: You may need to restart your terminal or run:" -ForegroundColor Cyan
    Write-Host "  `$env:Path = [Environment]::GetEnvironmentVariable('Path', 'User')" -ForegroundColor Cyan
}

function Uninstall-CollectraGui {
    $targetPath = Join-Path $InstallDir $BinaryName

    if (Test-Path $targetPath) {
        Remove-Item $targetPath -Force
        Write-Info "Uninstalled $BinaryName from $InstallDir"

        # Optionally remove from PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
        if ($currentPath -like "*$InstallDir*") {
            $newPath = ($currentPath -split ";" | Where-Object { $_ -ne $InstallDir }) -join ";"
            [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
            Write-Info "Removed $InstallDir from PATH"
        }

        # Remove directory if empty
        if ((Get-ChildItem $InstallDir -Force | Measure-Object).Count -eq 0) {
            Remove-Item $InstallDir -Force
            Write-Info "Removed empty directory: $InstallDir"
        }
    }
    else {
        Write-Warn "$BinaryName is not installed in $InstallDir"
    }
}

# Main
switch ($Action) {
    "install"   { Install-CollectraGui }
    "uninstall" { Uninstall-CollectraGui }
}
