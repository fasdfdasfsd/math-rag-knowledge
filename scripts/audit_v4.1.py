#!/usr/bin/env python3
"""
v4.1 逐文件审计脚本
验证范围: L1/L2/L3/全局记忆/config/deploy 全部文件
验证深度: 存在性 → JSON有效性 → 内容完整性 → 跨文件一致性 → 安全语义
"""
import json, os, sys, hashlib
from pathlib import Path
from datetime import datetime

PROJECT = Path("D:/panzt_projects/claude-code/python-rag")
CLAUDE_HOME = Path.home() / ".claude"
MEMORY_DIR = CLAUDE_HOME / "projects/D--panzt-projects-claude-code-python-rag/memory"

results = {"pass": 0, "fail": 0, "warn": 0, "skip": 0}
checks = []

def check(category, item, condition, detail=""):
    """记录一条检查结果"""
    if condition:
        results["pass"] += 1
        checks.append(("PASS", category, item, detail))
    else:
        results["fail"] += 1
        checks.append(("FAIL", category, item, detail))

def warn(category, item, condition, detail=""):
    if condition:
        results["warn"] += 1
        checks.append(("WARN", category, item, detail))

def skip(category, item, detail=""):
    results["skip"] += 1
    checks.append(("SKIP", category, item, detail))

def file_exists(path, category, label):
    exists = os.path.exists(str(path))
    check(category, f"{label} 文件存在", exists,
          f"路径: {path}" if not exists else "")
    return exists

def json_valid(path, category, label):
    try:
        with open(str(path), encoding='utf-8') as f:
            d = json.load(f)
        check(category, f"{label} JSON 有效", True)
        return d
    except Exception as e:
        check(category, f"{label} JSON 有效", False, str(e))
        return None

def content_contains(path, markers, category, label):
    """检查文件是否包含所有标记字符串"""
    try:
        with open(str(path), encoding='utf-8') as f:
            content = f.read()
        for marker in markers:
            found = marker in content
            check(category, f"{label} 包含 '{marker}'", found,
                  "" if found else f"文件: {path}")
    except Exception as e:
        check(category, f"{label} 可读", False, str(e))

def frontmatter_valid(path, required_fields, category, label):
    """检查 Markdown frontmatter"""
    try:
        with open(str(path), encoding='utf-8') as f:
            content = f.read()
        has_fm = content.startswith('---')
        check(category, f"{label} 有 frontmatter", has_fm)
        if has_fm:
            end_idx = content.find('---', 3)
            check(category, f"{label} frontmatter 闭合", end_idx > 0)
            fm_text = content[3:end_idx]
            for field in required_fields:
                found = field in fm_text
                check(category, f"{label} frontmatter 含 '{field}'", found,
                      "" if found else f"缺失字段: {field}")
    except Exception as e:
        check(category, f"{label} frontmatter 可读", False, str(e))

# ============================================================
# 1. L1 用户全局
# ============================================================
print("=" * 60)
print("1. L1 用户全局 (~/.claude/)")
print("=" * 60)

# L1-1: CLAUDE.md
f = CLAUDE_HOME / "CLAUDE.md"
if file_exists(f, "L1", "L1-1 CLAUDE.md"):
    content_contains(f, ["安全红线", "硬编码密钥", "知识库", "05-编程语言规范", "10-软件工程基础"],
                     "L1", "L1-1 CLAUDE.md")

# L1-2: settings.json
f = CLAUDE_HOME / "settings.json"
if file_exists(f, "L1", "L1-2 settings.json"):
    d = json_valid(f, "L1", "L1-2 settings.json")
    if d:
        env = d.get("env", {})
        required_env = ["ANTHROPIC_BASE_URL", "ANTHROPIC_MODEL", "API_TIMEOUT_MS",
                        "CLAUDE_CODE_SUBAGENT_MODEL"]
        for k in required_env:
            check("L1", f"L1-2 env.{k} 存在", k in env)
        check("L1", "L1-2 API_TIMEOUT >= 600000",
              int(env.get("API_TIMEOUT_MS", 0)) >= 600000)
        check("L1", "L1-2 model=deepseek-v4-pro", d.get("model") == "deepseek-v4-pro")
        check("L1", "L1-2 language=chinese", d.get("language") == "chinese")
        check("L1", "L1-2 theme=dark", d.get("theme") == "dark")

