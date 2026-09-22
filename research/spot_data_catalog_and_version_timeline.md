# ES-SP-07 西班牙现货市场数据目录与版本时间线

> 研究期：2025-01-01—2025-12-31；规则基准日：2026-08-11；访问日：2026-08-21。研究对象为西班牙大陆竞价区独立储能的日前、日内、计划、计量、偏差与结算数据。
>
> 本文件只建立官方数据入口、字段和版本的证据地图，不下载或保存 `data/raw/` 原始时序，不进行收益、预测、策略、MILP、代码或回测。尚未由官方页面/文件逐项确认的字段、时滞、历史覆盖、修订行为和权限均保留为 `open`/`provisional`。

## 1. 结论摘要与证据分层

### 1.1 可复核的官方入口

| 数据层 | 主要官方入口 | 已确认内容 | 不能据此确认的内容 |
|---|---|---|---|
| OMIE 现货市场 | OMIE “Acceso a ficheros”、市场结果页和公共文件格式说明 | 日前价格、IDA 价格/容量/计划、连续日内价格/成交/计划、曲线、部分报价和最近六年滚动公开文件入口；文件头含发行时间和数据日期 | 每个 2025 文件的完整留存、逐笔连续交易的历史修订、IDA 报价释放时滞、内部 API 限额 |
| REE/eSIOS 公共数据 | REData/eSIOS API、档案下载、市场与价格页面 | 指标和档案查询入口、按数据日期/发布日筛选、JSON/下载入口、部分平衡和价格展示 | 每个指标的 ID、单位、时区、刷新/发布时滞、revision、2025 全年覆盖 |
| ENTSO-E Transparency | Transparency Platform Web API/数据视图 | 日前价格、日前商业交换计划、物理潮流以及平衡数据项目的标准数据项和 API 入口；数据项用 A44、A09、A11 等官方代码区分 | Spain bidding-zone/EIC 与 OMIE/REE 单位的完整 crosswalk、API token/限额、重发布规则和所有 2025 历史归档 |
| REE 计划/计量/结算 | BOE/MITECO P.O.10.x、P.O.14.x、REE 结算入口/指南 | PDBF、PDVP、PDVD、PHF/PHFC 的制度接口；15 分钟计量、储能出入方向、D+1/M+1 流程；BRP 明细结算文件的私有边界 | 具体项目的字段消息、公开下载权限、版本号、修订标记、BRP 账户数据历史可得性 |

### 1.2 三层内容分离

* **规则事实（F）**：BOE/CNMC/MITECO 或官方数据文档直接说明的入口、字段、时段、生效日期和访问边界。
* **研究解释（I）**：将 OMIE 成交结果、REE 计划、计量/结算和 ENTSO-E 跨区数据串成可复核工作流；不替代规则。
* **建模假设（A）**：本阶段不新增建模假设。项目今后若要把公开文件作为输入，必须另行登记时间截面、缺失处理、单位换算和版本选择。

## 2. 数据集目录

“已确认字段”只表示官方文件或页面明确列出；“候选字段”表示研究上需要但尚未从对应接口逐项核验，不得直接写入模型或收益公式。

