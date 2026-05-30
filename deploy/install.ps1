# ============================================================
# Claude Code 4-Layer Config Deployment v4.1
# Windows 11 One-Click Install
# Usage: .\deploy\install.ps1
# Note: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned may be needed
# ============================================================

$ErrorActionPreference = "Stop"

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Claude Code 4-Layer Config Deploy v4.1" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$ClaudeHome = "$env:USERPROFILE\.claude"
$MemoryDir = "$ClaudeHome\projects\D--panzt-projects-claude-code-python-rag\memory"

# ---- Pre-check ----
Write-Host "[Check] Prerequisites..." -ForegroundColor Yellow
try { git --version | Out-Null } catch { Write-Host "[FAIL] git not installed" -ForegroundColor Red; exit 1 }
if (-not (Test-Path "$ProjectDir\config")) {
    Write-Host "[FAIL] config/ not found. Run from project root." -ForegroundColor Red
    exit 1
}
Write-Host "[OK] Prerequisites passed" -ForegroundColor Green
Write-Host ""

# ---- Step 1: L1 User Global ----
Write-Host "[Step 1/4] L1 User Global Config..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $ClaudeHome | Out-Null

# CLAUDE.md
Copy-Item -Path "$ProjectDir\config\L1-用户全局\CLAUDE.md" -Destination "$ClaudeHome\CLAUDE.md" -Force
Write-Host "  [OK] ~/.claude/CLAUDE.md"

# settings.json (don't overwrite user's existing API key)
if (Test-Path "$ClaudeHome\settings.json") {
    Write-Host "  [SKIP] ~/.claude/settings.json exists, merge manually from config/L1"
} else {
    Copy-Item -Path "$ProjectDir\config\L1-用户全局\settings.json" -Destination "$ClaudeHome\settings.json"
    Write-Host "  [OK] ~/.claude/settings.json (edit to add API key)"
}

# knowledge/ (don't overwrite if exists)
if (Test-Path "$ClaudeHome\knowledge") {
    Write-Host "  [SKIP] ~/.claude/knowledge/ exists"
} else {
    Copy-Item -Path "$ProjectDir\knowledge" -Destination "$ClaudeHome\knowledge" -Recurse
    Write-Host "  [OK] ~/.claude/knowledge/"
}
Write-Host ""

# ---- Step 2: L2 Project Shared ----
Write-Host "[Step 2/4] L2 Project Shared Config..." -ForegroundColor Yellow

# CLAUDE.md
Copy-Item -Path "$ProjectDir\config\L2-项目共享\CLAUDE.md" -Destination "$ProjectDir\CLAUDE.md" -Force
Write-Host "  [OK] ./CLAUDE.md"

# .claude/ dirs
New-Item -ItemType Directory -Force -Path "$ProjectDir\.claude" | Out-Null
New-Item -ItemType Directory -Force -Path "$ProjectDir\.claude\rules" | Out-Null

Copy-Item -Path "$ProjectDir\config\L2-项目共享\settings.json" -Destination "$ProjectDir\.claude\settings.json" -Force
Write-Host "  [OK] ./.claude/settings.json"

Copy-Item -Path "$ProjectDir\config\L2-项目共享\primer.md" -Destination "$ProjectDir\.claude\primer.md" -Force
Write-Host "  [OK] ./.claude/primer.md"

Copy-Item -Path "$ProjectDir\config\L2-项目共享\activeContext.md" -Destination "$ProjectDir\.claude\activeContext.md" -Force
Write-Host "  [OK] ./.claude/activeContext.md"

Copy-Item -Path "$ProjectDir\config\L2-项目共享\MEMORY.md" -Destination "$ProjectDir\.claude\MEMORY.md" -Force
Write-Host "  [OK] ./.claude/MEMORY.md"

# .claudeignore
if (Test-Path "$ProjectDir\.claudeignore") {
    Write-Host "  [OK] ./.claudeignore (exists)"
} else {
    Copy-Item -Path "$ProjectDir\config\L2-项目共享\.claudeignore" -Destination "$ProjectDir\.claudeignore"
    Write-Host "  [OK] ./.claudeignore (created from template)"
}

# .claude/rules/ count check
$ruleCount = @(Get-ChildItem -Path "$ProjectDir\.claude\rules\*.md" -ErrorAction SilentlyContinue).Count
if ($ruleCount -ge 5) {
    Write-Host "  [OK] .claude/rules/ ($ruleCount files)"
} else {
    Write-Host "  [WARN] .claude/rules/ incomplete ($ruleCount files)"
}
Write-Host ""

# ---- Step 3: L3 Project Local ----
Write-Host "[Step 3/4] L3 Project Local Config..." -ForegroundColor Yellow

# settings.local.json
if (Test-Path "$ProjectDir\.claude\settings.local.json") {
    Write-Host "  [SKIP] .claude/settings.local.json exists"
} else {
    Copy-Item -Path "$ProjectDir\config\L3-项目本地\settings.local.json" -Destination "$ProjectDir\.claude\settings.local.json"
    Write-Host "  [OK] .claude/settings.local.json (edit to add personal API key)"
}

# CLAUDE.local.md
if (Test-Path "$ProjectDir\CLAUDE.local.md") {
    Write-Host "  [SKIP] CLAUDE.local.md exists"
} else {
    Copy-Item -Path "$ProjectDir\config\L3-项目本地\CLAUDE.local.md" -Destination "$ProjectDir\CLAUDE.local.md"
    Write-Host "  [OK] CLAUDE.local.md"
}
Write-Host ""

# ---- Step 4: Global Memory Dir ----
Write-Host "[Step 4/4] Global Memory Directory..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $MemoryDir | Out-Null
if (Test-Path "$MemoryDir\MEMORY.md") {
    Write-Host "  [SKIP] Global MEMORY.md exists"
} else {
    $memoryContent = @"
# Project Memory Index

> python-rag project memory directory
> One .md file per memory, this file is the index

## Memory List

(No entries yet. Added automatically after important decisions.)
"@
    $memoryContent | Out-File -FilePath "$MemoryDir\MEMORY.md" -Encoding UTF8
    Write-Host "  [OK] Global MEMORY.md created"
}
Write-Host ""

# ---- Done ----
Write-Host "============================================" -ForegroundColor Green
Write-Host "[DONE] Deployment Complete!" -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:"
Write-Host "  1. Edit ~/.claude/settings.json -> add API key"
Write-Host "  2. Edit .claude/settings.local.json -> add personal API key"
Write-Host "  3. Restart Claude Code to verify"
Write-Host ""
Write-Host "Verify:"
Write-Host "  - SessionStart shows memory file status"
Write-Host "  - 'rm -rf /tmp/test' is blocked"
Write-Host "  - '@knowledge/README.md' is accessible"
Write-Host ""
