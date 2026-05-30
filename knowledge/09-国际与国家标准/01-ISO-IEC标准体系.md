---
title: ISO/IEC 标准体系
category: 国际与国家标准
priority: recommended
tags: [ISO, IEC, 质量标准, 安全标准, 软件过程]
created: 2026-05-30
---

# ISO/IEC 标准体系

## 概述

ISO（International Organization for Standardization）与 IEC（International Electrotechnical Commission）联合发布的软件与系统工程标准体系，覆盖软件生命周期过程、产品质量模型、信息安全管理及质量管理体系，是国际通行的软件工程基准框架。

---

## 核心要点

### 1. ISO/IEC 12207:2017 — 软件生命周期过程

| 过程类别 | 过程名称 | 说明 |
|----------|----------|------|
| 协议过程 | 获取 / 供应 | 甲方乙方合同对接 |
| 组织级使能过程 | 生命周期模型管理 / 基础结构管理 / 质量保证 | 组织能力建设 |
| 技术过程 | 需求定义 / 设计 / 构建 / 集成 / 测试 / 部署 / 维护 | 核心开发流程 |
| 技术管理过程 | 项目计划 / 评估 / 风险管理 / 配置管理 | 项目管理活动 |

- 定义了 **43 个过程**，覆盖从概念到退役全生命周期
- 2017 版简化了过程数量，增强了与 Agile / DevOps 的兼容性

### 2. ISO/IEC 25010 — 软件质量模型（SQuaRE 系列）

八大质量特性（Product Quality Model）：

| 特性 | 子特性示例 | 说明 |
|------|-----------|------|
| 功能适用性 | 功能完备性、正确性、适合性 | 软件是否满足需求 |
| 性能效率 | 时间行为、资源利用率、容量 | 响应速度与资源消耗 |
| 兼容性 | 共存性、互操作性 | 与其它系统协作 |
| 易用性 | 可辨识性、易学性、可操作性、错误防护 | 用户体验 |
| 可靠性 | 成熟度、可用性、容错性、可恢复性 | 系统稳定性 |
| 安全性 | 机密性、完整性、抗抵赖性、可追踪性 | 数据保护 |
| 可维护性 | 模块化、可复用性、可分析性、可修改性、可测试性 | 代码维护 |
| 可移植性 | 适应性、可安装性、可替换性 | 跨平台部署 |

- 同时包含 **Quality in Use 模型**（有效性、效率、满意度、抗风险、上下文覆盖）
- 2011 年发布，2023 年进行修订更新

### 3. ISO/IEC 27001 — 信息安全管理

- 建立 **ISMS（Information Security Management System）**
- PDCA 循环：Plan → Do → Check → Act
- Annex A 包含 **14 个控制域**、**114 项控制措施**
- 核心原则：**CIA 三元组** — 机密性（Confidentiality）、完整性（Integrity）、可用性（Availability）
- 与 ISO 27002（实施细则）配合使用
- 认证有效期 3 年，需年度监督审核

### 4. ISO 9001 — 质量管理体系

- 七项管理原则：以顾客为关注焦点 / 领导力 / 全员参与 / 过程方法 / 改进 / 循证决策 / 关系管理
- 强调 **持续改进（Continual Improvement）** 和 **过程方法（Process Approach）**
- 与 CMMI 相比，ISO 9001 更侧重质量管理体系而非过程成熟度
- 2015 版引入了基于风险的思维（Risk-Based Thinking）

---

## 实际应用

| 场景 | 参考标准 | 说明 |
|------|----------|------|
| 定义软件开发生命周期流程 | ISO/IEC 12207 | 制定组织级过程规范 |
| 制定软件质量指标体系 | ISO/IEC 25010 | 选择度量指标与质量目标 |
| 建立信息安全管理体系 | ISO/IEC 27001 | 通过认证提升客户信任 |
| 搭建质量管理体系 | ISO 9001 | 跨行业通用质量管理 |
| 供应商能力评估 | ISO/IEC 12207 + 9001 | 评估外包方开发能力 |
| 系统安全合规审计 | ISO/IEC 27001 | 配合行业监管检查 |

---

## 参考来源

- ISO/IEC 12207:2017 — Systems and software engineering — Software life cycle processes
- ISO/IEC 25010:2011 — Systems and software engineering — Systems and software Quality Requirements and Evaluation (SQuaRE)
- ISO/IEC 27001:2022 — Information security, cybersecurity and privacy protection
- ISO 9001:2015 — Quality management systems — Requirements