| data_id / 提供方 | 数据集和字段范围 | 分辨率、时间、单位和方向 | 发布、权限、历史覆盖 | 2025适用性与证据状态 |
|---|---|---|---|---|
| **D-SP-OMIE-DA** / OMIE | 日前价格、成交量、聚合供需曲线、跨区容量/占用、PDBC/PDBF 相关公开计划；候选：market period、Spain zone、price、matched energy、capacity、offer/order identifiers | **2025-01-01—03-17：**小时日前版本，按 `S-SP-BOE-2024-RULES`；**2025-03-18—09-30：**`S-SP-BOE-2025-RULES` 已生效并带来新日前报价类型，但日前 MTU 仍为小时；**2025-10-01 交付起：**日前 MTU15，按 `S-SP-OMIE-MTU15-DA-2025`。价格 EUR/MWh，能量通常 MWh/GWh，容量/功率 MW；买/卖方向需保留为独立字段 | `file-access-list`列出价格、程序、曲线、报价、容量和最近文件；格式文件头含发行时间和数据日期；公共文件库覆盖最近六年滚动，早期文件需通过 OMIE assistance portal；日前报价文件在90天保密期后发布。S-SP-OMIE-FILES-2026；S-SP-OMIE-FORMATS-2024；S-SP-BOE-2024-RULES；S-SP-BOE-2025-RULES；S-SP-OMIE-MTU15-DA-2025 | **confirmed入口/三段版本边界；公开历史逐文件完整性和修订 open**。2025 MTU15 不得回填至 10月1日前；2025-03-18 前后须保留 `rule_version` |
| **D-SP-OMIE-IDA** / OMIE | 三场 IDA 的价格、成交量、跨区容量/占用、累计/增量计划、订单头/详情；候选：auction/session、delivery period、accepted volume、price、cross-zonal capacity | 2025-03-18 生产运行切换至季度小时（交付从2025-03-19）；2025-01-01—03-17 使用前一版本；价格 EUR/MWh，成交/计划 MWh，容量 MW；具体 session horizon 由规则版本确定 | OMIE 文件清单列出 IDA 价格、计划、曲线、报价和容量；格式文档给出 2024-06-13 后 IDA 的历史解释和文件结构；IDA 报价具体保密/释放时滞未由该文件确认，不能套用日前90天。S-SP-BOE-2024-IDAS；S-SP-BOE-2025-RULES；S-SP-OMIE-FILES-2026；S-SP-OMIE-FORMATS-2024 | **confirmed入口/2025边界；IDA逐文件归档、修订和报价公开时点 open** |
| **D-SP-OMIE-CONT** / OMIE | 连续日内按合同的最小/最大/加权平均价、成交交易、每轮价格/计划、最终计划、容量/占用；候选：trade timestamp、round、buy/sell、volume、price、order status | 2025-01-01—03-17 按 `S-SP-BOE-2024-IDAS`/前一连续市场版本；2025-03-18 起按 `S-SP-BOE-2025-RULES` 的季度小时产品衔接；合同和轮次不等于固定15分钟时间序列，必须保留 period 与 round；价格 EUR/MWh，成交/计划 MWh，容量 MW；方向为买入/卖出，不自行正负化 | OMIE 清单列出连续市场价格、交易、计划和容量文件；公共结果页提供按合同最小/最大/加权均价等视图；连续订单逐笔版本/撤单/更正规则未逐项核验。S-SP-OMIE-FILES-2026；S-SP-OMIE-MARKET-2026；S-SP-OMIE-FORMATS-2024；S-SP-BOE-2024-IDAS；S-SP-BOE-2025-RULES | **confirmed入口/分段规则标签；逐笔历史、修订、可见权限 open** |
| **D-SP-REE-PLAN** / REE/eSIOS | OMIE 结果向 REE 的计划链：PDBC、PDBF、PDVP、PDVD、PHF/PHFC；候选：UP/UF、UO、BRP/PM、revision/version、commercial/physical schedule | 计划必须附 `rule_version`：日前/日内 2025-01-01—03-17、2025-03-18—09-30、2025-10-01 起分别按相应市场规则；同时按 ISP15 结算/计量版本切片。功率 MW、能量 MWh；计划方向按注入/取电及项目 UP 规则保存，不能只用单一有符号功率 | BOE 规则确认计划序列和信息交换；具体消息文件、公开/私有边界和历史版本由 REE/参与者接口决定。S-SP-BOE-2024-RULES；S-SP-BOE-2025-RULES Rules 35–36、58.4；S-SP-PO31-2024-STORAGE；S-REE-DOWNLOAD-2026 | **confirmed制度链/版本切片要求；公开字段、版本 crosswalk 和2025覆盖 open-critical** |
| **D-SP-REE-BAL** / REE/eSIOS | 平衡能量/激活、aFRR/mFRR/RR、IGCC/不平衡价格和相关公开指标；候选：activation volume、direction、CBMP/local price、BSP/UP、platform/mRID | 产品按规则可能为15分钟交付/结算；单位通常 MWh、MW、EUR/MWh 或 EUR/MW，但每个 indicator 的单位和时区必须逐项读取元数据；方向保留上调/下调原值 | eSIOS 文档确认 indicators/archives 查询、按 `datos` 或 `publicacion` 日期筛选及下载/JSON 路径；REE 结算页面的 BRP 明细为权限数据。S-REE-REData-API-2026；S-eSIOS-API-IND-2026；S-REE-DATA-BAL-2026；S-REE-LIQ-ACCESS-2026 | **入口 confirmed；指标 ID、延迟、历史/修订和公开权限 open**。不得把平台公开价格当成储能已获得的结算收入 |
| **D-SP-METER** / REE/MITECO/SIMEL | 储能 Activa saliente（出/注入）、Activa entrante（入/取电）、reactive；QH best energy、有效/估计/无效和 incidence 候选字段 | 2025-05-01 起 P.O.10.x 的 ISP15 计量与储能双向方向；kWh/MWh、无功按 kvarh/Mvarh；出/入分别记录，不用符号替代；Europe/Madrid 本地日历和原始 offset 需保留 | P.O.10.5 明确最佳值最大24小时、D+1/M+1 发布和缺失估计分支；SIMEL 字段和公开历史不等于公共 API。S-MITECO-2025-ISP §§1352–1358、1531–1543、1929–1932、1998–2000、2205–2213、2255–2261 | **规则事实 confirmed；具体 API、公开权限、缺失标志和重发布 open**。2025-01—04 需使用当时适用的计量版本，不能按5月规则回填 |
| **D-SP-BRP-SETTLE** / REE | `reganeu`/`reganecuQH`、`p48cierre`、`rp48preccierre`、`prdv*`、A1–A5/C1–C5 等结算/偏差文件；候选：MEDBC、POSFIN、AJUDSV、DESV、settlement stage、revision | ISP15 后按15分钟；MWh、EUR/MWh、EUR；P.O.14.4 定义方向和 CET/CEST 基础；金额正负号必须读取版本/字段定义，不能凭名称猜测 | REE 指南列出文件作用和字段角色，但 BRP ZIP 仅参与者权限可访问；M+1/后续结算批次可能产生修订。S-REE-LIQ-GUIDE-2024 pp.4–10、16–18；S-REE-LIQ-ACCESS-2026 §§71–80；S-CNMC-2024-ISP15；S-CNMC-2025-QH；S-CNMC-2025-VOLTAGE-13076 | **规则/私有边界 confirmed；公开历史、版本号、修订和精确字段 crosswalk open-critical**。不得用事后文件作为实时决策输入 |
| **D-SP-ENTSOE-DA** / ENTSO-E Transparency | 日前价格（A44）、日前商业交换计划（A09）、物理潮流（A11）、跨区容量相关数据；候选：bidding zone EIC、time interval、resolution、direction、published/created time | Transparency 数据可按 UTC 或 CET/CEST 视图查询；价格 EUR/MWh，商业交换/潮流通常 MW/MWh，方向为 import/export；实际数据项分辨率和时标按请求返回 | 官方 Web API 数据提取指南列出 A44/A09/A11 和 TimeInterval；API 访问和 token/配额须按最新平台账户规则核验；旧页面明确 legacy 数据视图可能不再更新。S-ENTSOE-TP-API-2026；S-ENTSOE-TP-LIST-2022 | **数据项/入口 confirmed；西班牙 zone/EIC crosswalk、2025归档、重发布和权限 open**。ENTSO-E 仅作跨区/独立核验，不替代 OMIE 成交结算 |
| **D-SP-ENTSOE-BAL** / ENTSO-E Transparency/EDI | 平衡激活、备用/分配结果、跨TSO交换等欧洲层消息；候选：mRID、bid/activation/allocation result、direction、volume、price | 按平台产品/消息 schema；时间通常需以 UTC 或 message TimeInterval 解释，QH/MTU 不能从入口统一假设；单位/方向逐 message 核验 | EDI library/Transparency 数据项为 schema 和入口，不等于西班牙参与者结算文件；MARI/PICASSO/TERRE 版本和归档需与 REE 本地文件交叉核对。S-ENTSOE-EDI-2024；S-ENTSOE-TP-API-2026；S-REE-PLATFORMS-2026 | **schema/平台入口 confirmed；逐消息字段、归档、mRID crosswalk、修订 open**。TERRE 截止2025-12-30后不得外推 |
| **D-SP-STRUCT** / OMIE/REE/ENTSO-E | 参与者、UP/UO/UF、BRP/PM/代表、EIC、bidding-zone、platform membership 的结构关系；候选：有效起止日、版本、关联类型 | 事件/结构数据，无固定分辨率；代码和日期均为字符串/标识，不做能量单位转换 | OMIE 规则和 P.O.14.2 规定部分结构字段；公开门户不保证逐项目历史账户可见。S-SP-BOE-2025-RULES Rule 4、58.4；S-SP-PO31-2024-STORAGE；S-CNMC-2024-11535-PO；S-ENTSOE-TP-API-2026 | **一般规则 confirmed；独立储能项目级账户和跨机构代码映射 open-critical** |

