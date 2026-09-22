# ES-02 西班牙平衡容量规则（2025 历史期 / 2026-08-11 基准）

> 研究对象：独立电化学储能；范围仅覆盖平衡容量采购、与容量直接相连的申报/资格/履约规则及容量收入判断。完整平衡能量激活、能量价格、不平衡公式、现货规则和模型实现留在 ES-03/ES-05 及以后阶段。所有网页/PDF访问日期：2026-08-11。

## 1. 结论摘要：什么是容量市场，什么不是

| 产品 | 2025 年西班牙容量采购/收入判断 | 独立储能结论（不等于产品预认证） | 依据 |
|---|---|---|---|
| FCR / regulación primaria | 未识别可由 BSP 竞价取得的容量市场。REE 非规范性指南将其描述为并网发电机的强制、无偿自动物理响应；约束性 P.O.1.5 确认年度需求和响应性能。 | 一般储能可成为 BSP 的规则并不自动扩展到 FCR；独立电池 FCR 资格、补偿和测试仍 `unresolved`。 | S-REE-GUIDE-2024 pp.10-11；S-CNMC-2024-MP Art.5；P.O.1.5 §4.1 |
| aFRR / regulación secundaria | **有本地容量/备用市场和容量收入**：D-1 每日、15 分钟产品，上/下分开竞价，边际容量价格。容量中标后有等量能量支持报价义务。 | 储能持有人可作为 BSP；一般报价能力≥1 MW；aFRR BSP 上、下方向已 habilitado reserve 合计≥100 MW。产品测试、SOC、持续时间留 ES-04。 | S-CNMC-2024-MP Arts.7(1)(c), 7(4)-(5), 9-10；P.O.7.2 §§5.1-5.3、Annex I |
| mFRR / regulación terciaria | 未识别独立容量采购或容量费。P.O.7.3 的“次日备用需求”和“可用备用报价”是为能量激活准备，不是容量出清收入。 | 储能一般参与原则和≥1 MW门槛已确认；产品预认证、能量持续性和SOC留 ES-04。 | S-CNMC-2024-11535-PO pp.155-160；BOE-A-2025-5342 §§1362-1395 |
| RR / reservas de sustitución | 未识别独立容量采购或容量费。2025 P.O.3.3只规定RR平衡能量报价（€/MWh）和激活结算；TERRE为能量平台。 | 2025储能一般 BSP/测试入口已确认，P.O.3.3产品专门条件仍待确认；TERRE停止后2026替代机制不得外推。 | S-CNMC-2025-QH P.O.3.3 §§13.1、Annex I；S-ACER-RR-IF；S-ENTSOE-TERRE-2026 |
| IN / IGCC | 非BSP产品或容量市场；是TSO-TSO不平衡净额过程。 | 储能不能以IN参与者身份取得本地容量收入。 | S-ACER-IN-IF；CNMC P.O.7.2/REE平台说明 |
| SRAD | **有本地特定产品容量拍卖和容量费**，对象是需求响应；2025为年度服务框架，2026规则改为原则上六个月合同/每年两次。 | 独立储能是否能以需求响应身份参加未确认，不能从标准产品储能资格推断。 | S-SRAD-2025 §§119-138, 167-179, 217-225；S-SRAD-2026 §§124-138 |

**研究解释**：在西班牙，`reserve requirement`、预认证能力、强制提交可用备用和真正的 `capacity/reserve market` 必须分开。经审阅的约束性文本只明确给 aFRR 建立“mercado de reserva de balance”；mFRR/RR 的文本是能量报价/激活规则，SRAD 是需求响应特定容量拍卖。

**建模假设**：ES-02 未新增建模假设。上述“未识别容量市场”是基于审阅的 2025 约束性 P.O.文本的证据范围结论，不是对未来规则的永久否定。

## 2. 一般 BSP、聚合与储能入口（先于逐产品规则）

