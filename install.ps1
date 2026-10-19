<#
.SYNOPSIS
  Install generated SANA OS files (SOUL.md + skills) into Hermes profiles.

.DESCRIPTION
  Copies dist\mode-<Mode>\profiles\<Profile>\ into <HermesHome>\profiles\<Profile>\.
  Files are copied byte-for-byte (UTF-8 without BOM, as built).

  1. Preflight, before anything is changed: the build output, MANIFEST.json and every
     requested profile (source files and Hermes profile folder) must exist, and each
     SOUL.md must match the hash in MANIFEST.json. If anything is missing, nothing is
     installed.
  2. For each profile: the new files are copied into a staging folder inside the profile
     and verified; the existing SOUL.md and skills\sana-os are moved to
     <profile>\sana-os-backups\<timestamp>\; the staged files are moved into place.
     If any step fails, the profile is restored to what it was.
  config.yaml, memories, sessions and other skills are not touched.
  config.yaml is read, not changed: if context_file_max_chars is missing or
  below the SOUL.md length, the profile is reported as NOT READY.

  Exit code:
    0  installed (or, with -WhatIf, would install) and ready
    2  installed, but at least one profile is NOT READY (see the warnings)
    1  preflight failed or an installation failed; failed profiles were restored

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
$distMode = Join-Path $PSScriptRoot "dist\mode-$Mode"
$distRoot = Join-Path $distMode 'profiles'
# Test hook: set SANA_INSTALL_TEST_FAIL to 'after-backup' or 'after-soul' to make the
# installation of every profile fail at that point, so the restore can be tested.
$testFail = $env:SANA_INSTALL_TEST_FAIL

