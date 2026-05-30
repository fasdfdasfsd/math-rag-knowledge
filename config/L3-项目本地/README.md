# L3 — 项目本地层

> 部署位置：`<项目根>/.claude/settings.local.json` 和 `<项目根>/CLAUDE.local.md`
> 
> ⚠️ 这两个文件包含个人密钥，**已在 .gitignore 中排除，禁止提交**

## 部署步骤

### 1. 编辑 settings.local.json
填入你的个人 API 密钥：
```json
"ANTHROPIC_AUTH_TOKEN": "sk-你的密钥"
```

### 2. 部署
```bash
cp config/L3-项目本地/settings.local.json .claude/settings.local.json
cp config/L3-项目本地/CLAUDE.local.md ./CLAUDE.local.md
```

## 安全规则
- 🚫 禁止将 settings.local.json 提交到 Git
- 🚫 禁止将 CLAUDE.local.md 提交到 Git
- ✅ .gitignore 已自动排除这两个文件