| Claim ID | 规则事实（官方原文含义） | 官方来源、日期/生效期、定位 | 研究解释 | 对独立储能相关性 | 状态/信心 |
|---|---|---|---|---|---|
| ES02-GEN-001 | 生产、需求、**储能设施持有人**、商业化商及其代表，满足条件后可通过一个或多个已 habilitada UP 成为 BSP。 | S-CNMC-2024-MP，CNMC，发布2024-06-06；条件自BOE发布30日后生效（2024-07-06，Resuelve Segundo）；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.7(1)(a)-(e)，BOE HTML §§653-665；访问2026-08-11。 | 储能一般 BSP 身份有约束性依据，不再只依赖 REE 指南。 | 独立电化学储能可进入后续产品资格流程，但不代表任何产品自动获准。 | `confirmed` / 高 |
| ES02-GEN-002 | 每个 BSP UP 一般最低报价能力为1 MW；如果欧洲标准产品IF设定不同最小值，以该标准值为准。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.7(4)，BOE HTML §§666-668；S-REE-GUIDE-2024，REE，2024-12，https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/Guia_descriptiva_Ser_proveedor_servicios_de_ajuste.pdf，p.14为操作解释；访问2026-08-11。 | 1 MW是UP/BSP报价门槛，不是每个储能电芯/站点必然门槛，也不是容量收入资格本身。 | 申报聚合时应先满足UP/BSP层级门槛；产品专门最小值仍需检查。 | `confirmed` / 高 |
| ES02-GEN-003 | aFRR BSP须有一或多个UP，全部获aFRR habilitación；上、下方向已 habilitado reserve 合计至少100 MW。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.7(5)，BOE HTML §§669-675；访问2026-08-11。 | 100 MW是aFRR BSP总体预认证容量条件，明确为上+下合计；不是单个电池或单方向100 MW。 | 聚合储能若要组成aFRR BSP，必须解决100 MW合计条件及同组/代表限制；具体过渡适用留ES-04。 | `confirmed` / 高 |
| ES02-GEN-004 | UP按主要活动类型区分为generation、demand、storage；一般按市场参与者、BRP和生产类型聚合；具有安全相关个体化要求的设施须单独UP。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.8(1)-(6)，BOE HTML §§676-684；访问2026-08-11。 | 聚合边界不是任意混合，储能UP与generation/demand UP原则上分开。 | 独立储能的同类聚合可行性有框架依据，但电气/安全相关个体化限制仍需P.O.3.1/ES-04核对。 | `confirmed` / 高 |
| ES02-GEN-005 | 储能、需求和发电设施 habilitación 需申请、实时经合格控制中心交换信息、更新结构数据，并满足对应产品的测试/响应曲线要求；**Art.9(2)(d)保留例外：未单独通过测试的设施，可在规定比例内并入已有合格的服务UP**。标准产品还须符合相应IF产品特征；测试入口在P.O.3.8。 | **S-CNMC-2024-MP**（CNMC，2024-06-06发布；条件自2024-07-06起生效，产品条款按SRS/MARI/PICASSO连接切换），BOE-A-2024-11535，https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf，Art.9(1)-(4)，BOE PDF pp.30-31/HTML §§685-697；P.O.3.8入口，PDF pp.71-86。 | 一般准入、产品预认证和测试是三层条件；Art.9(2)(d)的UP比例例外不能被改写成“每个设施必须单独通过测试”。例外的具体比例由对应P.O.确定，本文件不外推。 | 独立电化学储能需按产品证明UP响应曲线；若采用聚合UP，部分设施可落入比例例外，但SOC、持续时间、恢复和产品专门比例仍留ES-04。 | `confirmed`一般入口/测试例外（高）；具体比例和产品细则 `unresolved` |
| ES02-GEN-006 | 储能持有人可申请成为其连接的BRP，也可委托所选BRP；BSP分配的平衡能量按BSP自身BRP或其指定BRP的顺序分配。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Arts.12、16(1)-(3)，BOE HTML §§718-724、757-770；访问2026-08-11。 | BSP容量收入与BRP偏差责任是不同结算角色。 | 后续储能收益/偏差研究需保留BSP/BRP拆分；ES-02不展开不平衡公式。 | `confirmed` / 高 |

## 3. FCR / regulación primaria（频率约束，不是储能容量市场）

