# S02 / run-01 · DeepSeek Harness 源码分析与 LangChain 优化候选

> **后续授权更新（2026-11-12）：** 用户已确认DeepSeek主方案并授权重写正式llm设计。本次重写与核验记录见 [rewrite-01](rewrite-01/README.md)，正式入口见 [llm/README](../llm/README.md)。下文“llm保持原字节”和候选推荐仅描述此前只读研究阶段；旧回执未被覆盖，不能用于证明当前正式稿不变。


日期：2026-11-12（Asia/Shanghai）。状态：**本轮分析完成，优化候选待用户确认**。本轮属于研究与方案比较，不是 ModelProvider 实现 Run。

按用户要求，`../llm/` 正式草案保持原字节。本轮只写本 run-01；未改运行代码、依赖、其他 task 或被分析仓库。项目内 arch 技能仍不作为本轮设计依赖，未调用其生成器/校验器。

主要结论：借鉴 deepseek-harness 的稳定 seam、准备调用、配置快照、协议回放和计量分离；当前框架已选 LangChain，推荐把上一轮“Bridge → 自建协议驱动”的默认路径调整为 **LangChain 原生内部调用 + 统一治理协调器 + 边界 ModelClient**，减少重复协议和消息组装。该调整仅为本轮候选，尚未写回正式方案。

- [分析：源码事实、启发及不宜照搬之处](00-analysis.md)
- [思考：方案比较与判断依据](01-thinking.md)
- [行动：实际读取与验证](02-actions.md)
- [复盘：证据与证明边界](03-review.md)
- [反思：需要纠正的设计倾向](04-reflection.md)
- [完整 LangChain 优化候选](05-langchain-optimization.md)
- [输入基线与受保护文件 hash](evidence/baseline.json)
- [离线机制探针](evidence/langchain-mechanism-probe.py) / [实际结果](evidence/langchain-mechanism-results.json)
- [文档与写集核对](evidence/document-check.json)

参考仓库 HEAD：`47f943859bef60e4160492346772ded9b24f765a`。当前项目 S01 环境实装 LangChain 1.5.0、core 1.8.0、provider 1.7.4、LangGraph 1.2.20；已检查安装源码，未升级。

实际验证仅包含三个离线机制观察和文档/输入保留核对。TypeScript 测试、真实 provider、吞吐压测、多用户账务/故障及图片渲染均 not_run，不以源码存在测试当作本轮运行通过。