# L1-3~12: knowledge/
expected_dirs = {
    "01-Token成本优化": 5, "02-RAG最佳实践": 6, "03-性能优化": 4,
    "04-Python生态链": 5, "05-编程语言规范": 6, "06-安全规范": 8,
    "07-数据库规范": 5, "08-软件工程生命周期": 10,
    "09-国际与国家标准": 5, "10-软件工程基础": 10
}
for dname, expected_count in expected_dirs.items():
    dpath = CLAUDE_HOME / "knowledge" / dname
    exists = dpath.is_dir()
    check("L1", f"L1-knowledge/{dname} 目录", exists)
    if exists:
        actual = len(list(dpath.glob("*.md")))
        check("L1", f"L1-knowledge/{dname} 文件数={expected_count}",
              actual == expected_count, f"实际: {actual}")
        # 抽查每个目录的第一个文件
        files = list(dpath.glob("*.md"))
        if files:
            frontmatter_valid(files[0], ["category", "priority"], "L1",
                             f"L1-knowledge/{dname}/{files[0].name}")

# ============================================================
# 2. L2 项目共享—根目录
# ============================================================
print("\n" + "=" * 60)
print("2. L2 项目共享—根目录")
print("=" * 60)

# L2-1: CLAUDE.md
f = PROJECT / "CLAUDE.md"
if file_exists(f, "L2", "L2-1 CLAUDE.md"):
    markers = ["项目身份", "规范遵守", "安全红线", "Token 成本纪律",
               "推理质量纪律", "架构约定", "子代理协作策略", "记忆管理",
               "禁止事项", "Read-Before-Edit", "即时写入",
               "deepseek-v4-flash", "deepseek-v4-pro"]
    content_contains(f, markers, "L2", "L2-1 CLAUDE.md")
    # 验证与 config 模板一致
    template = PROJECT / "config/L2-项目共享/CLAUDE.md"
    if template.exists():
        with open(str(f), encoding='utf-8') as f1, open(str(template), encoding='utf-8') as f2:
            identical = f1.read() == f2.read()
        check("L2", "L2-1 CLAUDE.md 与 config/L2 模板一致", identical)

# L2-2: .claudeignore
f = PROJECT / ".claudeignore"
if file_exists(f, "L2", "L2-2 .claudeignore"):
    required_excludes = ["__pycache__", ".venv", ".git/", ".pytest_cache",
                         "node_modules", "dist/", "build/", ".vscode/", ".idea/"]
    content_contains(f, required_excludes, "L2", "L2-2 .claudeignore")

# L2-3: .gitignore
f = PROJECT / ".gitignore"
if file_exists(f, "L2", "L2-3 .gitignore"):
    required = ["/CLAUDE.local.md", "/.claude/settings.local.json",
                ".env", "*.pem", "*.key", "secrets/", "__pycache__"]
    content_contains(f, required, "L2", "L2-3 .gitignore")

# ============================================================
# 3. L2 .claude/ 配置
# ============================================================
print("\n" + "=" * 60)
print("3. L2 .claude/ 配置")
print("=" * 60)