| Claim ID | 规则事实 | 官方定位及有效期 | 研究解释/储能边界 | 状态/信心 |
|---|---|---|---|---|
| ES02-FCR-001 | P.O.1.5将primary定义为系统在扰动后数秒内稳定频率的物理响应；ENTSO-E要求按年度发布西班牙次年primary reserve requirement。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；P.O.条款按连接/修订规则生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.1.5 §4.1，BOE PDF pp.39-40（2024版；2025年沿用至后续修订）；访问2026-08-11。 | 这是物理频率遏制能力，不是ACE恢复或BRP不平衡价格产品。 | 对储能需核对P.O.7.1、并网代码、控制器和能量持续性；本阶段不推断。 | `confirmed` / 高 |
| ES02-FCR-002 | REE指南将primary描述为**并网发电机/调速器路径**的强制、无偿服务，由调速器自主响应；1.5%静态调差和15/30秒响应是该指南描述的技术示例。 | **S-REE-GUIDE-2024**（REE，2024-12发布，非规范性），https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/Guia_descriptiva_Ser_proveedor_servicios_de_ajuste.pdf，pp.10-11；约束性入口为**S-CNMC-2024-MP**（2024-06-06发布/2024-07-06条件生效），BOE-A-2024-11535，Art.5(1)及P.O.1.5 §4.1。 | “并网发电机/调速器路径”是对REE指南层级的研究解释，不是将指南升级为约束性规则；审阅材料未发现面向BSP竞价的FCR容量市场或容量费。 | Art.7一般储能BSP资格不足以证明独立电池可提供FCR；FCR储能资格、补偿和测试列`open-critical`。 | `confirmed`（指南表述/物理响应）/中高；储能 `unresolved` |
| ES02-FCR-003 | REE指南本身声明不具有规范价值，不能替代P.O.7.1/3.8。 | S-REE-GUIDE-2024，REE，2024-12版本；https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/Guia_descriptiva_Ser_proveedor_servicios_de_ajuste.pdf；p.4，lines 51-64；访问2026-08-11。 | FCR的强制/无偿结论引用指南用于操作说明，产品资格必须待BOE/P.O.闭环。 | 禁止把指南中的发电机要求直接外推为储能参数。 | `confirmed`层级说明 / 高 |

## 4. aFRR / regulación secundaria：已确认的容量市场

