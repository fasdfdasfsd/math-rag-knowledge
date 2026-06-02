# 术语表 (Glossary)

## 1. 编写说明

本词汇表的编写目的是解释软件需求规格说明文档中使用和定义的术语。
一方面，本表将规范词汇含义，避免客户或开发团队误解；
另一方面，本表将作为团队下一阶段识别对象的依据。[reference:8]

在需求定义时，系统词汇表是必不可少的组成部分。系统词汇表是系统（业务）术语的集合，
这些术语的含义用自然语言表达出来，寻求需求人员和用户对该词汇有一致的认识并固定下来。[reference:9]

---

## 2. 需求分析阶段术语


| 术语       | 英文                   | 定义                                                                           |
| ---------- | ---------------------- | ------------------------------------------------------------------------------ |
| 用户故事   | User Story             | 采用"作为[角色]，我想要[功能]，以便于[价值]"的模板描述需求，强制从用户视角思考 |
| 史诗       | Epic                   | 大型用户故事的集合，通常横跨多个迭代周期                                       |
| 功能需求   | Functional Requirement | 描述系统必须完成的行为或功能                                                   |
| 非功能需求 | NFR                    | 定义系统质量属性，包括性能、可用性、安全性等                                   |
| 用例       | Use Case               | 描述系统与外部参与者之间交互的序列                                             |
| 干系人     | Stakeholder            | 与系统有利益关系的个人或组织                                                   |

## 3. 设计阶段术语


| 术语      | 英文                      | 定义                                                                     |
| --------- | ------------------------- | ------------------------------------------------------------------------ |
| 分层架构  | Layered Architecture      | 将系统划分为表现层、业务逻辑层、数据访问层                               |
| 微服务    | Microservices             | 将单体应用拆分为独立部署的服务，每个服务拥有自己的数据库                 |
| 事件驱动  | Event-Driven              | 通过事件总线解耦组件，适用于异步处理场景                                 |
| 设计模式  | Design Pattern            | 可复用的面向对象软件设计经验总结                                         |
| MVC       | Model-View-Controller     | 将应用分为模型、视图、控制器三部分的架构模式                             |
| ORM       | Object-Relational Mapping | 对象关系映射，实现面向对象编程语言与关系数据库之间的数据转换             |
| SOLID原则 | SOLID Principles          | 面向对象设计的五个基本原则：单一职责、开闭、里氏替换、接口隔离、依赖反转 |

## 4. 开发与测试阶段术语


| 术语     | 英文                                         | 定义                                     |
| -------- | -------------------------------------------- | ---------------------------------------- |
| CI/CD    | Continuous Integration/Continuous Deployment | 持续集成/持续部署                        |
| 单元测试 | Unit Test                                    | 对软件中最小可测试单元进行检查和验证     |
| 集成测试 | Integration Test                             | 对多个模块组合后的功能进行验证           |
| 回归测试 | Regression Test                              | 验证代码修改后原有功能是否仍正常         |
| API      | Application Programming Interface            | 应用程序接口，定义软件组件之间交互的规范 |
| RESTful  | Representational State Transfer              | 一种网络应用程序的设计风格和开发方式     |
| JWT      | JSON Web Token                               | 一种用于身份认证的开放标准令牌格式       |

## 5. 部署与运维阶段术语


| 术语     | 英文                      | 定义                                                 |
| -------- | ------------------------- | ---------------------------------------------------- |
| DevOps   | Development & Operations  | 开发运维一体化文化与实践                             |
| 容器化   | Containerization          | 将应用及其依赖打包为标准容器镜像的技术               |
| 负载均衡 | Load Balancing            | 将流量分发到多个服务器以提高可用性和响应速度         |
| SLA      | Service Level Agreement   | 服务等级协议，定义服务提供商与客户之间的服务质量约定 |
| RBAC     | Role-Based Access Control | 基于角色的访问控制，根据用户角色授予权限             |

## 6. 通用软件开发术语


| 术语           | 英文                                      | 定义                                                           |
| -------------- | ----------------------------------------- | -------------------------------------------------------------- |
| 需求规格说明书 | SRS (Software Requirements Specification) | 描述软件系统必须提供的功能和性能以及限制条件的文档             |
| 高可用         | HA (High Availability)                    | 系统在面临故障时仍能持续提供服务的能力                         |
| 灾备           | Disaster Recovery                         | 在灾难发生后恢复系统和数据的能力                               |
| 敏捷开发       | Agile Development                         | 以用户需求为核心，采用迭代、循序渐进的方式进行软件开发的方法论 |
| 版本控制       | Version Control                           | 对软件开发过程中文件变化的管理和追踪                           |
| SaaS           | Software as a Service                     | 软件即服务，一种通过互联网提供软件的模式                       |

---

## 参考标准

- IEEE Std 830-1998：IEEE Recommended Practice for Software Requirements Specifications
- ISO/IEC/IEEE 29148:2011：Systems and Software Engineering — Life Cycle Processes — Requirements Engineering[reference:10]
- GB/T 8567-2006：计算机软件文档编制规范