# L2-4: settings.json
f = PROJECT / ".claude/settings.json"
if file_exists(f, "L2", "L2-4 settings.json"):
    d = json_valid(f, "L2", "L2-4 settings.json")
    if d:
        # 权限
        perms = d.get("permissions", {})
        allow = perms.get("allow", [])
        deny = perms.get("deny", [])

        check("L2", "L2-4 allow 数量=15", len(allow) == 15, f"实际: {len(allow)}")
        check("L2", "L2-4 deny 数量=9", len(deny) == 9, f"实际: {len(deny)}")

        # Allow 详细检查
        required_allow = [
            "Bash(git *)", "Bash(uv *)", "Bash(python -m pytest *)",
            "Bash(python -m ruff *)", "Bash(python -m mypy *)",
            "Bash(python deploy.py *)", "Bash(mkdir *)", "Bash(ls *)",
            "Bash(cat *)", "Bash(find *)", "Bash(echo *)", "Bash(wc *)",
            "Bash(curl http://localhost:*)", "Bash(curl https://api.deepseek.com:*)",
            "Read(**)"
        ]
        for a in required_allow:
            check("L2", f"L2-4 allow: {a}", a in allow)

        # Deny 详细检查
        required_deny = [
            "Bash(rm -rf *)", "Bash(git push --force *)",
            "Bash(git push origin main)", "Bash(git push origin master)",
            "Bash(dropdb *)", "Read(**/*.env)", "Read(**/*.pem)",
            "Read(**/*.key)", "Read(**/secrets/**)"
        ]
        for a in required_deny:
            check("L2", f"L2-4 deny: {a}", a in deny)

        # Hooks
        hooks = d.get("hooks", {})
        expected_hooks = ["PreToolUse", "PostToolUse", "Notification",
                         "Stop", "PreCompact", "SessionStart"]
        for h in expected_hooks:
            check("L2", f"L2-4 hook: {h}", h in hooks)

        # PreToolUse matchers
        pt_matchers = [entry.get("matcher", "") for entry in hooks.get("PreToolUse", [])]
        expected_matchers = ["rm -rf", "git push.*main", "git push.*master", "git commit"]
        for m in expected_matchers:
            check("L2", f"L2-4 PreToolUse matcher: {m}", m in pt_matchers)

        # PostToolUse matchers (should NOT have | or if)
        post = hooks.get("PostToolUse", [])
        for entry in post:
            matcher = entry.get("matcher", "")
            has_if = "if" in entry
            check("L2", f"L2-4 PostToolUse {matcher} 无 if 条件", not has_if,
                  f"残留 if: {entry.get('if','')}" if has_if else "")
        post_matchers = [e.get("matcher", "") for e in post]
        check("L2", "L2-4 PostToolUse 已拆分为 Edit+Write",
              "Edit" in post_matchers and "Write" in post_matchers)

        # SessionStart command
        ss_entries = hooks.get("SessionStart", [])
        if ss_entries:
            ss_cmd = ss_entries[0].get("hooks", [{}])[0].get("command", "")
            check("L2", "L2-4 SessionStart 检查 MEMORY.md", ".claude/MEMORY.md" in ss_cmd)
            check("L2", "L2-4 SessionStart 检查 primer.md", ".claude/primer.md" in ss_cmd)
            check("L2", "L2-4 SessionStart 检查 activeContext.md", ".claude/activeContext.md" in ss_cmd)
            check("L2", "L2-4 SessionStart 检查 CLAUDE.md", "CLAUDE.md" in ss_cmd)

        # Stop hook
        stop_entries = hooks.get("Stop", [])
        if stop_entries:
            stop_cmd = stop_entries[0].get("hooks", [{}])[0].get("command", "")
            check("L2", "L2-4 Stop 写入退出时间戳", ".last-session-exit" in stop_cmd)

        # 与 config/L2 模板一致性
        template = PROJECT / "config/L2-项目共享/settings.json"
        if template.exists():
            with open(str(template), encoding='utf-8') as f2:
                tpl = json.load(f2)
            identical = d == tpl
            check("L2", "L2-4 settings.json 与 config/L2 模板一致", identical,
                  "存在差异，需同步" if not identical else "")

# L2-5: primer.md
f = PROJECT / ".claude/primer.md"
if file_exists(f, "L2", "L2-5 primer.md"):
    markers = ["项目身份", "ADR-001", "ADR-002", "ADR-003", "ADR-004", "ADR-005",
               "分层架构", "向量数据库", "LangChain", "配置层级", "记忆管理"]
    content_contains(f, markers, "L2", "L2-5 primer.md")

# L2-6: activeContext.md
f = PROJECT / ".claude/activeContext.md"
if file_exists(f, "L2", "L2-6 activeContext.md"):
    content_contains(f, ["当前阶段", "已完成", "阻塞项", "下一步"],
                     "L2", "L2-6 activeContext.md")

