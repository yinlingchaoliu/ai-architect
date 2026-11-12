# {{title}}

日期：{{date}}。项目：{{project}}。状态：**draft**。文档类型：`target-architecture`。

来源/候选：{{baseline}}

## 1. 目标与非目标

{{scope}}

## 2. 分层、领域和依赖方向

| 层/领域 | 拥有数据与职责 | 提供契约 | 不承担 | 消费方 |
|---|---|---|---|---|
{{layers}}

```mermaid
{{diagram}}
```

## 3. 代码结构与部署单元

{{project_structure}}

{{deployment}}

## 4. 关键调用与公共合同

{{contracts}}

{{flows}}

## 5. 方案取舍与迁移

{{alternatives}}

{{migration}}

## 6. 验收与未知

{{acceptance}}

{{unknowns}}