function Get-Sha256([string] $path) {
    (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
}

# ---- 1. Preflight: nothing is changed until every requested profile can be installed.
$errors = @()
$manifest = $null
$manifestPath = Join-Path $distMode 'MANIFEST.json'
if (-not (Test-Path -LiteralPath $manifestPath)) {
    $errors += "Build output not found: $manifestPath  (run: python build.py --mode $Mode)"
} else {
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($manifest.mode -ne $Mode) { $errors += "$manifestPath is for mode '$($manifest.mode)', not '$Mode'" }
    foreach ($p in $Name) {
        $src = Join-Path $distRoot $p
        $dst = Join-Path $HermesHome "profiles\$p"
        $entry = $manifest.profiles.$p
        if ($null -eq $entry) { $errors += "${p}: not in $manifestPath"; continue }
        if (-not (Test-Path -LiteralPath (Join-Path $src 'SOUL.md'))) { $errors += "${p}: $src\SOUL.md not found"; continue }
        if (-not (Test-Path -LiteralPath (Join-Path $src 'skills\sana-os'))) { $errors += "${p}: $src\skills\sana-os not found"; continue }
        if ((Get-Sha256 (Join-Path $src 'SOUL.md')) -ne $entry.soul_sha256) {
            $errors += "${p}: $src\SOUL.md does not match MANIFEST.json (rebuild, or check out dist/ again)"
        }
        if (-not (Test-Path -LiteralPath $dst)) {
            $errors += "${p}: Hermes profile folder not found: $dst  (create it first: hermes profile create $p)"
        }
    }
}
if ($errors.Count -gt 0) {
    Write-Host 'Preflight failed. Nothing was changed.'
    foreach ($e in $errors) { Write-Warning $e }
    exit 1
}

# ---- 2. Install each profile, restoring it if any step fails.
function Remove-EmptyBackup([string] $backup) {
    # A backup folder with nothing in it (first install, or a restore) is not kept.
    foreach ($d in @($backup, (Split-Path -Parent $backup))) {
        if ((Test-Path -LiteralPath $d) -and -not (Get-ChildItem -LiteralPath $d -Force)) {
            Remove-Item -LiteralPath $d -Force
        }
    }
}

function Install-SanaProfile([string] $p) {
    $src = Join-Path $distRoot $p
    $dst = Join-Path $HermesHome "profiles\$p"
    $soulDst = Join-Path $dst 'SOUL.md'
    $skillsDst = Join-Path $dst 'skills\sana-os'
    $backup = Join-Path $dst "sana-os-backups\$stamp"
    $stage = Join-Path $dst ".sana-os-staging-$stamp"
    $done = @{ soulMoved = $false; skillsMoved = $false; soulPlaced = $false; skillsPlaced = $false }

    try {
        # Stage and verify the new files inside the profile folder (same volume, so the
        # moves below are renames).
        New-Item -ItemType Directory -Force -Path $stage | Out-Null
        Copy-Item -LiteralPath (Join-Path $src 'SOUL.md') -Destination (Join-Path $stage 'SOUL.md')
        Copy-Item -LiteralPath (Join-Path $src 'skills\sana-os') -Destination (Join-Path $stage 'skills-sana-os') -Recurse
        if ((Get-Sha256 (Join-Path $stage 'SOUL.md')) -ne $manifest.profiles.$p.soul_sha256) {
            throw 'the staged SOUL.md does not match MANIFEST.json'
        }
        $want = @(Get-ChildItem -LiteralPath (Join-Path $src 'skills\sana-os') -Recurse -File).Count
        $got = @(Get-ChildItem -LiteralPath (Join-Path $stage 'skills-sana-os') -Recurse -File).Count
        if ($want -ne $got) { throw "staged $got skill files, expected $want" }

        # Move the current files to the backup folder.
        New-Item -ItemType Directory -Force -Path $backup | Out-Null
        if (Test-Path -LiteralPath $soulDst) {
            Move-Item -LiteralPath $soulDst -Destination (Join-Path $backup 'SOUL.md'); $done.soulMoved = $true
        }
        if (Test-Path -LiteralPath $skillsDst) {
            Move-Item -LiteralPath $skillsDst -Destination (Join-Path $backup 'skills-sana-os'); $done.skillsMoved = $true
        }
        if ($testFail -eq 'after-backup') { throw 'test failure after backup' }

        # Put the staged files in place.
        Move-Item -LiteralPath (Join-Path $stage 'SOUL.md') -Destination $soulDst; $done.soulPlaced = $true
        if ($testFail -eq 'after-soul') { throw 'test failure after SOUL.md was placed' }
        New-Item -ItemType Directory -Force -Path (Join-Path $dst 'skills') | Out-Null
        Move-Item -LiteralPath (Join-Path $stage 'skills-sana-os') -Destination $skillsDst; $done.skillsPlaced = $true
        Remove-Item -LiteralPath $stage -Recurse -Force
        Remove-EmptyBackup $backup
        return $true
    } catch {
        Write-Warning "${p}: installation failed: $($_.Exception.Message). Restoring the previous files."
        try {
            if ($done.skillsPlaced) { Remove-Item -LiteralPath $skillsDst -Recurse -Force }
            if ($done.soulPlaced) { Remove-Item -LiteralPath $soulDst -Force }
            if ($done.skillsMoved) { Move-Item -LiteralPath (Join-Path $backup 'skills-sana-os') -Destination $skillsDst }
            if ($done.soulMoved) { Move-Item -LiteralPath (Join-Path $backup 'SOUL.md') -Destination $soulDst }
            Remove-EmptyBackup $backup
            if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
            Write-Warning "${p}: restored."
        } catch {
            Write-Warning "${p}: RESTORE FAILED: $($_.Exception.Message). The previous files are in $backup"
        }
        return $false
    }
}

$failed = @()
$notReady = @()
foreach ($p in $Name) {
    $src = Join-Path $distRoot $p
    $dst = Join-Path $HermesHome "profiles\$p"
    Write-Host "== $p  ($Mode)"

    if ($PSCmdlet.ShouldProcess($dst, 'Install SOUL.md and skills\sana-os (moving the current ones to sana-os-backups)')) {
        if (-not (Install-SanaProfile $p)) { $failed += $p; continue }
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
if ($failed.Count -gt 0) {
    Write-Warning "Failed and restored: $($failed -join ', ')."
    exit 1
}
if ($notReady.Count -gt 0) {
    Write-Warning "Installed, but not ready: $($notReady -join ', '). Fix config.yaml as above, then start a new session."
    exit 2
}
Write-Host 'Done. Start a NEW Hermes session for SOUL.md changes to take effect; run /context there and check that SOUL.md is loaded, not truncated.'
exit 0