# L2-7: MEMORY.md
f = PROJECT / ".claude/MEMORY.md"
if file_exists(f, "L2", "L2-7 MEMORY.md"):
    content_contains(f, ["session-2026-05-30", "metadata", "避坑"],
                     "L2", "L2-7 MEMORY.md")

# ============================================================
# 4. L2 .claude/rules/
# ============================================================
print("\n" + "=" * 60)
print("4. L2 .claude/rules/ 路径作用域规则")
print("=" * 60)

rules_dir = PROJECT / ".claude/rules"
expected_rules = {
    "security.md": {"paths": None, "markers": ["密钥管理", "API 认证", "输入验证", "SQL 注入", "日志安全"]},
    "python.md": {"paths": ["src/**/*.py", "tests/**/*.py"], "markers": ["类型注解", "异常处理", "禁止", "structlog", "docstring"]},
    "api.md": {"paths": ["src/api/**/*.py"], "markers": ["职责边界", "契约优先", "版本", "Pydantic", "速率限制"]},
    "database.md": {"paths": ["src/repositories/**/*.py", "src/models/**/*.py"], "markers": ["SQL", "SQLAlchemy", "批量操作", "Alembic"]},
    "testing.md": {"paths": ["tests/**/*.py"], "markers": ["覆盖率", "pytest", "Mock", "assert"]},
}

for fname, spec in expected_rules.items():
    f = rules_dir / fname
    if file_exists(f, "L2-rules", fname):
        # Frontmatter
        if spec["paths"] is None:
            # security.md should have NO paths (global)
            frontmatter_valid(f, ["description"], "L2-rules", f"{fname} frontmatter")
            with open(f, encoding='utf-8') as fh:
                content = fh.read()
            has_paths = "paths:" in content.split("---")[1]
            check("L2-rules", f"{fname} 无 paths (全局加载)", not has_paths,
                  "security.md 不应有 paths 字段" if has_paths else "")
        else:
            frontmatter_valid(f, ["paths", "description"], "L2-rules", f"{fname} frontmatter")
            for p in spec["paths"]:
                with open(f, encoding='utf-8') as fh:
                    check("L2-rules", f"{fname} paths 含 '{p}'", p in fh.read())

        # Content markers
        content_contains(f, spec["markers"], "L2-rules", f"{fname} 内容")

# ============================================================
# 5. L2 knowledge/
# ============================================================
print("\n" + "=" * 60)
print("5. L2 knowledge/ 项目知识库")
print("=" * 60)

l2_expected_dirs = {
    "01-Token成本优化": 6, "02-RAG最佳实践": 6, "03-性能优化": 5,
    "04-Python生态链": 5, "05-编程语言规范": 7, "06-安全规范": 9,
    "07-数据库规范": 5, "08-软件工程生命周期": 11,
    "09-国际与国家标准": 5, "10-软件工程基础": 16
}
for dname, expected_count in l2_expected_dirs.items():
    dpath = PROJECT / "knowledge" / dname
    exists = dpath.is_dir()
    check("L2-knowledge", f"knowledge/{dname} 目录", exists)
    if exists:
        actual = len(list(dpath.glob("*.md")))
        check("L2-knowledge", f"knowledge/{dname} 文件数={expected_count}",
              actual == expected_count, f"实际: {actual}")
        # Verify every file has valid frontmatter
        for mdf in dpath.glob("*.md"):
            frontmatter_valid(mdf, ["category", "priority"], "L2-knowledge",
                             f"knowledge/{dname}/{mdf.name}")

# Management docs
mgmt_files = [
    "README.md", "Claude Code软件工程初始化方案设计.md",
    "知识文件模板规范.md", "规则强制执行映射表.md",
    "知识反馈闭环协议.md", "知识审查协议.md", "避坑汇总.md"
]
for mf in mgmt_files:
    f = PROJECT / "knowledge" / mf
    check("L2-knowledge", f"knowledge/{mf} 存在", f.exists())