| Claim ID | 规则事实 | 官方定位及有效期 | 研究解释/储能相关性 | 状态/信心 |
|---|---|---|---|---|
| ES02-aFRR-001 | aFRR/secondary有本地“mercado de reserva de balance”；上、下方向独立竞价和分配。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、条件2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.10(1)-(2)(a)，BOE HTML §§698-705；P.O.按Resuelve/SRS/PICASSO连接日实施；访问2026-08-11。 | 这是明确的容量/备用采购和容量收入入口；不要与PICASSO能量市场混为一谈。 | 独立储能若满足aFRR habilitación，可在BSP层申报容量；100 MW BSP条件是额外门槛。 | `confirmed` / 高 |
| ES02-aFRR-002 | aFRR容量采购按D-1每日进行，覆盖供给日每个15分钟编程期（QH）。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、条件2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.10(2)(b)，BOE HTML §§703-706；P.O.7.2 §5.1，BOE PDF pp.99-100；访问2026-08-11。 | 采购频率为日 ahead reserve，产品时段为QH；不是年度/季度容量合约。 | 电池容量收入与每个QH中标状态绑定，SOC持续约束留ES-04。 | `confirmed` / 高 |
| ES02-aFRR-003 | P.O.7.2要求OS每日发布上/下reserve requirement；BSP可按每个QH、每个方向提交多个区块，字段含MW、€/MW、方向和不可分代码。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；按MARI/PICASSO连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §§5.1-5.2，BOE HTML §§2301-2330；Annex I，BOE PDF p.113；访问2026-08-11。 | 容量报价单位为MW，价格为€/MW；上、下方向不是对称单一产品。 | 储能需具备双向容量选择能力，但电池上下方向是否需同时达到特定测试值仍留ES-04。 | `confirmed` / 高 |
| ES02-aFRR-004 | OS按最低总成本、独立上/下和每个QH进行容量分配；分配结果形成独立边际价格。分配容量的MW数量为1 MW最小、1 MW粒度；无一般最大值（仅技术限制）。 | **S-CNMC-2024-11535-PO**（CNMC/BOE，2024-06-06发布；按MARI/PICASSO连接条款生效），https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf，P.O.7.2 §5.3、Annex I §§1.1-1.2，BOE PDF pp.99-100、113（PDF lines约5106-5155、5818-5833）；一般1 MW入口另见**S-CNMC-2024-MP** Art.7(4)。 | 这是可竞价容量采购、边际定价和容量费的完整证据链；能量激活价格仍属于ES-03，不与容量边际价混合。 | 申报系统最大值、技术限值、复杂报价和当前信息交换字段需在ES-04/ES-06核对。 | `confirmed` / 高 |
| ES02-aFRR-005 | 容量分配是firm commitment；BSP至少要在对应QH和方向提交不低于中标容量的aFRR能量支持报价；未提交会触发P.O.14.4支付义务。 | S-CNMC-2024-MP，CNMC，发布2024-06-06、条件2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.10(2)(c)、Art.10(4)，BOE HTML §§705-710；P.O.7.2 §§6.1、9.1，BOE PDF pp.102、106；访问2026-08-11。 | 容量收入不是“无条件的MW租金”，而是伴随能量报价义务和违约支付入口。具体支付公式属于ES-03/ES-05。 | 储能SOC/能量持续能力直接决定履约风险，但本阶段不设参数。 | `confirmed`义务/高；金额 `ES-03/05-open` |
| ES02-aFRR-006 | REE指南称容量市场结果产生每QH上/下边际reserve price并支付；能量市场在容量市场后开放，PICASSO激活。 | S-REE-GUIDE-2024，REE，2024-12版本；https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/Guia_descriptiva_Ser_proveedor_servicios_de_ajuste.pdf；pp.11-12，指南p.4说明非规范性；访问2026-08-11。约束性来源优先使用S-CNMC-2024-MP（CNMC，2024-06-06发布/2024-07-06生效）及P.O.7.2。 | 指南是流程解释，Art.10/P.O.7.2是容量市场约束性证据。 | 2025 PICASSO连接后能量层平台化不改变本地aFRR容量市场存在这一结论。 | `confirmed` / 中高 |

### aFRR 2025→2026版本边界

- 2025历史适用：CNMC 2024条件/P.O.7.2在SRS和PICASSO连接条款下运行；REE记录PICASSO于2025-06接入。容量市场是本地aFRR reserve，能量激活自连接后通过PICASSO（S-REE-PLATFORMS-2026、S-REE-GUIDE-2024 pp.11-12）。
- 截至2026-08-11：Art.7/9/10一般条件仍是本研究基线；P.O.7.2最新修订、aFRRIF后续修订和储能具体SOC/持续时间尚未在本阶段完整核对，不能转成模型参数。

## 5. mFRR / regulación terciaria：备用要求与能量报价，不是容量市场