## 3. 字段、时区、分辨率、单位与方向

### 3.1 时间和夏令时

1. **内部统一表示**：以 `Europe/Madrid` 本地日期时间、原始 UTC offset、市场交付日、period/quarter-hour 编号和（如有）UTC 时间戳同时保存。OMIE 公共文件格式说明把下载小时标为 CET；ENTSO-E 数据视图提供 `UTC` 与 `CET_CEST` 选择；REE API 示例同时出现本地 `datetime` 与 `datetime_utc`。这证明存在多个展示时标，但没有证明每个指标都采用同一时标。
2. **DST 不确定性**：欧洲夏令时的重复/缺失本地小时、OMIE 文件的 H 编号和 eSIOS 指标的 `datetime` 如何逐项映射，公开入口尚未完成字段级验证。不得把本地“24小时”简单当成固定24个记录；实际抓取时需按 offset/UTC 去重并保留原始 period。
3. **15分钟边界**：日内季度小时从 2025-03-18 生产运行（交付从 2025-03-19），日前 MTU15 从 2025-10-01 交付（首场相关拍卖为 2025-09-30）；ISP15 结算/计量还要按 2024-12-01 与 2025-05-01 的规则切片。市场时段和结算时段不能仅凭文件名合并。

### 3.2 单位和方向

