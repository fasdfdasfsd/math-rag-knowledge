#!/bin/bash
# ============================================================
# Claude Code 四层配置 — Ubuntu 一键部署脚本
# 版本: v4.1 | 日期: 2026-05-30
# 用法: chmod +x install.sh && ./install.sh
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "============================================"
echo " Claude Code 四层配置部署 v4.1"
echo "============================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
CLAUDE_HOME="$HOME/.claude"
MEMORY_DIR="$CLAUDE_HOME/projects/D--panzt-projects-claude-code-python-rag/memory"

# ---- 前置检查 ----
echo -e "${YELLOW}[检查]${NC} 前置条件..."
command -v git >/dev/null 2>&1 || { echo -e "${RED}❌ git 未安装${NC}"; exit 1; }
[ -d "$PROJECT_DIR/config" ] || { echo -e "${RED}❌ config/ 目录不存在，请在项目根目录运行${NC}"; exit 1; }
echo -e "${GREEN}✅ 前置条件通过${NC}"
echo ""

# ---- Step 1: L1 用户全局 ----
echo -e "${YELLOW}[Step 1/4]${NC} L1 用户全局配置..."
mkdir -p "$CLAUDE_HOME"

# CLAUDE.md
cp "$PROJECT_DIR/config/L1-用户全局/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"
echo "  ✅ ~/.claude/CLAUDE.md"

# settings.json（不覆盖用户已有的 API key）
if [ -f "$CLAUDE_HOME/settings.json" ]; then
    echo "  ⚠️ ~/.claude/settings.json 已存在，跳过（手动合并 config/L1-用户全局/settings.json）"
else
    cp "$PROJECT_DIR/config/L1-用户全局/settings.json" "$CLAUDE_HOME/settings.json"
    echo "  ✅ ~/.claude/settings.json（请编辑填入 API 密钥）"
fi

# knowledge/
if [ -d "$CLAUDE_HOME/knowledge" ]; then
    echo "  ⚠️ ~/.claude/knowledge/ 已存在，跳过"
else
    cp -r "$PROJECT_DIR/knowledge" "$CLAUDE_HOME/knowledge"
    echo "  ✅ ~/.claude/knowledge/"
fi
echo ""

# ---- Step 2: L2 项目共享 ----
echo -e "${YELLOW}[Step 2/4]${NC} L2 项目共享配置..."

# CLAUDE.md
cp "$PROJECT_DIR/config/L2-项目共享/CLAUDE.md" "$PROJECT_DIR/CLAUDE.md"
echo "  ✅ ./CLAUDE.md"

# .claude/ 目录
mkdir -p "$PROJECT_DIR/.claude" "$PROJECT_DIR/.claude/rules"

cp "$PROJECT_DIR/config/L2-项目共享/settings.json" "$PROJECT_DIR/.claude/settings.json"
echo "  ✅ ./.claude/settings.json"

cp "$PROJECT_DIR/config/L2-项目共享/primer.md" "$PROJECT_DIR/.claude/primer.md"
echo "  ✅ ./.claude/primer.md"

cp "$PROJECT_DIR/config/L2-项目共享/activeContext.md" "$PROJECT_DIR/.claude/activeContext.md"
echo "  ✅ ./.claude/activeContext.md"

cp "$PROJECT_DIR/config/L2-项目共享/MEMORY.md" "$PROJECT_DIR/.claude/MEMORY.md"
echo "  ✅ ./.claude/MEMORY.md"

# .claudeignore
if [ -f "$PROJECT_DIR/.claudeignore" ]; then
    echo "  ✅ ./.claudeignore（已存在）"
else
    cp "$PROJECT_DIR/config/L2-项目共享/.claudeignore" "$PROJECT_DIR/.claudeignore"
    echo "  ✅ ./.claudeignore（从模板创建）"
fi

# .claude/rules/（已在项目中，验证）
if [ -d "$PROJECT_DIR/.claude/rules" ] && [ "$(ls -1 "$PROJECT_DIR/.claude/rules"/*.md 2>/dev/null | wc -l)" -ge 5 ]; then
    echo "  ✅ .claude/rules/ ($(ls -1 "$PROJECT_DIR/.claude/rules"/*.md | wc -l) 个文件)"
else
    echo "  ⚠️ .claude/rules/ 不完整"
fi
echo ""

# ---- Step 3: L3 项目本地 ----
echo -e "${YELLOW}[Step 3/4]${NC} L3 项目本地配置..."

# settings.local.json（不覆盖已有）
if [ -f "$PROJECT_DIR/.claude/settings.local.json" ]; then
    echo "  ⚠️ .claude/settings.local.json 已存在，跳过"
else
    cp "$PROJECT_DIR/config/L3-项目本地/settings.local.json" "$PROJECT_DIR/.claude/settings.local.json"
    echo "  ✅ .claude/settings.local.json（请编辑填入个人 API 密钥）"
fi

# CLAUDE.local.md
if [ -f "$PROJECT_DIR/CLAUDE.local.md" ]; then
    echo "  ⚠️ CLAUDE.local.md 已存在，跳过"
else
    cp "$PROJECT_DIR/config/L3-项目本地/CLAUDE.local.md" "$PROJECT_DIR/CLAUDE.local.md"
    echo "  ✅ CLAUDE.local.md"
fi
echo ""

# ---- Step 4: 全局记忆目录 ----
echo -e "${YELLOW}[Step 4/4]${NC} 全局记忆目录..."
mkdir -p "$MEMORY_DIR"
if [ -f "$MEMORY_DIR/MEMORY.md" ]; then
    echo "  ⚠️ 全局 MEMORY.md 已存在"
else
    cat > "$MEMORY_DIR/MEMORY.md" << 'EOF'
# 项目记忆索引

> python-rag 项目记忆目录
> 每个记忆一个 .md 文件，本文件为索引

## 记忆列表

（暂无记忆条目，重要决策后自动添加）
EOF
    echo "  ✅ 全局 MEMORY.md 已创建"
fi
echo ""

# ---- 验证 ----
echo "============================================"
echo -e "${GREEN}✅ 部署完成！${NC}"
echo "============================================"
echo ""
echo "下一步："
echo "  1. 编辑 ~/.claude/settings.json 填入 API 密钥"
echo "  2. 编辑 .claude/settings.local.json 填入个人 API 密钥"
echo "  3. 重启 Claude Code 验证"
echo ""
echo "验证项："
echo "  - SessionStart 应输出记忆文件 ✅/❌"
echo "  - 尝试 rm -rf /tmp/test 应被阻止"
echo "  - @knowledge/README.md 应可引用"
echo ""