| Claim ID | 规则事实 | 官方定位及有效期 | 研究解释/储能相关性 | 状态/信心 |
|---|---|---|---|---|
| ES02-mFRR-001 | P.O.7.3的对象是本地手动mFRR/tertiary reserve activation；OS发布次日每QH最小备用需求；不足时可通过技术约束手段补足。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；mFRR条款按MARI连接日生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§6-7，BOE PDF pp.155-156；访问2026-08-11。 | “发布备用需求”是系统运维要求，不等于BSP获得容量中标或容量费。 | 储能预认证可形成可用mFRR能力，但不能把能力本身作为收入。 | `confirmed` / 高 |
| ES02-mFRR-002 | UP每天提交上/下tertiary reserve报价，字段为每QH的MW和€/MWh能量价格；报价需随可用性更新，且在对应QH开始前25分钟截止更新。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；按MARI连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§8.1-8.2，BOE PDF pp.156-157（lines 8090-8119）；S-CNMC-2025-QH，CNMC/BOE，发布2025-03-17，https://www.boe.es/eli/es/res/2025/03/06/(12)，§§1382-1395；访问2026-08-11。 | 报价是能量激活产品（即使字段含“reserve MW”），价格单位€/MWh；没有独立€/MW容量结算字段。 | 储能需把SOC/可用功率映射到能量报价，详细策略和激活留ES-03。 | `confirmed` / 高 |
| ES02-mFRR-003 | mFRR标准产品QH分辨率，交付参数需按供应商是否同时参与aFRR/secondary及程序化/直接激活类型区分；同时参与aFRR的供应商对应5-30分钟标准范围，mFRR-only供应商适用不同产品表参数；MARI平台通过欧盟IF激活，平台故障用本地算法后备。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；按MARI连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§7、9-10，BOE PDF pp.155-159；S-ACER-mFRR-IF，ACER，2020-01-24及2022-09-30修订，https://www.acer.europa.eu/electricity/implementation-monitoring/eb；访问2026-08-11。 | 这是能量产品的交付约束，不构成容量采购周期/容量费；ES-03记录不同供应商配置的细分交付参数。 | 电池响应与能量持续要求留ES-04；本阶段只记录边界。 | `confirmed` / 高 |
| ES02-mFRR-004 | 激活mFRR能量按每QH、每类激活和方向的边际价格计价；未履约由P.O.7.3/14.4监测、可能触发支付/资格措施。 | S-CNMC-2024-11535-PO，CNMC，发布2024-06-06；按MARI连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§11-12，BOE PDF pp.159-160；S-CNMC-2024-MP，CNMC，发布2024-06-06/条件2024-07-06生效，https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.14；访问2026-08-11。 | 价格/罚则属于能量结算模块，不应被写作容量收入。 | 后续ES-03/05提取具体激活和支付公式。 | `confirmed`原则 / 高；公式 `open` |
| ES02-mFRR-005 | 2025 P.O.3.1要求tertiary reserve available offers obligatory；这是可用能力申报义务，不是另设容量市场。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；MTU15生产日期及OS通知条款控制生效），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.1 §13.2，BOE HTML §§1382-1395（PDF pp.35882-35884）；相关mFRR平台接口由**S-CNMC-2024-11535-PO** P.O.7.3 §4、§8记录。 | 强制提交不能被解释为有偿容量采购；容量费证据缺失时应保持“无独立容量市场”结论。该claim仅覆盖“必须提交可用备用”，不预断激活结算价格。 | 独立储能能否满足“available reserve”与SOC持续性留ES-04。 | `confirmed` / 高 |

## 6. RR / reservas de sustitución：2025 TERRE能量产品与停止边界

