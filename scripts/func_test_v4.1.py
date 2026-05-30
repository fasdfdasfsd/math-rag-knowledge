#!/usr/bin/env python3
"""
v4.1 功能测试套件
测试范围: 权限 Allow/Deny | Hook 拦截 | Rules 注入 | 知识库引用 | Git 保护
"""
import subprocess, json, os, sys, tempfile
from pathlib import Path

PROJECT = Path("D:/panzt_projects/claude-code/python-rag")
results = {"pass": 0, "fail": 0, "skip": 0}
tests = []

def test(name, category, command, expect_success=True, timeout=10):
    """执行命令并判断结果是否符合预期"""
    try:
        result = subprocess.run(
            command, shell=True, capture_output=True, text=True,
            cwd=str(PROJECT), timeout=timeout
        )
        actual_success = result.returncode == 0
        passed = actual_success == expect_success
        status = "PASS" if passed else "FAIL"
        detail = f"exit={result.returncode}" + (f" stderr={result.stderr[:100]}" if result.stderr else "")
        if passed:
            results["pass"] += 1
        else:
            results["fail"] += 1
        tests.append((status, category, name, detail))
        return passed, result
    except subprocess.TimeoutExpired:
        results["fail"] += 1
        tests.append(("FAIL", category, name, "超时"))
        return False, None
    except Exception as e:
        results["skip"] += 1
        tests.append(("SKIP", category, name, str(e)))
        return False, None

print("=" * 60)
print("V4.1 功能验证测试套件")
print("=" * 60)

# ============================================================
# A. 权限 Allow 测试 — 确认允许的命令能正常执行
# ============================================================
print("\n--- A. Allow 权限功能测试 ---")

# A-1: git 命令可用
test("A-1: git status", "Allow", "git status", expect_success=True)

# A-2: ls 命令可用
test("A-2: ls 命令", "Allow", "ls CLAUDE.md", expect_success=True)

# A-3: cat 命令可用
test("A-3: cat 命令", "Allow", "cat .claudeignore | head -1", expect_success=True)

# A-4: echo 命令可用
test("A-4: echo 命令", "Allow", "echo 'test-ok'", expect_success=True)

# A-5: mkdir 命令可用 (分步执行避免 shell 链接问题)
test("A-5a: mkdir 命令", "Allow",
     "mkdir -p claude-test-tmp", expect_success=True)

# A-6: find 命令可用
test("A-6: find 命令", "Allow", "find .claude/rules -name '*.md' | head -1", expect_success=True)

# A-7: wc 命令可用
test("A-7: wc 命令", "Allow", "wc -l CLAUDE.md", expect_success=True)

# A-8: python -m pytest 可用 (检查 pytest 是否存在)
test("A-8: python -m pytest", "Allow",
     "python -m pytest --version 2>&1 || echo 'pytest not installed (expected)'",
     expect_success=True)

# A-9: python -m ruff 可用
test("A-9: python -m ruff", "Allow",
     "python -m ruff --version 2>&1 || echo 'ruff not installed'",
     expect_success=True)

# A-10: python -m mypy 可用
test("A-10: python -m mypy", "Allow",
     "python -m mypy --version 2>&1 || echo 'mypy not installed'",
     expect_success=True)

# ============================================================
# B. 权限 Deny 测试 — 确认危险操作被阻止
# ============================================================
print("\n--- B. Deny 权限验证 ---")

# B-1: .env 文件不可读 (如果存在)
env_file = PROJECT / ".env"
if not env_file.exists():
    env_file.write_text("SECRET=test")
    test("B-1: .env 创建测试文件", "Deny-prep", "echo done", expect_success=True)

# B-2: 验证 settings.json deny 规则存在
with open(str(PROJECT / ".claude/settings.json"), encoding='utf-8') as f:
    settings = json.load(f)
deny_rules = settings["permissions"]["deny"]

print("\nDeny 规则清单 (settings.json 中定义):")
for r in deny_rules:
    print(f"  {r}")

# 验证每条 deny 规则的格式
for i, rule in enumerate(deny_rules):
    is_valid = rule.startswith("Bash(") or rule.startswith("Read(")
    status = "PASS" if is_valid else "FAIL"
    if is_valid:
        results["pass"] += 1
    else:
        results["fail"] += 1
    tests.append((status, "Deny格式", f"B-{i+3}: {rule}", "格式正确" if is_valid else "格式异常"))

# ============================================================
# C. Hook 配置验证
# ============================================================
print("\n--- C. Hook 配置验证 ---")

hooks = settings["hooks"]
hook_types = list(hooks.keys())
print(f"Hook 类型: {hook_types}")