| 内容 | 规则/官方页面可支持的表示 | 研究处理边界 |
|---|---|---|
| 价格 | 现货/平衡能量通常 EUR/MWh；容量可能 EUR/MW 或 EUR/MW·时段；OMIE 格式文档的价格示例以 EUR/MWh 表示 | 每个数据文件保留原始单位和小数/空值；未读到单位元数据时标 `open`，不得硬转 |
| 能量/成交量 | MWh 或公共统计中的 GWh；计划和计量按 MWh/kWh | 先按文件字段/标题识别，再转换；不要把 MW 功率直接当 MWh 能量 |
| 功率/容量 | MW；跨区容量/占用和可用功率按独立字段保存 | 不把容量值当成交量或储能可用功率 |
| 储能方向 | MITECO P.O.10.5 明确 `Activa saliente`（向系统流出/注入）和 `Activa entrante`（从系统流入/取电）并存 | 方向保留两个字段；是否采用正负号由具体接口定义，不能自行用负号替代 |
| 交易方向 | OMIE 买/卖、REE 上调/下调、ENTSO-E import/export | 各层方向不直接等同：例如上调不必然等于储能放电，需结合计划和运行状态 |

### 3.3 标识与关联

需要优先保留 `delivery_date`、`period/MTU`、`session/round`、`publication_time`、`issue_time`、`data_date`、`unit/UP/UO/UF`、`BRP/PM`、`EIC`、`mRID`、`platform`、`rule_version` 和 `settlement_stage`。目前没有官方证据证明 OMIE 的 offer/order ID、REE 的 UP/UF、ENTSO-E 的 mRID/EIC 可以在公开数据中一一关联，因此跨机构关联为 **open-critical**，不能用名称或时间近似替代。

