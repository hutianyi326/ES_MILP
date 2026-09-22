# ES-01/ES-02/ES-03 未解决问题与版本风险登记

> 仅登记范围、版本和证据缺口；不得把以下项目当作规则事实或模型假设。责任模块按西班牙任务计划分配，主线程在 ES-G1 审核时决定是否进入后续阶段。

## A. 2025→2026 规则版本与平台边界

| ID | 问题 | 当前证据 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES-01-Q01 | 2025 年每个 P.O.（7.1/7.2/7.3/3.3/14.4）在年初和平台连接日实际有效版本、替代关系及生效日是否完整？ | CNMC 2024-11535 Resuelve（P.O. provisions tied to SRS/MARI/PICASSO connection）；REE says MARI Dec-2024/PICASSO Jun-2025 | 年内参数引用可能错用旧版本 | ES-02/03/05 | `open` |
| ES-01-Q02 | TERRE/LIBRA 2025-12-30 停止后，西班牙 2026 RR/Replacement Reserve 是否由新平台、本地产品或 96 ID closures 替代？ | **S-ENTSOE-TERRE-2026** web §§127-151, 208-229确认REE/REN在2025-12-30约09:00–10:00 MTU停止；**S-CNMC-2025-QH** P.O.3.1 §13.1仅写“直到96闭市” | 2026 RR 交易/激活/结算不能从 2025 规则外推 | ES-03/05/06 + 主线程争议 | `open-critical` |
| ES-01-Q03 | REE 是否发布了 2026 年 RR replacement P.O./fallback 或 TERRE closure notice？ | **S-REE-PLATFORMS-2026**当前页面（访问2026-08-11）仅列IGCC/MARI/PICASSO入口；**S-ENTSOE-TERRE-2026**记录平台停止；尚未找到对应REE/BOE有效P.O. | 可能存在未索引的一方文件；在闭环前不得建模 | ES-03/06 | `open-critical` |
| ES-01-Q04 | PICASSO 2025-06 和 MARI 2024-12 的具体连接日、过渡期 local algorithm 何时停止？ | **S-REE-PLATFORMS-2026**仅提供月份；**S-CNMC-2024-11535-PO** P.O.7.2 §8、P.O.7.3 §4要求OS网页通知具体切换日并保留fallback | 平台激活数据和版本切点 | ES-03 | `open` |
| ES-01-Q05 | 2025 年 15 分钟 ISP 的实际商业运行日与 P.O.10.5 计量全量覆盖日是否同为 2025-05-01，还是有分阶段实施？ | BOE-2025-6693 Resuelve Segundo：次月首日生效；前言记载 2024-03-01 已用于 RR/tertiary verification | 结算回测的时间边界 | ES-05/06 | `open` |

## B. 产品对应和独立储能准入