# Verify 避坑汇总 has 12 entries
f = PROJECT / "knowledge/避坑汇总.md"
if f.exists():
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    import re
    pitfalls = re.findall(r'###\s+\d+\.', content)
    check("L2-knowledge", f"避坑汇总 条目数>=11 (实际: {len(pitfalls)})",
          len(pitfalls) >= 11, f"条目: {pitfalls}")

# ============================================================
# 6. L3 项目本地
# ============================================================
print("\n" + "=" * 60)
print("6. L3 项目本地")
print("=" * 60)

# L3-1: CLAUDE.local.md
f = PROJECT / "CLAUDE.local.md"
if file_exists(f, "L3", "L3-1 CLAUDE.local.md"):
    content_contains(f, ["个人偏好", "语言", "模型", "本地开发环境", "个人约定"],
                     "L3", "L3-1 CLAUDE.local.md")

# L3-2: settings.local.json
f = PROJECT / ".claude/settings.local.json"
if file_exists(f, "L3", "L3-2 settings.local.json"):
    d = json_valid(f, "L3", "L3-2 settings.local.json")
    if d:
        # CRITICAL: must NOT have Bash(*)
        l3_allow = d.get("permissions", {}).get("allow", [])
        has_bash_star = any("Bash(*)" in a for a in l3_allow)
        check("L3", "L3-2 无 Bash(*) (安全)", not has_bash_star,
              "!!! Bash(*) 存在 — L2 安全模型被绕过 !!!" if has_bash_star else "")

        # Check effort
        check("L3", "L3-2 effort=high", d.get("effort") == "high")

        # Check env has required keys
        env = d.get("env", {})
        check("L3", "L3-2 env.API_TIMEOUT_MS 存在", "API_TIMEOUT_MS" in env)

        # Verify no deploy-specific Bash permissions leaked
        deploy_bash = [a for a in l3_allow if a.startswith("Bash(cp ") or a.startswith("Bash(mkdir ")]
        check("L3", "L3-2 无部署残留 Bash 权限", len(deploy_bash) == 0,
              f"残留: {deploy_bash}" if deploy_bash else "")

# Verify L3 files are git-ignored
import subprocess
for l3file in ["CLAUDE.local.md", ".claude/settings.local.json"]:
    result = subprocess.run(
        ["git", "check-ignore", "-q", l3file],
        cwd=str(PROJECT), capture_output=True
    )
    check("L3", f"L3 {l3file} git-ignored", result.returncode == 0)

# Verify config/L3 templates are NOT ignored
for tmpl in ["config/L3-项目本地/CLAUDE.local.md", "config/L3-项目本地/settings.local.json"]:
    result = subprocess.run(
        ["git", "check-ignore", "-q", tmpl],
        cwd=str(PROJECT), capture_output=True
    )
    check("L3", f"模板 {tmpl} 未被 git-ignore", result.returncode != 0,
          "模板文件被误排除!" if result.returncode == 0 else "")

# ============================================================
# 7. 全局记忆
# ============================================================
print("\n" + "=" * 60)
print("7. 全局记忆层")
print("=" * 60)

if MEMORY_DIR.is_dir():
    check("Memory", "全局记忆目录存在", True)
    expected = ["MEMORY.md", "memory-persistence-design.md",
                "session-v4.1-deploy.md", "session-v4.1-audit.md"]
    for mf in expected:
        f = MEMORY_DIR / mf
        check("Memory", f"全局记忆 {mf}", f.exists())
else:
    check("Memory", "全局记忆目录存在", False, str(MEMORY_DIR))

# ============================================================
# 8. config/ 模板
# ============================================================
print("\n" + "=" * 60)
print("8. config/ 配置模板")
print("=" * 60)

config_files = {
    "L0-组织强制": ["README.md"],
    "L1-用户全局": ["CLAUDE.md", "settings.json", "README.md"],
    "L2-项目共享": ["CLAUDE.md", "settings.json", ".claudeignore",
                    "primer.md", "activeContext.md", "MEMORY.md",
                    "global-memory.md", "README.md"],
    "L3-项目本地": ["CLAUDE.local.md", "settings.local.json", "README.md"],
}
for subdir, files in config_files.items():
    dpath = PROJECT / "config" / subdir
    check("Config", f"config/{subdir} 目录", dpath.is_dir())
    for fname in files:
        f = dpath / fname
        check("Config", f"config/{subdir}/{fname}", f.exists())

