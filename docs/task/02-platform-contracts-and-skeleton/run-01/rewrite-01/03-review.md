# 复盘：本轮产物与验证边界

日期：2026-11-12。review_mode=self_review；没有独立评审或实现验收。本轮目标是重写正式方案，实际文档核验见 [document-check.json](evidence/document-check.json) 与 [正式检查结果](../../llm/design-validation.json)。

## 结果

正式专题现在以DeepSeek ModelService模式为主，LangChain承接能力实现；Provider/ModelType/AIModelEntity贯穿目录、类型路由、参数/特性校验、调用样例及lib_request迁移。六类共享接口但保留真实payload；视觉属于LLM，检索cosine不冒充模型重排。后续透明接入只在参考文末保留方向，没有配置外部产品职责。

服务/Graph桥接共用执行内核、唯一有限重试owner、一次流投影和attempt级费用观察；共享资源与请求状态分离。费用覆盖tokens以外单位，不能把on_llm_end当六类usage来源，不能让未知量/价变0。S02/S03/S04/S10只在专题内给切片映射，没有批量重写其他task。

文档检查验证文件存在/链接、图源与正文相同、JSON样例六类、Python代码块可解析、来源hash、归档可读与写集范围。语义自审覆盖主次关系、六类边界、唯一调用owner、异步/状态隔离、多单位账务与迁移反例。机械检查不等于API可导入、Mermaid可视或服务运行正确。

## 范围核验

本轮30项项目输入、23项DSH源和9项已安装框架文件逐项核对；原稿16项归档核验。其他方案文件按起始hash检测，根S02概览有一处范围外排版变化，保留并单列 [观察](evidence/outside-write-set-observations.json)。该路径不在本轮写集，未擅自还原，也未将其当已授权方案调整。

前轮只读记录仍是历史证据；本轮在新目录记录重写，不反向改旧回执。新manifest覆盖当前正式稿，不把旧manifest继续当当前稿的一致性证明。

## 尚无的证明

ModelService/Provider/Bridge和六类Adapter均未实现；真实多厂商、API兼容、费用账本、并发容量、故障恢复、生产/业务效果均not_run。六类样例的语法/JSON存在，不证明已接入六类模型。DSH测试只读，Dify源码只参考；前轮机制探针只证明局部框架行为。

下一实施输入已集中到正式06的M1–M6与07的U01–U23。需要实际代码/具名厂商/持久治理的检查应在相应实施阶段留新证据，不能将本轮文档检查升级为这些验收。
