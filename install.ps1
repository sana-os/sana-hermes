<#
.SYNOPSIS
  Install generated SANA OS files (SOUL.md + skills) into Hermes profiles.

.DESCRIPTION
  Copies dist\mode-<Mode>\profiles\<Profile>\ into <HermesHome>\profiles\<Profile>\.
  Files are copied byte-for-byte (UTF-8 without BOM, as built).
  An existing SOUL.md and skills\sana-os folder are first moved to
  <profile>\sana-os-backups\<timestamp>\ so nothing is lost.
  config.yaml, memories, sessions and other skills are not touched.

.EXAMPLE
  .\install.ps1 -Name sana-hub -WhatIf
  .\install.ps1 -Name sana-hub
  .\install.ps1 -Name sana-history,sana-coaching -Mode inline
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    # Not named $Profile: that name is PowerShell's automatic $PROFILE variable.
    [Parameter(Mandatory = $true)]
    [Alias('Profile')]
    [ValidateSet('sana-hub', 'sana-history', 'sana-coaching', 'sana-reasoning', 'sana-review', 'sana-friend')]
    [string[]] $Name,

    [ValidateSet('skills', 'inline')]
    [string] $Mode = 'skills',

    [string] $HermesHome = (Join-Path $env:LOCALAPPDATA 'hermes')
)

$ErrorActionPreference = 'Stop'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$distRoot = Join-Path $PSScriptRoot "dist\mode-$Mode\profiles"

if (-not (Test-Path -LiteralPath $distRoot)) {
    throw "Build output not found: $distRoot  (run: python build.py --sana-os <path> --mode $Mode)"
}

foreach ($p in $Name) {
    $src = Join-Path $distRoot $p
    $dst = Join-Path $HermesHome "profiles\$p"
    Write-Host "== $p  ($Mode)"

    if (-not (Test-Path -LiteralPath $dst)) {
        Write-Warning "Profile folder not found: $dst"
        Write-Warning "Create it first:  hermes profile create $p   (then run this script again)"
        continue
    }

    $backup = Join-Path $dst "sana-os-backups\$stamp"
    $soulDst = Join-Path $dst 'SOUL.md'
    $skillsDst = Join-Path $dst 'skills\sana-os'

    if (Test-Path -LiteralPath $soulDst) {
        if ($PSCmdlet.ShouldProcess($soulDst, "Back up to $backup")) {
            New-Item -ItemType Directory -Force -Path $backup | Out-Null
            Copy-Item -LiteralPath $soulDst -Destination (Join-Path $backup 'SOUL.md')
        }
    }
    if (Test-Path -LiteralPath $skillsDst) {
        if ($PSCmdlet.ShouldProcess($skillsDst, "Move to $backup\skills-sana-os")) {
            New-Item -ItemType Directory -Force -Path $backup | Out-Null
            Move-Item -LiteralPath $skillsDst -Destination (Join-Path $backup 'skills-sana-os')
        }
    }

    if ($PSCmdlet.ShouldProcess($soulDst, 'Install SOUL.md')) {
        Copy-Item -LiteralPath (Join-Path $src 'SOUL.md') -Destination $soulDst -Force
    }
    if ($PSCmdlet.ShouldProcess($skillsDst, 'Install SANA OS skills')) {
        New-Item -ItemType Directory -Force -Path (Join-Path $dst 'skills') | Out-Null
        Copy-Item -LiteralPath (Join-Path $src 'skills\sana-os') -Destination $skillsDst -Recurse -Force
    }

    $chars = (Get-Content -LiteralPath (Join-Path $src 'SOUL.md') -Raw -Encoding UTF8).Length
    Write-Host "   SOUL.md: $chars chars. Skills: $((Get-ChildItem -LiteralPath (Join-Path $src 'skills\sana-os') -Directory).Name -join ', ')"
    if ($chars -gt 20000) {
        Write-Host "   Note: over 20,000 chars. Set context_file_max_chars in this profile's config.yaml (see README)."
    }
}

Write-Host ''
Write-Host 'Done. Start a NEW Hermes session for SOUL.md changes to take effect.'