| Claim ID | 规则事实 | 官方定位及有效期 | 研究解释/储能相关性 | 状态/信心 |
|---|---|---|---|---|
| ES02-RR-001 | P.O.3.3明确其对象是RR平衡**能量**激活/交换；2025规则把RR标准产品定义为QH分辨率、15-60分钟交付期。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；OS通知/MTU15生产日期控制有关条款生效），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.3 §1、§6、Annex I，BOE PDF pp.123-126（HTML/PDF lines约5946-5965、6051-6087）；平台历史边界另见**S-ENTSOE-TERRE-2026**。 | RR产品本身是能量市场/平台，不是本地容量采购；没有独立€/MW容量费条款。 | 储能一般BSP资格不等于RR产品专门预认证。 | `confirmed` / 高 |
| ES02-RR-002 | 2025 RR标准能量报价：FAT30分钟、最小1MW、最大值无一般上限（技术限制）、交付15-60分钟、价格分辨率0.01€/MWh，按上/下方向报价。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；有关条款按MTU15生产日期及OS通知实施，2025历史适用至TERRE停止边界），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.3 Annex I.1，BOE PDF pp.125-126（lines约6051-6087；“Principales características”表）；访问2026-08-11。 | 这些是能量报价字段和交付参数，不是容量市场参数。 | 一般1MW与Art.7(4)一致；储能SOC/持续供能/资格仍留ES-04。 | `confirmed`产品参数 / 高 |
| ES02-RR-003 | RR平台保留24个activation horizons/gates；单个报价可覆盖15/30/45/60分钟并优化60分钟。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；2025历史适用至TERRE于2025-12-30停止，具体生产日/OS通知控制实施），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.3 Annex I脚注2，BOE PDF p.126（lines约6093-6095）；2025规则“Modificación del P.O.3.3”前言确认TERRE维持24 horizons；访问2026-08-11。 | “24 horizons”是TERRE平台激活频率/时域，不是日内市场24个交易窗口或容量采购时段。 | 回测或数据目录不能把24 horizons标成容量产品。 | `confirmed` / 高 |
| ES02-RR-004 | 2025 P.O.3.1 §13.1规定RR平台使用直到西班牙连续日内市场达到96次closures；这是RR停止触发条件，和24 horizons分开。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；2025历史适用至TERRE停止，具体生产日/OS通知控制实施），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.1 §13.1，BOE PDF pp.26-27（lines约1341-1361）；TERRE实际切点由**S-ENTSOE-TERRE-2026**（ENTSO-E，页面更新至2026，https://www.entsoe.eu/network_codes/eb/terre/，web §§127-151、208-229；2025-12-30停止、2026-01-01 former member）记录；访问2026-08-11。 | 96是日内市场闭市数量触发条件，不是RR容量采购次数。 | 2026替代/本地fallback未确认，不得从96条件推断后续容量机制。 | `confirmed`边界 / 高；2026路径 `open-critical` |
| ES02-RR-005 | P.O.3.3要求BSP从D-1 12:00起提交RR能量报价；H-55′为eSIOS接收截止（H为交付小时）；每UP、每方向每小时最多40个块，且平台关门前至少5分钟由OS按PHFC/不可用信息进行前置验证。 | **S-CNMC-2025-QH**（CNMC/BOE，2025-03-17发布；2025历史适用至TERRE停止，具体生产日/OS通知控制实施），https://www.boe.es/eli/es/res/2025/03/06/(12)，P.O.3.3 Annex I §§2.1-2.2，BOE PDF pp.126-127（lines约6096-6134；D-1 12:00、H-55′、40块、至少提前5分钟）；连续更新/PHFC接口同决议P.O.3.1 §13.1，HTML §§1341-1361；访问2026-08-11。 | 这是实时/能量报价关门和验证，不是容量采购关门；PM–OS技术文件仍控制价格字段校验。 | 后续ES-03可继续提取激活和未交付，ES-02不把它转为容量参数。 | `confirmed` / 高 |
| ES02-RR-006 | ENTSO-E记录REE/REN于2025-12-30约09:00-10:00 MTU停止TERRE并自2026-01-01为former member；西班牙替代机制未在本阶段找到闭环官方P.O.。 | S-ENTSOE-TERRE-2026，ENTSO-E，页面更新至2026；https://www.entsoe.eu/network_codes/eb/terre/；有效边界：2025-12-30停止、2026-01-01 former member；web §§127-151、208-229；访问2026-08-11。 | 2025研究可在12-30切点前使用TERRE RR能量规则；2026不能外推。 | 独立储能2026 RR收入/资格保持`unresolved`。 | `confirmed`切点 / 高；替代路径 `unresolved` |

## 7. SRAD：需求响应特定容量产品（条件范围）