# config/README.md
f = PROJECT / "config/README.md"
check("Config", "config/README.md 手册", f.exists())

# ============================================================
# 9. deploy/ 脚本
# ============================================================
print("\n" + "=" * 60)
print("9. deploy/ 部署脚本")
print("=" * 60)

required_deploy = ["install.sh", "install.ps1", "install.bat", "README.md"]
for fname in required_deploy:
    f = PROJECT / "deploy" / fname
    check("Deploy", f"deploy/{fname}", f.exists())

# bash syntax check (only on Linux/WSL)
import platform
if platform.system() != "Windows":
    result = subprocess.run(["bash", "-n", str(PROJECT / "deploy/install.sh")],
                           capture_output=True, text=True)
    check("Deploy", "install.sh bash 语法", result.returncode == 0, result.stderr)
else:
    skip("Deploy", "install.sh bash 语法", "Windows 环境无 bash，跳过")

# ============================================================
# 10. 跨层一致性
# ============================================================
print("\n" + "=" * 60)
print("10. 跨层一致性检查")
print("=" * 60)

# L2 settings 与 config/L2 模板一致
f_actual = PROJECT / ".claude/settings.json"
f_template = PROJECT / "config/L2-项目共享/settings.json"
if f_actual.exists() and f_template.exists():
    with open(str(f_actual), encoding='utf-8') as f1, open(str(f_template), encoding='utf-8') as f2:
        d1, d2 = json.load(f1), json.load(f2)
    identical = d1 == d2
    check("一致性", ".claude/settings.json == config/L2/settings.json", identical)

# CLAUDE.md 一致性
f_actual = PROJECT / "CLAUDE.md"
f_template = PROJECT / "config/L2-项目共享/CLAUDE.md"
if f_actual.exists() and f_template.exists():
    with open(str(f_actual), encoding='utf-8') as f1, open(str(f_template), encoding='utf-8') as f2:
        identical = f1.read() == f2.read()
    check("一致性", "CLAUDE.md == config/L2/CLAUDE.md", identical)

# L1 CLAUDE.md 一致性
f_actual = CLAUDE_HOME / "CLAUDE.md"
f_template = PROJECT / "config/L1-用户全局/CLAUDE.md"
if f_actual.exists() and f_template.exists():
    with open(str(f_actual), encoding='utf-8') as f1, open(str(f_template), encoding='utf-8') as f2:
        identical = f1.read() == f2.read()
    check("一致性", "~/.claude/CLAUDE.md == config/L1/CLAUDE.md", identical)

# 方案文档 Hook 数量一致性
f = PROJECT / "knowledge/Claude Code软件工程初始化方案设计.md"
if f.exists():
    with open(f, encoding='utf-8') as fh:
        content = fh.read()
    # 方案应写 "9 个 Hook"
    has_9 = "9 个 Hook" in content
    check("一致性", "方案 §四 写 '9 个 Hook'", has_9,
          "方案文档 Hook 数量不是 9!" if not has_9 else "")
    # 方案应写 "82 个"
    has_82 = "82 个" in content
    check("一致性", "方案 §十 knowledge 写 '82 个'", has_82)

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("审计总结")
print("=" * 60)
print(f"通过: {results['pass']}  失败: {results['fail']}  警告: {results['warn']}  跳过: {results['skip']}")

if results['fail'] > 0:
    print("\n❌ 失败项:")
    for status, cat, item, detail in checks:
        if status == "FAIL":
            print(f"  [{cat}] {item}")
            if detail:
                print(f"       {detail}")

print(f"\n总检查项: {sum(results.values())}")
print(f"通过率: {results['pass']}/{results['pass']+results['fail']} ({100*results['pass']/(results['pass']+results['fail']):.1f}%)")

# 返回码
sys.exit(0 if results['fail'] == 0 else 1)