| ID | 问题 | 当前证据 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES-01-Q06 | 独立电化学储能能否作为 FCR/regulated primary BSP，适用 P.O.7.1、并网代码和测试是什么？ | CNMC 2024 Art.5 lists FCR; REE guide says primary is mandatory/non-remunerated generator response; no storage-specific proof found | 不能将 FCR 作为储能收入产品 | ES-04 | `open-critical` |
| ES-01-Q07 | REE guide/FAQ 的“storage可参加 aFRR/mFRR/RR 且≥1 MW”在 2025 各产品 P.O. 中是否有同一法律效力？ | BOE-A-2024-11535 Arts.7(1)(c), 7(4), 9(2)-(4)绑定确认储能BSP、一般1 MW、遥测/控制中心/测试；产品专门参数仍在后续P.O. | 一般资格与产品资格必须分层 | ES-04 | `resolved-general; product-specific-open` |
| ES-01-Q08 | aFRR BSP 100 MW 是单一 BSP 总和、上/下方向合计，还是当前版本已修改？ | BOE-A-2024-11535 Art.7(5)明确“suma de reserva habilitada a subir y a bajar” | 储能聚合规模和收益门槛 | ES-02/04 | `resolved-by-ES-02; transition-open` |
| ES-01-Q09 | storage 在 UP/UF、发电/负荷双模式、代表/BRP 安排上是否必须拆分注入和取电计量？ | CNMC 2024 Art.16 treats storage connection and both directions; P.O.10.x measurement rules | 双向 SOC/偏差计算和计量口径 | ES-04/05 | `open` |
| ES-01-Q10 | 储能参与 mFRR/aFRR/RR 的 SOC、能量持续时间、恢复/容量预留是否在 P.O.3.8/7.2/7.3/3.3 或控制中心规范中规定？ | 当前 ES-01 只定位入口，未提取参数 | 直接决定可交付容量和履约罚则 | ES-03/04 | `open-critical` |
| ES-01-Q11 | SRAD（P.O.7.5）需求响应产品是否接受独立储能，尤其以“installation de demanda”或 storage mode 报名？ | BOE-2025-22853 §§321-332 定义 demand/SRAD；REE FAQ仅确认 storage参加标准aFRR/mFRR | 不得把 SRAD 当储能产品 | ES-04/05 | `open-critical` |
| ES-01-Q12 | 聚合限制（同一 titular/representación、同组企业、地理/电气区域）在 2025/2026 对 storage 是否变化？ | CNMC 2024 Art.2/Art.5; REE guide; P.O.3.1 Annex II entry | 聚合可行性和最小规模 | ES-04 | `open` |

## C. 平衡能量、结算和履约证据缺口

| ID | 问题 | 当前证据 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES-01-Q13 | 2025 mFRR/aFRR/RR 的报价关门、分辨率、方向、local fallback 条件是否与当前 P.O. 逐项一致？ | ES-03已确认aFRR（FAT5、D-1首版/25min更新）、mFRR（FAT12.5、23:00前次日可用备用/25min更新）、RR（FAT30、15–60min、24 horizons、D-1 12:00、H-55′、40块及前置校验）；PM–OS细粒度字段和当前版本变更仍待ES-06 | 不能提前写入策略 | ES-03/04/05 | `partially-resolved; PM-OS-detail-open` |
| ES-01-Q14 | 2025 aFRR/mFRR 价格是本地边际价还是欧洲平台边际价，过渡日如何切换？ | ES-03确认本地aFRR按P.O.7.2 §9.2形成周期边际价、PICASSO连接后由平台形成；mFRR按P.O.7.3 §4、§9走MARI并保留local fallback；逐日切换仍以OS通知为准 | 平衡能量收益序列版本断裂 | ES-03/05 | `partially-resolved; cutover-open` |
| ES-01-Q15 | 未交付、可用率、性能偏差、资格暂停的具体公式和宽限期？ | ES-03已登记Art.14、P.O.7.2/P.O.7.3/P.O.14.4的监测、支付和资格接口；系数、宽限期、恢复测试及储能SOC仍未提取 | 履约罚则、储能风险 | ES-04/05 | `open-critical` |
| ES-01-Q16 | BRP 偏差结算是单价还是双价，2025 的 ratio/price cap/方向规则及储能双向 netting？ | ES-05 已确认核心单/双价、2%阈值、PBALSUB/PBALBAJ 和 DESV 方向公式；版本切片、价格上限/下限、公开字段及储能双向 UP 仍需 ES-06/后续核对 | 核心规则已确认；版本/数据/储能细节仍未决 | ES-05/06 | `partially-resolved; version/data/storage-open` |
| ES-01-Q17 | 2025 计量使用 15-min meter 的有效日期、缺失值替代和修订结算流程？ | BOE-2025-6693 §§60-67, 90-110；P.O.10.x annexes；ES-05 已确认 2025-05-01 计量生效、≤24h 最佳值、M+11 闭算和120天更正窗口 | 计量接口核心规则已确认，回测修订字段仍未闭合 | ES-05/06 | `partially-resolved; API/revision-open` |

## D. 官方数据可得性