## 4. 发布时滞、重发布、历史覆盖与权限

### 4.1 已确认的边界

* OMIE 公共文件入口声明公开仓库覆盖最近六年滚动；更早文件需通过 assistance portal。该说明不是对每个数据集逐日完整性的保证。
* OMIE 公共文件格式规定文件头包括来源、发行日期/时间、数据日期和报告名称；因此可以记录 `issued_at` 与 `data_date`，但这不是 `revision_number` 或更正标志。
* OMIE 日前报价头和详情文件在 90 天保密期后发布；这只适用于该报价文件说明，不能自动扩展到 IDA 或连续日内逐笔订单。
* eSIOS API 文档提供 archive 按 `start_date`、`end_date`、`date_type=datos/publicacion` 查询，以及 indicator 按日期范围、小时/15分钟等聚合的入口；官方文档未在入口页固定每个指标的发布延迟、保留年限、版本号或配额。
* P.O.10.5 明确储能计量的最佳值最大 24 小时、D+1/M+1 发布和特定缺失/估计分支；这些是计量/结算时序，不是日前/日内决策数据。
* REE 说明 BRP 结算 ZIP 在参与者权限区域；`reganeu/reganecuQH` 等详细账户文件不能假设公开可取。公开汇总也不能重建某一储能项目的结算。
* ENTSO-E 的官方数据提取指南按数据项代码和 `TimeInterval` 定义查询依赖；平台旧视图明确标识为 legacy 时，应保留数据来源版本，不能把当前页面回写为历史接口版本。

### 4.2 不得混用的公开与私有数据

| 用途 | 可作为候选输入 | 只能作为事后结算/核验 |
|---|---|---|
| 日前/日内交易决策 | 在决策时间已发布的 OMIE 价格、容量、市场结果、已知计划和当时可取得的 REE/eSIOS 公共指标；必须保存请求/发布时间 | 90天后才公开的日前订单详情、未来修订后的价格/计划、结算后才形成的偏差/激活结果 |
| 执行和偏差核验 | 交割前已发布的最终计划（如参与者权限可取得）及实时公开信息 | P.O.10.5 的 M+1 计量闭算、BRP `p48cierre`/`reganecuQH`、后续 objection/recalculation |
| 历史研究 | 公开历史价格、容量、聚合量；应保留 `retrieved_at`、`issued_at`、`data_date`、规则版本和原始单位 | 事后才释放的报价/交易明细、重发布版本和私有结算文件只能标记为 ex-post，不能伪装成实时可知 |

**研究解释**：对任意回溯或未来模拟，决策输入和事后结算输入至少要分两个数据层保存。做不到逐项证明“在决策时已公开”的字段，不应回填到决策数据集。

## 5. 2025 规则与数据版本时间线

