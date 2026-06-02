# MCP 安装日志

> v4.2 部署完成：7/7 Connected | 1 项待 Redis 就绪

## 已安装（7/7）

| 阶段 | 日期 | MCP | 包名 | 状态 | 用途 |
|------|------|------|------|:--:|------|
| 1 | 05-31 | git | git-mcp-server | ✅ | 本地版本控制 |
| 1 | 05-31 | github | @modelcontextprotocol/server-github | ✅ | 远程协作（国内可能需代理） |
| 2 | 05-31 | search | one-search-mcp | ✅ | 多引擎搜索（替 Brave） |
| 2 | 05-31 | playwright | @playwright/mcp@latest | ✅ | 浏览器自动化（Chromium 已安装） |
| 2 | 05-31 | postgres | @modelcontextprotocol/server-postgres | ✅ | 数据库操作（只读用户） |
| 3 | 05-31 | filesystem | @modelcontextprotocol/server-filesystem | ✅ | 批量文件操作 |
| 3 | 05-31 | docker | mcp-server-docker | ✅ | 容器管理 + 沙箱执行 |

## 待安装（1 项）

| MCP | 依赖 | 就绪后执行 |
|------|------|------|
| **Redis** | Redis 服务运行 | `claude mcp add redis -- npx -y @gongrzhe/server-redis-mcp redis://localhost:6379` |

## 已移除

| MCP | 原因 |
|------|------|
| e2b (@e2b/mcp-server) | 海外 API 国内不可用；替选：Docker 本地沙箱 |
| docs (@arabold/docs-mcp-server) | Node.js v24 兼容性问题；替选：WebFetch + Playwright |

## 国内替选矩阵

| v4.2 原配 | 问题 | 替选 | 状态 |
|------|------|------|:--:|
| E2B Cloud | 海外 API + ghcr.io 均被封 | Docker 直接沙箱 | ✅ |
| Context7 | 海外 CDN 超时 | WebFetch + Playwright | ✅ |
| Brave Search | API 被墙 | OneSearch MCP | ✅ |

## 避坑记录

### 命令语法
- ❌ `claude mcp add <name> npx -y <pkg>` — `-y` 需在 `--` 后
- ✅ `claude mcp add <name> -- npx -y <pkg>`

### 包名纠正
| 方案文档原包名 | 实际可用包名 | 说明 |
|------|------|------|
| @anthropic/mcp-server-git | git-mcp-server | 官方未发布独立 Git MCP |
| @anthropic/mcp-server-filesystem | @modelcontextprotocol/server-filesystem | 官方在 @modelcontextprotocol 命名空间 |
| @anthropy/mcp-server-docker | mcp-server-docker | 社区维护 |
| @anthropy/mcp-server-redis | @gongrzhe/server-redis-mcp | 社区维护，需传 Redis URL |
| @iflow-mcp/one-search-mcp | one-search-mcp | npm 实际包名不同 |

### 安装失败
- `@arabold/docs-mcp-server` — Windows + Node.js v24 stdio 兼容性，已降级

### Docker 沙箱避坑 (来自审计)
| # | 问题 | 根因 | 解决 |
|:--:|------|------|------|
| 1 | `docker pull python:3.12-slim` checksum 错误 | 国内镜像站同步延迟 | 换 `python:3.12-alpine` |
| 2 | `-w /test` → `C:/Program Files/Git/test` | Git Bash MinGW 路径转换 | `MSYS_NO_PATHCONV=1` |
| 3 | 容器内 `~/.claude.json` 不可访问 | 家目录未挂载 | `-v C:\Users\...\\.claude.json:/root/.claude.json:ro` |
| 4 | `read-only filesystem` 写报告 | `:ro` 挂载 | 写入 `/tmp/` 或跳过 |
| 5 | 容器内 `docker` CLI 不存在 | Windows DinD 不可行 | 宿主机单独验证（见避坑 #28） |

### 审计脚本避坑
| # | 问题 | 根因 | 解决 |
|:--:|------|------|------|
| 1 | 正则 `in` 操作符误报 FAIL | Python `"pattern.*" in str` 是字面匹配，不执行正则 | 改用 `re.search()` |
| 2 | 跨行文本未匹配 (`src/api`) | CLI 规则在 code block 中换行 | 确认实际内容后标记为假阳性 |
| 3 | `#14` vs `14.` 格式不匹配 | .md 数字列表 vs markdown 标题 | 统一为数字列表格式 |
