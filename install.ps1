<#
.SYNOPSIS
  Install generated SANA OS files (SOUL.md + skills) into Hermes profiles.

.DESCRIPTION
  Copies dist\mode-<Mode>\profiles\<Profile>\ into <HermesHome>\profiles\<Profile>\.
  Files are copied byte-for-byte (UTF-8 without BOM, as built).
  An existing SOUL.md and skills\sana-os folder are first moved to
  <profile>\sana-os-backups\<timestamp>\ so nothing is lost.
  config.yaml, memories, sessions and other skills are not touched.
  config.yaml is read, not changed: if context_file_max_chars is missing or
  below the SOUL.md length, the profile is reported as not ready.

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
    throw "Build output not found: $distRoot  (run: python build.py --mode $Mode)"
}
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot "dist\mode-$Mode\MANIFEST.json") -Raw -Encoding UTF8 | ConvertFrom-Json
$notReady = @()

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

    # Character count as Hermes counts it (Python len), recorded by build.py.
    # PowerShell's .Length counts UTF-16 units and can differ.
    $chars = [int]$manifest.profiles.$p.soul_chars
    Write-Host "   SOUL.md: $chars chars. Skills: $((Get-ChildItem -LiteralPath (Join-Path $src 'skills\sana-os') -Directory).Name -join ', ')"

    # Read-only check of config.yaml. This script never edits it.
    # It checks only Hermes' cap on context files. Whether the whole prompt fits
    # the model's context window is a separate check (/context in a session).
    $cfgPath = Join-Path $dst 'config.yaml'
    $cap = $null
    if (Test-Path -LiteralPath $cfgPath) {
        $m = [regex]::Match((Get-Content -LiteralPath $cfgPath -Raw -Encoding UTF8),
                            '(?m)^context_file_max_chars:[ \t]*(\d+)[ \t]*(#.*)?\r?$')
        if ($m.Success) { $cap = [int]$m.Groups[1].Value }
    }
    if ($null -eq $cap) {
        if ($chars -gt 20000) {
            Write-Warning "NOT READY: context_file_max_chars is not pinned in $cfgPath."
            Write-Warning "  Hermes then caps SOUL.md by the model's context length, and at 20,000 chars when that is unknown; the middle would be cut. See README."
            $notReady += $p
        }
    } elseif ($cap -lt $chars) {
        Write-Warning "NOT READY: context_file_max_chars is $cap, below the $chars chars of SOUL.md; the middle would be cut."
        $notReady += $p
    } else {
        Write-Host "   context_file_max_chars: $cap (>= $chars). Check /context in a new session as well."
    }
}

Write-Host ''
if ($notReady.Count -gt 0) {
    Write-Warning "Installed, but not ready: $($notReady -join ', '). Fix config.yaml as above, then start a new session."
}
Write-Host 'Done. Start a NEW Hermes session for SOUL.md changes to take effect; run /context there and check that SOUL.md is loaded, not truncated.'