| 日期/时段 | 事件 | 数据目录影响 | 状态/证据 |
|---|---|---|---|
| 2024-12-01 | P.O.14.1/14.4 ISP15 版本开始适用 | 2025年初偏差/结算字段按15分钟版本分段；不能用旧小时结算字段覆盖全年 | confirmed；S-CNMC-2024-ISP15 |
| 2024-12（月份） | 西班牙接入 MARI | 2025 mFRR 数据需 local/MARI 及 fallback 版本标记 | REE 页面确认月份，具体首个有效时段 open；S-REE-PLATFORMS-2026 |
| 2025-03-17 | `S-CNMC-2025-QH` 发布，P.O.3.1/3.3/14.4 等程序修订；其生效与 OMIE MTU15 生产日期绑定 | 将 P.O.14.4 结算、平衡激活和计划字段标记为“2025-03-17 发布、具体生产生效日 open”；不得从 1 月 1 日回填 2025-5342 | confirmed publication/effective linkage；S-CNMC-2025-QH |
| 2025-03-18（交付从03-19） | OMIE 日内市场季度小时生产运行 | IDA/连续日内数据从此边界按 QH/新产品切片 | confirmed；S-SP-OMIE-QH-ID-2025、S-SP-BOE-2025-RULES |
| 2025-03-18 | `S-SP-BOE-2025-RULES` 日前/日内规则开始按 OMIE 生产切片适用；日前仍按小时，日内进入季度小时产品 | 日前数据使用 `S-SP-BOE-2025-RULES` 但保留 MTU60；日内/连续数据按 QH；三段 `rule_version` 必须写入数据目录 | confirmed for rule slice; daily MTU15 remains 2025-10-01；S-SP-BOE-2025-RULES |
| 2025-05-01 | MITECO P.O.10.x ISP15 计量规则生效 | 储能出/入计量、最佳值、缺失估计、D+1/M+1 数据流程切换；2025-01—04不能直接套用 | confirmed；S-MITECO-2025-ISP |
| 2025-06-26 | `S-CNMC-2025-VOLTAGE-13076` 发布，修改含 P.O.14.4 的电压控制相关条款；部分元素由 Resuelve Segundo 延期，具体结算适用日仍 open | 将 2025-06-26 后的 BRP/结算数据标注该版本边界；不得假设所有 P.O.14.4 修改同日生效，须保留元素级 effective/open 标签 | confirmed publication; element-specific effective date open；S-CNMC-2025-VOLTAGE-13076 |
| 2025-06（月份） | 西班牙接入 PICASSO | aFRR 能量数据需 local/SRS→PICASSO 版本标记；具体首个有效 MTU open | REE 页面确认月份，具体日 open；S-REE-PLATFORMS-2026 |
| 2025-10-01（首场拍卖 09-30） | OMIE 日前 MTU15 生产运行 | 日前价格/成交/计划从交付日切换为96个15分钟时段；此前不可回填 | confirmed；S-SP-OMIE-MTU15-DA-2025 |
| 2025-12-30 约09:00—10:00 MTU | 西班牙/葡萄牙停止 TERRE/LIBRA，成为 former member | RR 历史目录在该 MTU 截断；最后归档标识和重发布未确认 | stop confirmed；archive/replacement open-critical；S-ENTSOE-TERRE-2026 |
| 2026-01-01 | TERRE former-member 状态 | 2026替代机制和数据入口不能由2025 TERRE外推 | confirmed status；replacement open-critical |
| 2026-08-11 | 规则基准日 | 只采用此日前已发布/适用的版本；2026未来规则保留 future 状态 | project baseline |
| 2026-09-01 | 2026实时信息修订生效（基准日之后） | 新实时字段/质量门槛不得回填2025或2026-08-11；需单独版本标签 | future-effective；S-CNMC-2026-RT |

## 6. 数据工作流与可复现性要求（研究解释）

```text
OMIE 已发布市场结果/价格/容量
            │ 交割前可见的版本快照
            ▼
    现货决策输入层（保留 issued_at、data_date、rule_version）
            │
            ├── 交割前/实时：可取得的计划与公共系统信息
            ▼
REE 计划/计量/平衡数据 ──► BRP/储能事后结算层（M+1、A/C批次、私有文件）
            │
            └── ENTSO-E 跨区/平台数据：用于独立核验，保留 UTC、EIC、mRID 和 schema 版本
```

