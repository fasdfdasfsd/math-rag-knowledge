---
title: IEEE 标准体系
category: 国际与国家标准
priority: recommended
tags: [IEEE, SRS, 配置管理, 软件评审, 设计描述]
created: 2026-05-30
---

# IEEE 标准体系

## 概述

IEEE（Institute of Electrical and Electronics Engineers）制定的软件工程标准系列，专注于软件文档规范、评审流程和配置管理，是北美地区最广泛引用的软件工程标准之一。IEEE 标准常被 ISO 采纳为国际标准。

---

## 核心要点

### 1. IEEE 830 — 软件需求规格说明（SRS）

- 定义了 **SRS 的标准结构** 和内容要求
- 高质量 SRS 的 8 大特征：
  - 正确性（Correct）
  - 无歧义（Unambiguous）
  - 完整性（Complete）
  - 一致性（Consistent）
  - 按重要性分级（Ranked for importance/stability）
  - 可验证性（Verifiable）
  - 可修改性（Modifiable）
  - 可追踪性（Traceable）
- 标准章节模板：引言 → 总体描述 → 外部接口需求 → 系统功能 → 非功能需求 → 其他
- **已被 ISO/IEC/IEEE 29148:2018 取代**，但 830 的核心理念仍广泛使用

### 2. IEEE 828 — 配置管理（Configuration Management）

- 建立 **CM 计划** 的核心框架
- 四个基本活动：
  - **配置识别**（Configuration Identification）——标识每个配置项
  - **配置控制**（Configuration Control）——变更的评审与批准
  - **配置状态记录**（Configuration Status Accounting）——追踪变更历史
  - **配置审计**（Configuration Audit）——验证实际与记录一致
- 定义了 **基线（Baseline）** 概念：功能基线 → 分配基线 → 产品基线
- 已被 ISO/IEC/IEEE 24765 系列吸收

### 3. IEEE 1016 — 软件设计描述（SDD）

- 软件设计描述的推荐内容与组织方式
- 设计描述的核心关注点：
  - 架构设计（Architectural Design）
  - 详细设计（Detailed Design）
  - 接口设计（Interface Design）
  - 数据设计（Data Design）
- **设计视图（Design Views）** 概念：
  - 分解视图（Decomposition View）
  - 依赖视图（Dependency View）
  - 接口视图（Interface View）
  - 详细设计视图（Detailed Design View）
- 强调设计描述的 **多重视图** 方法，与 C4 模型思想一致

### 4. IEEE 1028 — 软件评审与审计

- 定义了五类评审类型：

| 评审类型 | 目的 | 参与方 |
|----------|------|--------|
| 管理评审 | 评估项目状态与进度 | 管理层 |
| 技术评审 | 评估技术方案正确性 | 技术专家 |
| 走查（Walkthrough） | 检查产品完整性 | 同级开发者 |
| 检查（Inspection） | 发现缺陷 | 主持人 + 检查员 |
| 审计（Audit） | 验证符合性 | 独立审计员 |

- 检查（Inspection）是缺陷发现效率最高的方式
- 推荐正式检查流程：计划 → 概述 → 准备 → 会议 → 返工 → 跟踪

---

## 实际应用指南

| 应用场景 | 参考标准 | 推荐做法 |
|----------|----------|----------|
| 编写需求规格说明书 | IEEE 830 / 29148 | 采用标准模板，确保可追踪性 |
| 建立配置管理流程 | IEEE 828 | 为每个项目编写 CM 计划 |
| 记录软件架构设计 | IEEE 1016 | 采用多视图方法描述设计 |
| 组织代码评审 | IEEE 1028 | 正式检查 vs 快速走查按需选择 |
| 编写用户文档 | IEEE 1063 | 参考软件用户文档标准 |
| 软件维护记录 | IEEE 1219 | 建立维护日志与变更记录 |

### 标准选择决策

- 新项目启动 → 参考 IEEE 830 或 ISO/IEC/IEEE 29148 编写 SRS
- 已有产品迭代 → 重点参考 IEEE 828 配置管理与基线控制
- 架构评审 → 参照 IEEE 1016 设计描述 + IEEE 1028 技术评审
- 发布前审计 → 执行 IEEE 1028 正式审计流程

---

## 参考来源

- IEEE 830-1998 — Recommended Practice for Software Requirements Specifications
- IEEE 828-2012 — Standard for Configuration Management in Systems and Software Engineering
- IEEE 1016-2009 — Standard for Information Technology—System Design—Software Design Descriptions
- IEEE 1028-2008 — Standard for Software Reviews and Audits
- ISO/IEC/IEEE 29148:2018 — Requirements Engineering