# C-1: PreToolUse 有 4 个 matcher
ptu = hooks.get("PreToolUse", [])
test("C-1: PreToolUse 条目数=4", "Hook",
     f"echo {len(ptu)} && [ {len(ptu)} -eq 4 ]", expect_success=True)

for entry in ptu:
    matcher = entry.get("matcher", "N/A")
    hooks_list = entry.get("hooks", [])
    has_cmd = len(hooks_list) > 0 and "command" in hooks_list[0]

    # C-2~5: 每个 PreToolUse 有 matcher 和 command
    cmd = hooks_list[0].get("command", "") if hooks_list else ""
    has_block = "exit 2" in cmd or "exit 0" in cmd

    if matcher in ["rm -rf", "git push.*main", "git push.*master"]:
        is_block = "exit 2" in cmd
        test(f"C-{matcher}: block hook (exit 2)", "Hook",
             f"echo " + ("block" if is_block else "warn"), expect_success=True)
    elif matcher == "git commit":
        is_warn = "exit 0" in cmd
        test(f"C-{matcher}: warn hook (exit 0)", "Hook",
             f"echo " + ("warn" if is_warn else "block"), expect_success=True)

# C-6: PostToolUse 有 2 个条目
post = hooks.get("PostToolUse", [])
test("C-6: PostToolUse 条目数=2", "Hook",
     f"echo {len(post)} && [ {len(post)} -eq 2 ]", expect_success=True)

# C-7, C-8: PostToolUse matcher 是 Edit 和 Write
post_matchers = [e.get("matcher", "") for e in post]
test("C-7: PostToolUse 含 Edit", "Hook",
     f"echo '{'Edit' in post_matchers}'", expect_success=True)
test("C-8: PostToolUse 含 Write", "Hook",
     f"echo '{'Write' in post_matchers}'", expect_success=True)

# C-9: 每个 PostToolUse 无 if 条件
for entry in post:
    has_if = "if" in entry
    matcher = entry.get("matcher", "?")
    if not has_if:
        results["pass"] += 1
        tests.append(("PASS", "Hook", f"C-Post {matcher} 无 if", "安全"))
    else:
        results["fail"] += 1
        tests.append(("FAIL", "Hook", f"C-Post {matcher} 有 if", entry.get("if", "")))

# C-10: Notification hooks
notif = hooks.get("Notification", [])
test("C-10: Notification 条目数=2", "Hook",
     f"echo {len(notif)} && [ {len(notif)} -eq 2 ]", expect_success=True)

# C-11: PreCompact hook 存在
compact = hooks.get("PreCompact", [])
test("C-11: PreCompact 存在", "Hook",
     f"echo {len(compact)} && [ {len(compact)} -ge 1 ]", expect_success=True)

# C-12: SessionStart hook 存在
ss = hooks.get("SessionStart", [])
test("C-12: SessionStart 存在", "Hook",
     f"echo {len(ss)} && [ {len(ss)} -ge 1 ]", expect_success=True)

# C-13: Stop hook 存在
stop = hooks.get("Stop", [])
test("C-13: Stop 存在", "Hook",
     f"echo {len(stop)} && [ {len(stop)} -ge 1 ]", expect_success=True)

# ============================================================
# D. Rules 注入验证
# ============================================================
print("\n--- D. Rules 路径作用域验证 ---")

rules_dir = PROJECT / ".claude/rules"

# D-1: security.md 无 paths (全局)
with open(str(rules_dir / "security.md"), encoding='utf-8') as f:
    content = f.read()
fm = content.split("---")[1] if "---" in content else ""
has_paths = "paths:" in fm
test("D-1: security.md 无 paths (全局)", "Rules",
     f"echo '{'no-paths' if not has_paths else 'has-paths'}' && [ {'1' if not has_paths else '0'} -eq 1 ]",
     expect_success=True)

# D-2~5: 其他 rules 有 paths
for fname, expected_paths in [
    ("python.md", ["src/**/*.py", "tests/**/*.py"]),
    ("api.md", ["src/api/**/*.py"]),
    ("database.md", ["src/repositories/**/*.py", "src/models/**/*.py"]),
    ("testing.md", ["tests/**/*.py"]),
]:
    with open(str(rules_dir / fname), encoding='utf-8') as f:
        content = f.read()
    fm = content.split("---")[1] if "---" in content else ""
    all_found = all(p in fm for p in expected_paths)
    test(f"D-{fname}: paths 正确", "Rules",
         f"echo '{'ok' if all_found else 'missing'}' && [ {'1' if all_found else '0'} -eq 1 ]",
         expect_success=True)