| Claim ID | 规则事实 | 官方定位及有效期 | 研究解释/储能相关性 | 状态/信心 |
|---|---|---|---|---|
| ES02-SRAD-001 | SRAD是为tertiary up reserve不足设置的本地特定平衡产品；通过发布需求、**拍卖分配**、激活/计量和拍卖边际价补偿实现。 | S-SRAD-2025，CNMC/BOE，发布2025-11-11、2026-01-01起适用；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-22853；§§119-138、167-179；访问2026-08-11。 | 与标准mFRR不同，SRAD明确存在容量拍卖和容量收入，但法定对象是需求响应。 | 不得把标准产品storage一般BSP资格外推为SRAD资格。 | `confirmed`产品机制 / 高 |
| ES02-SRAD-002 | SRAD 在 2025 年已有年度拍卖/服务框架；CNMC 2025 背景说明 2023—2025 按年度 subastas 及保密价格上限运行，2025-11 修订主要规定后续周期。 | S-SRAD-2025，CNMC/BOE，发布2025-11-11、修订自2026-01-01起适用；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-22853；§§191-202，BOE HTML；历史适用2025-01-01—2025-12-31需按对应版本核对；访问2026-08-11。 | 2025 已有 SRAD 年度服务/拍卖框架，但不能把它作为**已确认的独立储能收入**，也不能与 aFRR D-1 容量价格混合。 | 储能资格仍未确认。 | `confirmed`历史框架 / 中高 |
| ES02-SRAD-003 | 2026修订将通常服务期改为6个月，原则上每年1月1日—6月30日及7月1日—12月31日两次拍卖；允许OS在通知/授权下调整次数。 | S-SRAD-2025，CNMC/BOE，发布2025-11-11、2026-01-01起适用；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-22853；§§215-223；S-SRAD-2026，CNMC/BOE，发布2026-05-15、2026-05-16生效；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10602；§§124-138；访问2026-08-11。 | 截至2026-08-11适用六个月框架；保密附件使具体价格、预算和容差不可从公开文本完全提取。 | 独立储能是否可按demand unit/aggregation参加仍`open-critical`。 | `confirmed`框架 / 高；storage资格 `unresolved` |
| ES02-SRAD-004 | 2026规则允许通过需求设施聚合达到1 MW SRAD最小报价：单个需求设施合同功率>1MW，或一组单设施≤1MW且总合同功率≥0.1MW（具体条件见P.O.7.5）。 | S-SRAD-2025，CNMC/BOE，发布2025-11-11、2026-01-01起适用；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-22853；§§169-174；S-SRAD-2026，CNMC/BOE，发布2026-05-15、2026-05-16生效；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10602；P.O.7.5正式文本及附件待继续核对；访问2026-08-11。 | 该门槛是需求响应聚合门槛，不是独立储能的标准BSP门槛。 | 储能以“storage”身份而非需求设施身份能否使用此路径未确认。 | `provisional`/中 |

## 8. ACER平台框架、法律层级和版本边界

| Claim ID | 规则事实 | 来源/定位 | 研究解释 |
|---|---|---|---|
| ES02-IF-001 | ACER登记aFRR、mFRR、RR、IN四个平台实施框架及其决定、实施状态：aFRR Decision 02/2020、15/2022、08/2024；mFRR 03/2020、14/2022；RR 2023修订框架；IN 13/2020、16/2022。 | S-ACER-aFRR-IF，ACER，发布2020-01-24、2022-09-30/2024-07-05修订，生效/实施截止至2024-07-24；https://www.acer.europa.eu/electricity/implementation-monitoring/eb；web §§118-133；S-ACER-mFRR-IF，ACER，发布2020-01-24、2022-09-30修订，https://www.acer.europa.eu/electricity/implementation-monitoring/eb；web §§105-116；S-ACER-RR-IF，ACER/相关NRA，2023-03-23修订批准，https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/MARKET-CODES/ELECTRICITY-BALANCING/02%20RR%20IF/Action-3a-RR-IF-Amended-proposal-approved.pdf；PDF pp.1-2、12-13；S-ACER-IN-IF，ACER，发布2020-06-24、2022-09-30修订，https://www.acer.europa.eu/electricity/implementation-monitoring/eb；web §§135-147；访问2026-08-11。 | 这些IF是欧洲跨TSO能量平台的共同方法/技术框架，不是西班牙本地容量采购证据；西班牙容量收入仍以CNMC/BOE P.O.为准。 |
| ES02-IF-002 | ACER平台页面明确标准产品能量竞价形成共同报价序列并由平台激活；平衡能量和跨区容量定价方法另有EBGL Art.30方法。 | **S-ACER-aFRR-IF**（ACER，2020-01-24发布、2022-09-30/2024-07-05修订；https://www.acer.europa.eu/electricity/implementation-monitoring/eb，web §§118-133）；**S-ACER-mFRR-IF**（ACER，2020-01-24发布、2022-09-30修订，同页§§105-116）；**S-ACER-RR-IF**（ACER/相关NRA，2023-03-23修订批准；https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/MARKET-CODES/ELECTRICITY-BALANCING/02%20RR%20IF/Action-3a-RR-IF-Amended-proposal-approved.pdf，PDF pp.1-2、12-13）；**S-ACER-IN-IF**（ACER，2020-06-24发布、2022-09-30修订；https://www.acer.europa.eu/electricity/implementation-monitoring/eb，web §§135-147）；西班牙实施为**S-CNMC-2024-MP**（CNMC，2024-06-06发布/2024-07-06生效）及**S-CNMC-2024-11535-PO**（CNMC/BOE，2024-06-06发布、按连接条款生效），https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；访问2026-08-11。 | 为避免越界，ES-02只用IF确认平台层级和版本，不展开欧洲能量激活价格。 |
| ES02-IF-003 | EUR-Lex consolidated EBGL用于可读性和修订整合；其法律效力来自原始《Regulation (EU) 2017/2195》及后续修订法规的正式公报文本。 | S-EBGL-2017，欧盟委员会/EUR-Lex，原始法规2017-11-23发布、2017-12-18生效；https://eur-lex.europa.eu/eli/reg/2017/2195；consolidated HTML相关Arts.1-2、17-22、49-55及其原始/修订链接，访问2026-08-11。 | 引用合并文本时必须保留版本、原始法规和修订文本注记，不能把网页整合文本误写为新的独立法规。 |