最低元数据字段：`source_id`、`url`、`accessed_at`、`published_at/issued_at`、`data_date`、`retrieved_at`、`rule_version`、`platform_version`、`resolution`、`timezone/utc_offset`、`unit`、`direction`、`revision/republication`、`access_scope`。若某字段没有官方值，记录 `unknown/open`，不以推测补齐。

## 7. 未决问题（ES-SP-07）

| ID | 问题 | 当前边界 | 优先级 |
|---|---|---|---|
| ES-SP-07-Q06 | OMIE 日前、IDA、连续日内公开文件是否对每个 2025 交付日完整留存？文件缺失、停牌、解耦、撤单和后续更正如何编码？ | 入口和最近六年滚动声明已确认；逐文件抽样和历史下载尚未执行 | open-critical |
| ES-SP-07-Q07 | OMIE 的 issued_at、data_date、版本/更正字段能否区分实时可知值和后来重发布值？ | 文件头有发行时间/数据日期；revisionNumber/更正标志未在格式说明中确认 | open-critical |
| ES-SP-07-Q08 | REE/eSIOS 各个平衡/不平衡 indicator ID、单位、15分钟/小时分辨率、时区、刷新时滞、API key/配额和2025覆盖是什么？ | API 路由、日期过滤和 token 入口 confirmed；逐指标元数据未闭合 | open-critical |
| ES-SP-07-Q09 | REE 公开计划/激活/计量文件与 BRP 私有结算 ZIP 的字段、版本号、修订标志如何一一映射？ | 规则链和私有边界 confirmed；公开文件与项目账户 crosswalk 未确认 | open-critical |
| ES-SP-07-Q10 | ENTSO-E Spain bidding-zone/EIC、OMIE zone、REE UP/UF 和 platform mRID 是否有官方交叉表？ | ENTSO-E 数据项/API 入口 confirmed；跨机构代码映射未闭合 | open-critical |
| ES-SP-07-Q11 | CET/CEST 的 DST 重复/缺失时段、UTC offset 与 OMIE H/period、REE QH/eSIOS datetime 如何统一？ | 官方入口分别支持 CET/CEST、UTC 或本地 datetime；指标级行为未逐项验证 | open |
| ES-SP-07-Q12 | 2025 MARI/PICASSO 的具体接入日、首个有效 MTU、fallback/重发布文件如何识别？ | REE 只确认 2024-12/2025-06 月份边界；精确日和数据文件 ID open | open-critical |
| ES-SP-07-Q13 | 2025-12-30 TERRE 最后 MTU 的 REE/eSIOS 归档标识、保留期和2026替代数据入口是什么？ | ENTSO-E 停止时段 confirmed；归档和替代机制未闭合 | open-critical |
| ES-SP-07-Q14 | OMIE 90天报价保密期是否同样适用于 IDA/连续逐笔订单，历史文件的撤单/修订如何表示？ | 日前报价文件90天规则 confirmed；IDAs/连续市场适用范围 open | open |
| ES-SP-07-Q15 | M+1计量/BRP结算等事后数据是否被错误地用于决策时点回测？ | 项目原则要求分层；具体文件级时间戳和访问权限仍需核验 | open-critical |

## 8. 阶段结论

* 已建立 OMIE、REE/eSIOS、ENTSO-E Transparency、REE/MITECO 计量和 BRP 结算的第一方入口清单，覆盖价格、成交量、订单/交易、跨区容量、计划、激活、计量、偏差和结算数据。
* 已把 2025-03-18 日内 QH、2025-05-01 ISP15 计量、2025-10-01 日前 MTU15、MARI/PICASSO 月份边界和 2025-12-30 TERRE 截止点写入版本标签；精确接入日/文件版本仍标 open。
* 已明确公开决策输入与事后结算/私有输入的边界。任何未证明在决策时点已发布的数据，不能写入决策数据集。
* 本阶段没有新增建模假设，没有下载/覆盖原始数据，也没有修改 `project/`、`model/`、`src/`、`tests/` 或 `outputs/`。
