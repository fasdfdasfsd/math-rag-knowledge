# Claude Code 用户全局指令

## 全局规则（所有项目遵守）

### 安全红线
- 禁止在任何代码、配置文件、日志中硬编码密钥/密码/Token
- 敏感文件（.env, *.pem, *.key, credentials.*）禁止被提交到版本控制
- 用户输入必须先验证后使用
- 第三方依赖使用前需检查安全漏洞和许可证

### 编码通用原则
- 优先使用项目配置的 linter/formatter
- 类型注解完整
- 函数保持短小（≤50 行）
- 不写"神奇数字"，使用命名常量

### Claude Code 使用习惯
- 重要决策后提醒记录到 MEMORY.md
- 长对话定期触发 /compact
- 新任务开始前先查阅 knowledge/ 对应规范
- Token 消耗保持克制，优先用缓存和更小模型

## 全局知识库

路径：`~/.claude/knowledge/`

| 分类 | 内容 |
|------|------|
| 05-编程语言规范 | Python, Java, JS/TS, React, SQL, API |
| 06-安全规范 | OWASP, 密钥管理, 注入防护, 隐私合规, Prompt安全 |
| 07-数据库规范 | PostgreSQL, MySQL, Redis, MongoDB, 向量数据库 |
| 08-软件工程生命周期 | 立项→需求→架构→开发→CR→审计→测试→CI/CD→验收→运维 |
| 09-国际与国家标准 | ISO, IEEE, CMMI, GB/T, PIPL/等保 |
| 10-软件工程基础 | 术语, 设计模式, 架构模式, 质量度量, 版本管理 |

> 注：项目级知识库（01~04）在项目 `knowledge/` 目录下，不在全局路径中。

查阅方式：
```
@~/.claude/knowledge/06-安全规范/03-密钥与认证管理.md
@~/.claude/knowledge/05-编程语言规范/Python-PEP8与编码规范.md
@~/.claude/knowledge/07-数据库规范/PostgreSQL规范.md
```