| ID | 问题 | 当前证据 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES-01-Q18 | REE/eSIOS 2025 数据是否可按 15-min 下载平衡容量、aFRR/mFRR/RR 能量、激活量和价格？ | **S-REE-DATA-BAL-2026**列出aFRR/mFRR/RR/IGCC类别；**S-ENTSOE-EDI-2024**列出平台激活/报价schema；字段与历史覆盖仍未验证 | 数据目录字段/分辨率未闭合 | ES-06 | `open-critical` |
| ES-01-Q19 | 数据门户的时区、CET/CEST 夏令时、单位（MW/MWh/GWh, €/MWh）、发布延迟、revisionNumber 和修订策略？ | ES-05 已从 2024-20995 P.O.14.4 §2.3 与 2025-5342 P.O.3.1 §3 定位 CET/CEST 规则；REE/ENTSO-E 仍仅提供数据入口，字段、延迟和修订策略待 ES-06 | 时间口径已定位，数据可复现性仍未闭合 | ES-05/06 | `partially-resolved; API/revision-open` |
| ES-01-Q20 | 2025 TERRE RR 数据在平台停止后是否仍在 REE 归档/API，且如何标识 2025-12-30 最后运行时段？ | **S-ENTSOE-TERRE-2026**确认停止MTU；**S-REE-DATA-BAL-2026**仅提供RR数据入口，归档字段/最后MTU标识待ES-06验证 | 历史回测缺口 | ES-06 | `open-critical` |
| ES-01-Q21 | BSP/BRP/UP/UF 的公开参与者和聚合关系可否按日期提取？ | CNMC 2024 P.O.14.2 data fields pp.195-196; REE eSIOS structural data | 独立储能可观测性与聚合分析 | ES-04/06 | `open` |

## E. ES-02 已关闭/保留的问题边界

| ID | ES-02结论 | 证据定位 | 后续状态 |
|---|---|---|---|
| ES-02-Q01 | 储能持有人可在满足服务专门要求后成为BSP；一般UP/BSP报价能力门槛为1 MW；aFRR BSP的上、下方向已 habilitado reserve 合计至少100 MW。 | S-CNMC-2024-MP Arts.7(1)(c), 7(4)-(5), 8-9；BOE HTML §§653-669, 676-701 | `closed-general; product qualification ES-04` |
| ES-02-Q02 | 西班牙存在可竞价并支付容量费的本地aFRR reserve market；上/下独立、D-1每日、QH产品、边际容量价格；容量中标带来至少等量aFRR能量支持报价义务及不履约支付入口。 | S-CNMC-2024-MP Art.10; P.O.7.2 §§5.1-5.3, 9.1; BOE PDF pp.99-106 | `closed-capacity; energy/penalty details ES-03/05` |
| ES-02-Q03 | FCR/primary在西班牙仍是并网发电机强制且无偿的物理频率响应；不应写为直接ACE恢复或储能容量市场。独立储能FCR资格未确认。 | S-REE-GUIDE-2024 pp.10-11; S-CNMC-2024-MP Art.5; P.O.1.5 §4.1 | `closed-general; storage FCR ES-04-open-critical` |
| ES-02-Q04 | mFRR/P.O.7.3和RR/P.O.3.3在已审版本中均以可用备用/能量报价、激活和能量结算为核心，未识别独立BSP容量采购或容量费；不能把预认证能力或reserve requirement当容量中标收入。 | S-CNMC-2024-11535-PO pp.155-160; S-CNMC-2025-QH P.O.3.3 pp.123-127 | `closed-negative; ES-03 energy details` |
| ES-02-Q05 | RR的24个activation horizons（平台小时频率、可优化60分钟）与连续日内市场96次closures触发条件分开；TERRE停止日为2025-12-30，2026替代路径未确认。 | S-CNMC-2025-QH P.O.3.3 Annex I pp.125-126; Art.13.1 pp.26-27; S-ENTSOE-TERRE-2026 | `closed-boundary; 2026 replacement ES-03-open-critical` |
| ES-02-Q06 | SRAD是需求响应特定产品，存在容量拍卖/容量费；2025适用年度框架，2026起原则上六个月合同。独立储能是否可按需求响应身份参加未确认。 | S-SRAD-2025 §§119-138, 167-179, 217-225; S-SRAD-2026 §§124-138 | `closed-capacity; storage eligibility ES-04-open-critical` |