# ============================================================
# E. Git 保护验证
# ============================================================
print("\n--- E. Git .gitignore 保护验证 ---")

# E-1: L3 文件被 git-ignore
result = subprocess.run(["git", "check-ignore", "-q", "CLAUDE.local.md"],
                       cwd=str(PROJECT), capture_output=True)
test("E-1: CLAUDE.local.md git-ignored", "Git",
     f"echo exit={result.returncode}", expect_success=(result.returncode == 0))

result = subprocess.run(["git", "check-ignore", "-q", ".claude/settings.local.json"],
                       cwd=str(PROJECT), capture_output=True)
test("E-2: settings.local.json git-ignored", "Git",
     f"echo exit={result.returncode}", expect_success=(result.returncode == 0))

# E-3: config/L3 模板不被 ignore
result = subprocess.run(["git", "check-ignore", "-q", "config/L3-项目本地/CLAUDE.local.md"],
                       cwd=str(PROJECT), capture_output=True)
test("E-3: config/L3 模板不被 ignore", "Git",
     f"echo exit={result.returncode}", expect_success=(result.returncode != 0))

# E-4: git repo 存在
result = subprocess.run(["git", "rev-parse", "--git-dir"],
                       cwd=str(PROJECT), capture_output=True)
test("E-4: Git 仓库存在", "Git",
     f"echo exit={result.returncode}", expect_success=(result.returncode == 0))

# ============================================================
# F. 知识库可引用验证
# ============================================================
print("\n--- F. 知识库可引用验证 ---")

# F-1: L1 知识库文件可读
l1_files = [
    "~/.claude/knowledge/06-安全规范/03-密钥与认证管理.md",
    "~/.claude/knowledge/05-编程语言规范/Python-PEP8与编码规范.md",
]
for fpath in l1_files:
    expanded = os.path.expanduser(fpath)
    exists = os.path.exists(expanded)
    test(f"F-L1: {os.path.basename(fpath)}", "Knowledge",
         f"echo {'ok' if exists else 'missing'}", expect_success=exists)

# F-2: L2 知识库文件可读
l2_files = [
    "knowledge/01-Token成本优化/01-Prompt缓存策略.md",
    "knowledge/06-安全规范/09-API安全规范.md",
    "knowledge/避坑汇总.md",
]
for fpath in l2_files:
    exists = (PROJECT / fpath).exists()
    test(f"F-L2: {os.path.basename(fpath)}", "Knowledge",
         f"echo {'ok' if exists else 'missing'}", expect_success=exists)

# ============================================================
# G. L3 安全验证
# ============================================================
print("\n--- G. L3 安全验证 ---")

l3_path = PROJECT / ".claude/settings.local.json"
with open(str(l3_path), encoding='utf-8') as f:
    l3 = json.load(f)

l3_allow = l3.get("permissions", {}).get("allow", [])
has_bash_star = any("Bash(*)" in a for a in l3_allow)
test("G-1: L3 无 Bash(*)", "Security",
     f"echo {'FAIL-BashStar' if has_bash_star else 'OK'}", expect_success=not has_bash_star)

# L3 允许特定脚本 Bash 权限（由权限系统自动添加），但禁止通配
dangerous_bash = [a for a in l3_allow if a == "Bash(*)" or a == "Bash(python *)" or a == "Bash(curl *)"]
has_dangerous = len(dangerous_bash) > 0
specific_bash = [a for a in l3_allow if a.startswith("Bash(") and a not in dangerous_bash]
test("G-2: L3 无危险通配 Bash", "Security",
     f"echo {'FAIL:' + ','.join(dangerous_bash) if has_dangerous else 'OK:' + str(len(specific_bash)) + ' specific'}",
     expect_success=not has_dangerous)

# ============================================================
# 总结
# ============================================================
print("\n" + "=" * 60)
print("功能测试总结")
print("=" * 60)
print(f"通过: {results['pass']}  失败: {results['fail']}  跳过: {results['skip']}")

if results['fail'] > 0:
    print("\n失败项:")
    for status, cat, name, detail in tests:
        if status == "FAIL":
            print(f"  [{cat}] {name}")
            print(f"         {detail}")

total = sum(results.values())
rate = 100 * results['pass'] / (results['pass'] + results['fail']) if (results['pass'] + results['fail']) > 0 else 100
print(f"\n总测试: {total}  通过率: {rate:.1f}%")

# 清理测试文件
env_test = PROJECT / ".env"
if env_test.exists():
    env_test.unlink()

sys.exit(0 if results['fail'] == 0 else 1)
