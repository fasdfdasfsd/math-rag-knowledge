---
title: CMMI 成熟度模型
category: 国际与国家标准
priority: recommended
tags: [CMMI, 成熟度, 过程改进, 质量]
created: 2026-05-30
---

# CMMI 成熟度模型

## 概述

CMMI（Capability Maturity Model Integration）由 CMMI Institute（现属 ISACA）发布，是评估和改进组织过程成熟度的框架。CMMI 2.0 于 2018 年发布，简化了模型结构并增强了对 Agile 和 DevOps 的支持。

---

## 核心要点

### CMMI 2.0 五级成熟度

| 等级 | 名称 | 核心特征 | 组织行为 |
|------|------|----------|----------|
| 1 | 初始级（Initial） | 过程不可预测，依赖个人英雄主义 | 救火式管理，成功靠个人能力 |
| 2 | 管理级（Managed） | 项目级过程已制度化 | 需求、计划、质量、配置得到管理 |
| 3 | 定义级（Defined） | 组织级标准过程已建立 | 跨项目复用，组织资产沉淀 |
| 4 | 量化管理级（Quantitatively Managed） | 过程用统计方法控制 | 用数据驱动决策，预测能力 |
| 5 | 优化级（Optimizing） | 持续改进，量化优化 | 主动发现薄弱环节，系统化改进 |

### 每个等级核心实践领域

#### Level 2 — 管理级（10 个实践领域）
- REQM — 需求管理
- PP — 项目计划
- PMC — 项目监控与控制
- SAM — 供应商协议管理
- MA — 度量与分析
- CM — 配置管理
- PPQA — 过程与产品质量保证
- RSK — 风险管理（CMMI 2.0 新增为独立 PA）
- CAR — 因果分析与解决
- OPD — 组织级过程定义

#### Level 3 — 定义级（新增领域）
- RD — 需求开发
- TS — 技术解决方案
- PI — 产品集成
- VER — 验证
- VAL — 确认
- IPM — 集成项目管理
- OPP — 组织级过程性能
- OT — 组织级培训

#### Level 4 — 量化管理级
- OPP — 组织级过程性能（深化）
- QPM — 量化项目管理

#### Level 5 — 优化级
- CAR — 因果分析与解决（深化）
- OPM — 组织级绩效管理

### CMMI 2.0 重要变化

- 从 **1.3 版 22 个过程域** 简化为 **实践领域（Practice Areas）**
- 引入 **敏捷视角**：每个实践领域可映射到 Scrum / SAFe 实践
- 新增 **信息安全（SEC）** 和 **虚拟解决方案（VRS）** 领域
- 支持 **持续改进视图**（Continuous View）和 **阶段式视图**（Staged View）

### CMMI vs ISO 9001 对比

| 维度 | CMMI | ISO 9001 |
|------|------|----------|
| 侧重点 | 软件过程成熟度 | 质量管理体系 |
| 等级 | 5 级成熟度 | 单一认证/不评级 |
| 覆盖范围 | 软件/系统开发全流程 | 通用质量管理 |
| 评估方式 | SCAMPI 评估（1-5 级） | 外部审核（通过/不通过） |
| 适合场景 | 软件开发组织 | 任何类型组织 |
| 更新频率 | 约 3-5 年大版本 | 约 5-7 年修订 |
| 互认性 | CMMI L3 ≈ ISO 9001 良好的质量管理基础 | - |

### 中小企业适用性分析

| 考量点 | 建议 |
|--------|------|
| 资源投入 | L2 评估约需 3-6 个月，L3 约 6-12 个月 |
| 团队规模 | < 20 人团队建议以 L2 为目标，非必须认证 |
| 实际获益 | L2 的管理规范化对 20-50 人团队价值最大 |
| 替代方案 | 小型团队可参考 CMMI 实践但不做正式评估 |
| 轻量实施 | 选择 3-5 个核心实践领域先行落地 |

---

## 实际应用

1. **初创团队**：学习 L2 实践领域理念，建立需求管理+配置管理基础
2. **成长型公司（20-100 人）**：争取达到 CMMI L3，建立组织级过程资产
3. **大型企业/外包商**：通过 CMMI L4/L5 作为竞标资质
4. **已通过 ISO 9001 的企业**：在质量基础上增加 CMMI 过程改进，事半功倍
5. **Agile 团队**：CMMI 2.0 已提供敏捷映射，可按需选择实践而非全盘照搬

---

## 参考来源

- CMMI Institute. CMMI V2.0 Model Introduction
- ISACA. CMMI V2.0 Model Overview
- SEI. CMMI for Development (CMMI-DEV) v1.3
- ISO 9001:2015 — Quality Management Systems
- Chrissis, M.B., Konrad, M., & Shrum, S. CMMI for Development: Guidelines for Process Integration and Product Improvement