## E. 越界控制与研究解释

- 日前/日内市场规则、OMIE/EUPHEMIA、价格和出清未在辅助服务 ES-01/ES-02 研究；此处仅引用其作为96连续闭市触发RR停止的程序接口。现货子项目 ES-SP-02 已另行研究日前规则，ES-SP-03 将研究日内细则。
- 电压/无功/黑启动列为“仅登记”服务；REE regulatory framework 提供条件入口，但未进入产品参数或储能收益分析。
- `provisional` 与 `unresolved` 项不得转化为模型参数；ES-02/ES-03结论仅用于规则交接，任何储能SOC、持续时间、FCR/SRAD资格和2026 RR替代争议交主线程ES-G3/后续模块裁决。

## F. ES-03 已确认的能量边界（不等于结算公式闭合）

- aFRR/PICASSO：aFRR能量产品为自动、FAT 5 min、15分钟交付、€/MWh；容量中标后的首版备用报价为D-1 20:00前，能量报价可从D-1 12:00接收并按规则持续更新；PICASSO主路径与本地/SRS/RCP fallback分层记录。
- mFRR/MARI：mFRR为手动、FAT 12.5 min、1 MW、€/MWh；同时参与aFRR/secondary的供应商适用5–30分钟标准交付（程序化5分钟、直接最长20分钟），mFRR-only供应商适用15分钟程序化交付、直接激活最长约29分钟；23:00前提交次日可用上/下备用、变更时持续更新、交付前25分钟截止；MARI故障由本地算法/其他机制覆盖。
- RR/TERRE：RR为手动程序化、FAT 30 min、交付15–60分钟、24 horizons；2025-12-30约09:00–10:00 MTU停止TERRE；2026替代机制未确认。
- IN/IGCC：仅为TSO–TSO netting和aFRR需求校正，不是储能可直接投标产品。
- ES-03不新增建模假设；未交付公式、SOC/持续时间、储能产品资格、不平衡价格和数据时区继续保留未决。

## G. ES-04 独立储能准入、预认证与技术履约未决事项

| ID | 问题 | 已确认边界/证据 | 风险/影响 | 状态 |
|---|---|---|---|---|
| ES04-U01 | 独立储能作为 FCR/一次调频 BSP 的明确申请、测试与补偿规则？ | Art.5 列 FCR；P.O.3.8 测试目录只列 aFRR/mFRR/RR；REE 指南描述并网发电机强制且无偿响应，非规范。 | FCR 是否属于储能产品范围 | `open-critical` |
| ES04-U02 | Art.9(2)(d) 未测试功率/UP 总功率比例精确公式、方向和四舍五入？ | 免测例外本身在 BOE Art.9(2)(d) 确认；公开 PDF OCR 中比例段不可可靠读取。 | 聚合新增 UF 的预认证 | `open-critical` |
| ES04-U03 | P.O.9.2/REE 接口是否要求储能 SOC、可用能量、方向状态等字段？ | Annex I 仅规定 4 秒遥测/AGC/ICCP；S-MITECO 规定 QH 计量；未找到 SOC 数值字段。 | 遥测和履约数据设计 | `open` |
| ES04-U04 | aFRR/mFRR/RR 的 SOC、持续时长、容量预留、补能/恢复及资源受限豁免？ | P.O.3.8 只给 15 分钟保持、100/300 秒 aFRR 和 12.5/30 分钟斜坡。 | 能量可交付性、可用容量与收益上限 | `open-critical` |
| ES04-U05 | 强制可用率、停权计数、整改后恢复测试及 Art.14 之外的资格保持阈值？ | Art.14 规定持续监测、至少五年复评、最多一个月整改后可 inhabilitación；Annex I 的 99.5% 和 <60 分钟为建议。 | 资格风险、罚则和恢复流程 | `open-critical` |
| ES04-U06 | 独立储能能否在 P.O.7.5 作为需求 UF 直接参加 SRAD？ | P.O.7.5 明确需求 UP/UF 和关联储能不得减少发电或增加充电；未见独立 storage UF 注册条款。 | SRAD 收入边界 | `open-critical` |
| ES04-U07 | 双向储能采用一个 UP 还是发电/需求分拆 UP 的具体 P.O.3.1/计量配置？ | Art.8 按主要活动分 UP；Art.16 要求注入/取电分别计量。 | UP/UF 结构和 BRP 偏差 | `open` |
| ES04-U08 | TERRE 停止后 2026 RR 替代平台、产品和储能预认证规则？ | ENTSO-E 确认 2025-12-30 停止；截至 2026-08-11 未找到完整西班牙 BOE/REE 替代规则。 | 2026 基准日和历史延续性 | `open-critical` |

