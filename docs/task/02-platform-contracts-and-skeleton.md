# S02 · 平台骨架与公共合同

状态：planned。前置：S01 兼容升级通过。对应目标：L1 接入、领域边界与 L6 装配；设计依据：[平台分层](../ai-archtect/01-platform-architecture.md)。

## 1. 目标与阶段变化

从多个独立项目入口，过渡到一个可启动、可测试、依赖边界明确的平台外壳。原业务仍保留，不在本步复制第二套会议/旅行实现。此时只交付版本 API、类型合同和装配入口，不宣称有持久任务或动态注册。

```text
原有独立应用 + S01 版本基线
  → platform/src/agent_platform（公共合同 + bootstrap + API/Worker 启动角色）
  → 后续通过 Adapter 消费现有能力
```

## 2. 关键技术决定

- Python 包名为 `agent_platform`，与旧项目通用 `src` 包隔离；新增平台 `pyproject.toml/uv.lock`，沿用 S01 已验证的基础依赖版本。
- 领域/应用合同不导入 FastAPI、LangGraph、A2A SDK 或数据库驱动；由 adapters/infrastructure 实现 port，bootstrap 装配。
- 框架装配采用 create_agent / middleware / context_schema 与 LangGraph 子图；公共合同映射 response_format/structured_response、content_blocks 和 v3 类型化事件。新能力清单及成熟度见[采用基线](01-langchain-upgrade.md)。
- 先固定版本化对象：AgentDefinition、ConfigRevision、Run、Task、Attempt、Event、Artifact、Decision、AgentEvent，以及统一错误码与状态转换规则。
- API 入参中的 tenant、owner、角色名称不授予权限；实际身份从认证上下文取得。提前定义数据可见性、secret 引用和预算字段。

## 3. 实施任务

| ID | 工作 | 拟修改/新增位置 | 完成条件 |
|---|---|---|---|
| S02-A | 创建可构建包和配置装配 | `platform/pyproject.toml`、`src/agent_platform/bootstrap/` | 从锁文件构建安装，API/Worker 启动互相独立 |
| S02-B | 固定对象和接口 Schema | `contracts/`，版本化示例 | 成功、失败、等待、未知输出均有可解析样例 |
| S02-C | 定义 Adapter/Pattern port | contracts/application ports | invoke/inspect/cancel 的 unsupported 与未知语义明确 |
| S02-D | 提供最小 API/Worker 外壳 | `api/`、Worker 入口 | liveness/readiness 分开；未接入能力返回明确未实现，不返回假成功 |
| S02-E | 建立基础检查 | `tests/contract/`、CI 配置 | Schema、包导入边界、锁文件重现通过 |

本步同时固定首版部署环境、容量/延迟测量口径、模型预算和业务评测集的版本；缺输入时使用明确的候选值，不写成已承诺 SLO。

## 4. 验收与回滚

从干净环境启动 API/Worker，验证认证上下文、非法租户、Schema 不匹配、未知 revision、统一错误和版本兼容。合同样例包含 messages 内容块与工件引用，避免把框架对象当公共 wire schema。检查旧入口仍可在各自环境运行。

本步没有长任务执行，不能只用 `/health` 作为平台能力验收。回滚时停用新 API/Worker 入口，保留合同版本和测试结果，继续原应用；不删除旧项目或修改其数据格式。

## 5. 重要文档与交接

本篇为该步骤的重要文档。实施后必须加入包结构/依赖图、合同版本、消费者样例、实际检查结果及尚未接入的能力清单。交给 S03 的固定输入是可构建包、Adapter port 和事件/输出合同；交给 S04 的输入还包括状态机草案。当前实现/测试结果：**not_run**。