## 9. 2025历史期与2026-08-11基准日版本矩阵

| 模块 | 2025历史适用 | 2026-08-11基准日 | 本阶段可用于容量结论的程度 |
|---|---|---|---|
| 一般BSP/储能 | BOE-A-2024-11535条件在MARI/PICASSO切换框架下适用；Art.7/9提供储能一般入口。 | Art.7/8/9仍作为一般入口；产品专门规则需按现行P.O.复核。 | 可确认一般储能BSP、1MW、aFRR 100MW、聚合/测试入口。 |
| FCR | primary物理响应由P.O.1.5/REE指南描述为发电机强制无偿。 | 无独立储能FCR闭环证据。 | 可排除已确认储能容量市场；储能资格未决。 |
| aFRR | 本地D-1/QH上、下容量市场；PICASSO于2025-06接入，容量层仍本地。 | 本地容量市场框架仍有效；当前P.O.修订/IF后续变更需继续追踪。 | 可确认容量采购与容量收入。 |
| mFRR | MARI于2024-12接入；P.O.7.3提交可用备用能量报价，非独立容量市场。 | MARI平台/本地fallback版本需按OS公告追踪。 | 可确认“未识别独立容量市场”，能量细节留ES-03。 |
| RR | TERRE至2025-12-30；P.O.3.3为能量报价，24 horizons；96 closures为停止触发。 | TERRE停止后替代机制未确认。 | 可确认2025非容量产品及切点；不可外推2026。 |
| SRAD | 需求响应特定年度拍卖/容量费框架。 | 2026-05-16修订后通常六个月拍卖；独立储能资格仍未决。 | 可确认产品有容量收入，但对象/储能适用待ES-04。 |

## 10. ES-02未决问题交接（不得作为模型参数）

1. 独立电化学储能能否直接提供FCR/primary，及P.O.7.1/3.8测试、SOC、持续时间和补偿。
2. aFRR 100 MW条件对聚合储能的同组、代表、UP/BRP结构及2025→2026过渡适用。
3. mFRR/RR储能专门SOC、最短持续时间、恢复、能量报价和未履约支付公式（ES-03/ES-04/ES-05）。
4. TERRE停止后2026 RR替代平台、P.O.或本地fallback；不得用96 closures或mFRR规则代替。
5. SRAD需求响应法定对象是否允许独立储能以demand/storage身份参加；2026保密附件中的价格上限、预算和容差。
6. 当前P.O.7.2/7.3/3.3修订与REE公告的精确生效日、eSIOS字段和公开容量价格数据（ES-06）。