ES-04 的所有未决项不得转化为模型约束、产品收入或 SOC 参数；需由主线程在 ES-G4 复审时决定是否进一步向 REE/CNMC 发函或暂不建模。

## I. ES-06 官方数据目录与历史版本未决事项（访问日 2026-08-18）

| ID | 问题 | ES-06 证据/边界 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES06-Q01 | eSIOS/REData 中 aFRR 容量、aFRR/mFRR/RR 能量、激活、IGCC/IN 的具体 indicator ID、字段、单位和方向是什么？ | S-REE-REData-API-2026 仅确认 widget GET/date filter；S-eSIOS-API-IND-2026 仅确认 `/indicators?text` 搜索和 JSON id。未逐项请求指标。 | 无法建立可复核 15-min 序列；不得写模型输入 | ES-06 | `open-critical` |
| ES06-Q02 | eSIOS/REE 数据的实际时区（CET/CEST）、DST 重复/缺失小时、发布延迟、缓存、revisionNumber 和修订覆盖是什么？ | API 文档示例有 ISO `datetime`/`datetime_utc`；P.O.10.5 仅确认 best value ≤24h、D+1/M+1 发布。逐指标元数据未核验。 | 时间对齐、缺失和 revision 处理可能改变回测 | ES-06/ES-05 | `open-critical` |
| ES06-Q03 | 2025 全年（含 2025-05-01 ISP15 前后）公共平衡数据、激活量和价格是否可下载，历史保留期和重发布机制是什么？ | eSIOS downloads 页面支持按 publication/data date 过滤，但未证明每个 dataset 的 2025 保留和 completeness。 | 历史回测覆盖风险 | ES-06 | `open-critical` |
| ES06-Q04 | `MEDBC`、`POSFIN/PHFC`、`AJUDSV`、`DESV` 是否有公共 API 字段，还是仅在 BRP 私有 `p48cierre/reganecuQH`？ | BOE-A-2025-13076 §13 确认公式；REE settlement guide pp.4–10、16 说明私有文件。公开字段/权限未核验。 | BRP 偏差无法独立复算 | ES-06/ES-05 | `open-critical` |
| ES06-Q05 | `PDESV/PDESVS/PDESVB` 的精确定义、单/双价方向和与 `prdvdatos/prdvusuqh/prdvbaqh` 的映射是什么？ | 指南 p.9 仅确认 `prdv*` 文件用于价格核对；未找到公开 volume-2 字段字典。 | 不平衡价格方向和结算金额可能错配 | ES-05/ES-06 | `open-critical` |
| ES06-Q06 | storage 双向计量的 AS/AE、QH best energy、telemetry integral 和缺失值标志在 SIMEL/eSIOS 的字段名及单位？ | BOE-A-2025-6693 §§1348–1355、1925、1950 确认 Activa saliente/entrante 和估计分支；接口字段未确认。 | 双向净额、充放电方向和缺失处理风险 | ES-04/ES-05/ES-06 | `open` |
| ES06-Q07 | MARI/PICASSO 连接日及 local fallback→platform 的逐日切点、平台 price/activation 数据是否与 REE settlement 段 `TER/SEC` 一致？ | REE 入口仅给 MARI 2024-12、PICASSO 2025-06 月份；具体日和字段 mapping 未确认。 | 2025 平衡能量序列版本断裂 | ES-03/ES-06 | `open` |
| ES06-Q08 | TERRE 最后 MTU（2025-12-30 约 09:00–10:00）在 REE/eSIOS 归档中的文件/时间戳和 2026 replacement 数据入口是什么？ | S-ENTSOE-TERRE-2026 确认停止和 former-member；REE RR 入口未确认归档标识；2026 replacement 未找到完整 BOE/REE规则。 | 2025 RR 截断与 2026 模拟无可复核输入 | ES-03/ES-05/ES-06 | `open-critical`（对应 ES05-Q06/ES04-U08） |
| ES06-Q09 | A1–A5/C1–C5、M+1/M+11/最终闭算和 120 日更正后，BSP 未交付、BRP 偏差和公开价格是否重算、覆盖原值或新增 revision？ | REE 指南 pp.8–10 说明结算批次和 corrections；P.O.14.1/14.4 的版本日程需逐项核对，API revision 字段未验证。 | 事后结算与可执行决策数据混淆 | ES-05/ES-06 | `open` |
| ES06-Q10 | 2026-06-27 BOE-A-2026-14009（THIPh/EHRPh、75% valid、M+1 publication）在 2026-08-11 基准日后是否已进入 REE/SIMEL 接口？ | BOE 明确 2026-09-01 生效；本研究基准日前不可使用，接口实施状态未核验。 | 避免 future rule 覆盖基准日 | ES-06 | `open`（future-effective boundary） |

ES-06 不关闭 ES05-Q01–Q06：FCR/SRAD 资格、SOC、持续时长、补能/恢复、可用率以及 2026 RR 替代仍保持 `open/open-critical`。任何 `open/provisional` 字段或时滞不得进入 `model/`、`src/`、`data/raw/` 或收益模型。

## H. ES-05 不平衡结算与储能接口（2026-08-18）

| ID | 问题 | 已确认边界/证据 | 风险/影响 | 责任模块 | 状态 |
|---|---|---|---|---|---|
| ES05-Q01 | P.O.14.4 在2025每个日期的有效版本（2024-20995、2025-5342、2025-13076）及 OMIE MTU15 触发替代日？ | ISP15 版本自2024-12-01生效（S-CNMC-2024-ISP15）；S-CNMC-2025-QH将生效绑定OMIE MTU15生产日；2025-13076后续修改。 | 结算历史版本切片可能错位 | ES-05/06 | `open` |
| ES05-Q02 | REE/eSIOS 公开不平衡价格、MEDBC、AJUDSV、激活量字段的 API 名、时区、延迟、revisionNumber、历史覆盖？ | S-REE-DATA-BAL-2026、S-eSIOS-PRICES-2026仅确认入口，字段尚未逐项下载核验。 | 数据目录与回测可复现性 | ES-06 | `open-critical` |
| ES05-Q03 | 计量估计/更正后，BSP 未交付和 BRP 偏差是否联动重算、触发方和通知字段？ | MITECO P.O.10.5规定最佳值≤24h、M+11闭算、闭算后120日更正和异常重发布；P.O.14.1规定BRP申诉。 | 最终结算与实时数据差异 | ES-05/06 | `open` |
| ES05-Q04 | SOC、持续时长、补能和可用率是否属于产品资格、未交付计算或豁免条件？ | P.O.14.4未出现SOC字段；ES-04 P.O.3.8/7.2/7.3技术参数缺口仍存在。 | 履约罚则和储能可交付容量 | ES-04/05 | `open-critical`（对应 ES04-U04/U05） |
| ES05-Q05 | 独立储能 FCR/SRAD 资格及其结算接口？ | Art.7一般储能BSP入口已确认；FCR、SRAD仍无独立储能产品条文。 | 产品范围和收益边界 | ES-04/05 | `open-critical`（对应 ES04-U01/U06） |
| ES05-Q06 | TERRE 2025-12-30停止后的2026 RR替代产品、激活和不平衡价格输入？ | ENTSO-E确认TERRE停止；截至基准日未找到完整西班牙 BOE/REE替代P.O. | 2026规则延续性 | ES-03/05/06 | `open-critical`（对应 ES04-U08） |
