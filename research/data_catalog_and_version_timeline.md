# ES-06 西班牙官方数据目录与历史版本时间线

研究对象：西班牙半岛平衡容量、平衡能量、激活、不平衡价格、BRP 偏差和储能双向计量。历史期为 **2025-01-01—2025-12-31**，规则基准日为 **2026-08-11**；本文件访问日为 **2026-08-18**。本目录不下载或保存大批量原始时序，也不把尚未核验的接口字段写成模型输入。

## 1. 证据分层和可复现性约定

* **规则事实（F）**：BOE/CNMC/MITECO 或 REE 约束性文本直接写出的定义、生效日和结算/计量流程。
* **数据接口事实（D）**：REE/eSIOS/ENTSO-E 官方页面或文档明确的 API 路由、公开/私有访问、字段示例和发布时间要求。
* **研究解释（I）**：把西班牙本地产品、欧洲平台和结算文件拼接成可复核工作流；不能替代规则。
* **建模假设（A）**：本文件不新增模型假设。`open`/`provisional` 的 API 字段、时滞、历史覆盖、权限或映射不得进入模型。

时间统一记录为 Europe/Madrid（CET/CEST）并保留原始 UTC offset；REE API 示例同时返回 `datetime`（带 offset）和 `datetime_utc`，但逐指标实际时区仍需核验。能量单位优先 MWh、价格 EUR/MWh，aFRR 容量价格 EUR/MW；接口的单位元数据未逐项验证时标记 `open`。

## 2. 官方来源登记

| source_id | 文件/页面（机构） | 发布/生效关系 | URL；访问日 | 定位与证据状态 |
|---|---|---|---|---|
| S-REE-REData-API-2026 | REData API 文档（REE） | 页面持续维护；文档未给单一版本日期 | [REE REData API](https://www.ree.es/es/datos/apidatos)，2026-08-18 | §§15–24：GET `/lang/datos/{category}/{widget}`；§§79–126：ISO 日期、hour/day/month/year 聚合及地域参数；§§164–200：JSONAPI、`last-update`/`cache-control`。**D-confirmed**；平衡 widget 名称和指标 ID 未核验。 |
| S-eSIOS-API-IND-2026 | eSIOS Indicator API 文档（REE） | 页面示例；无统一发布日期 | [Indicator API](https://api.esios.ree.es/doc/indicator/search_indicators_by_name.html)，2026-08-18 | §§8–12：`locale`、`text`；§§15–34：GET `/indicators?text=...`、API key、JSON 返回 `id`；逐项 indicator ID、单位、刷新频率和访问限额 **open**。**D-confirmed route / fields open**。 |
| S-REE-DOWNLOAD-2026 | eSIOS 公共下载页（REE） | 页面持续更新 | [eSIOS descargas](https://www.esios.ree.es/es/descargas)，2026-08-18 | 页面说明可按“publication date”或“data date”筛选；公开下载类别含 Mercados/Precios/Operación 等。2025 全年每个平衡文件的保留和重发布历史 **open**。**D-confirmed access pattern**。 |
| S-REE-LIQ-GUIDE-2024 |《Guía de ayuda para la comprobación de la liquidación de los servicios de ajuste del sistema》，Dec-2024（REE） | 2024-12；非规范性指南（PDF p.3） | [REE settlement guide PDF](https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/normativa_guias/Guia_comprobacion_liquidacion_servicios_ajuste_sistema.pdf)，2026-08-18 | PDF pp.4–6、9、16–18：`reganeu`/`reganecuQH`、`rp48preccierre`、`p48cierre`、`prdv*`、SIMEL、A1–A5/C1–C5 和字段表。**D-confirmed**，指南不改变 P.O. 法律效力。 |
| S-REE-LIQ-ACCESS-2026 |“Te ayudamos con tu liquidación”（REE） | 页面持续维护 | [REE liquidación access](https://www.ree.es/es/clientes/generador/acceso-a-tu-liquidacion)，2026-08-18 | §§53–64：REE 负责服务调整和不平衡结算，P.O.14.1/14.4 为法律入口；§§71–80：BRP 私有结算 ZIP，仅 BRP 可访问。**D-confirmed**。 |
| S-MITECO-2025-ISP | BOE-A-2025-6693，SEE Resolución 28-03-2025 | 发布 2025-04-02；**2025-05-01 生效** | [BOE-A-2025-6693](https://www.boe.es/buscar/doc.php?id=BOE-A-2025-6693)，2026-08-18 | §§88–109：P.O.10.1/10.2/10.4/10.5/10.6/10.11；§§104–108：发布后次月首日生效；§§1348–1355：storage 同时有 Activa saliente/entrante/reactiva；§§1925、1950：缺失和 QH 聚合处理；§§1930–1932：最佳值最大 24h 延迟；§§2205–2213、2255–2261、2334：D+1/M+1 发布和闭算。**F-confirmed**。 |
| S-CNMC-2024-ISP15 | BOE-A-2024-20995，CNMC Resolución 03-10-2024 | 发布 2024-10-14；ISP15/P.O.14.4 版本自 2024-12-01 的适用边界已有 ES-05 登记，逐日触发仍需按 OMIE MTU15 核验 | [BOE-A-2024-20995](https://www.boe.es/eli/es/res/2024/10/03/%281%29)，2026-08-18 | P.O.14.4 15.5、17.4、18.3 及前言：PHFC/QH、不平衡和成本分配的四分之一小时修订。**F-confirmed for amendment; exact daily slice open (ES05-Q01)**。 |
| S-CNMC-2025-QH | BOE-A-2025-5342，CNMC Resolución 06-03-2025 | BOE 发布 2025-03-17；部分条款按 MTU15 生产日/OS 通知生效 | [BOE-A-2025-5342](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-5342)，2026-08-18 | P.O.3.1、3.3、14.4 修订；与 2024-20995 的版本关系明确，实际 2025 日切换 **open**。**F-confirmed relation / timing open**。 |
| S-CNMC-2025-VOLTAGE-13076 | BOE-A-2025-13076，CNMC Resolución 12-06-2025 | 发布 2025-06-26；部分元素按 Resuelve deferred dates | [BOE-A-2025-13076](https://www.boe.es/eli/es/res/2025/06/12/%281%29)，2026-08-18 | P.O.14.4 §13（HTML §§2624–2637）：MEDBC、POSFIN、AJUDSV、DESV；适用日期切片 **open**（ES05-Q01）。**F-confirmed definitions/version boundary**。 |
| S-CNMC-2026-RT | BOE-A-2026-14009，CNMC Resolución 19-06-2026 | 发布 2026-06-27；**2026-09-01 生效**，因此在 2026-08-11 基准日尚未生效 | [BOE-A-2026-14009](https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-14009)，2026-08-18 | HTML §§419–430：`THIPh/THIQh`、`EHRPh/EHRQh` 及 storage 出/入分开、至少 75% 有效记录；§§388–391：实时数据至少 4 秒（OS 可按服务要求 4–12 秒）；§§491–492：M+1 发布质量/不合规；分析行 1125–1127：生效日。**F-confirmed future boundary；不可回填 2025/基准日**。 |
| S-REE-RT-FAQ-2026 |“Cómo participar en los servicios de balance / FAQ”（REE） | 页面访问时点 2026 | [REE balance participation](https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance/como-participar-en-los-servicios-de-balance)，2026-08-18 | 页面列出 1 MW、结构数据、实时遥测、控制中心、P.O.3.8 测试和 SRAD 需 habilitación。**D/解释性入口**；资格规则以 BOE/CNMC 为准。 |
| S-ENTSOE-EDI-2024 | EDI library（ENTSO-E） | schema 版本依文件；平台 schema 的生效/停用需逐文件 | [ENTSO-E EDI library](https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/)，2026-08-18 | 官方 schema 入口；可用于 PICASSO/MARI/TERRE/IGCC activation、bid、allocation result 的消息映射；字段名和历史归档未逐项下载，**D-provisional**。 |
| S-ENTSOE-TERRE-2026 | TERRE platform status（ENTSO-E） | 西班牙/葡萄牙约 2025-12-30 09:00–10:00 MTU 停止；2026-01-01 former member | [ENTSO-E TERRE](https://www.entsoe.eu/network_codes/eb/terre/)，2026-08-18 | web §§127–151、208–229（既有 ES-01/02 定位）。**F-confirmed stop; Spanish 2026 replacement open**。 |

## 3. 数据集目录（2025 历史期 vs 2026-08-11 基准）

以下“字段”是已由官方文本确认的字段或待核验的候选接口字段。候选字段不得直接作为模型输入。

| data_id / 提供方 | 数据内容和候选字段 | 频率/时区/单位 | 发布、闭算、修订和访问 | 2025 覆盖与 2026-08-11 状态 |
|---|---|---|---|---|
| D-01 REE/eSIOS 本地 aFRR reserve capacity | 每 QH、上/下方向的 requirement、allocation/awarded MW、边际 capacity price（€/MW）；BSP/UP 代码和不可分标记。indicator 630/631/632/633/634/2130 已通过官方搜索、元数据和历史请求确认。 | QH；Europe/Madrid（原始 offset 保留）；接口 `magnitud` 返回 `Potencia` 或 `Precio €/MW`，更细 SI 单位仍 **open** | 公共 eSIOS/REE 平衡入口；2025-07—2026-07 按月 130 个请求均 HTTP 200，最终修订延迟和质量标志仍 **open**。 | 2025 全年序列已保存；单位解释、revision/finality和参与者级字段仍待确认。 |
| D-02 REE/eSIOS + PICASSO aFRR energy | activated energy、direction、price；indicator 680/681/682/683 已通过官方搜索、元数据和历史请求确认。BSP/UP或portfolio 标识、CBMP/local fallback字段不在这些公共 indicator 值中。 | QH（15 min）；接口 `magnitud` 返回 `Energía` 或 `Precio €/MWh`，具体能量单位和底层结算映射仍 **open**；保留本地/UTC时间 | eSIOS 公共价格/程序和私有结算文件并存；2025-07—2026-07 请求均 HTTP 200，但部分月份少于理论 96 点/日，缺口和修订状态需单独解释。 | 2025-01—PICASSO 接入前后制度切片仍需用于规则分析；本批数据仅作为系统级公开序列，不能代替 BSP 结算。 |
| D-03 REE/eSIOS + MARI mFRR | mFRR 上/下 energy assignment、activation、price、availability/offer；结算常见 `TER` 段、`rp48preccierre`、`reganecuQH`。字段字典和 MARI message ID **open**。 | QH；MWh、€/MWh；本地日期时区，平台 schema 时区 **open** | 结算指南 pp.5–7 指向 `rp48preccierre`/`reganecuQH`；BRP 细节私有。MARI 2024-12 接入，逐日切换 **open**。 | 2025 全年需 local→MARI 分段；2026 可用性和重发布策略 **open**。 |
| D-04 REE/eSIOS + TERRE RR | RR bid/activation/assignment、上/下方向、FAT/15–60 min horizon、price。P.O.3.3 的 24 horizons/40 blocks 是规则字段；实际 eSIOS indicator/file ID **open**。 | QH product；MWh、€/MWh；Europe/Madrid/UTC 映射 **open** | TERRE 平台 2025-12-30 停止；历史归档是否保留、最后 MTU 标识和 republication **open-critical**。 | 2025-01-01 至停止时刻可列 TERRE；2025-12-30 后不得外推。2026 RR 替代产品/数据入口 **open-critical**。 |
| D-05 REE/eSIOS + IGCC/IN | TSO–TSO imbalance netting / exchanged volume、direction、price/settlement；不是 BSP 可投标产品。具体公开字段和 API **open**。 | 通常控制周期/小时或 QH；单位 MWh、€/MWh；时区 **open** | ENTSO-E EDI schema 提供消息层，REE 页面列 IGCC；公开历史覆盖和价格字段 **open**。 | 2025/2026 可作为系统层校验，不得当作储能收入。 |
| D-06 eSIOS imbalance price | indicator 763/764 分别返回 `Precio de los desvíos medidos a subir/bajar`；已通过官方搜索、元数据和 2025-07—2026-07 历史请求确认。`prdvdatos` 等结算文件的细分字段仍需另行核对。 | QH（ISP15 后）；接口 `magnitud` 返回 `Precio €/MWh`；P.O.14.4 使用 CET/CEST，API offset 已保留。 | 13 个月请求全部 HTTP 200；发布延迟、revisionNumber、单/双价结算映射仍 **open**。 | 2025 按 P.O.14.4 版本切片；公开指标可用于市场层价格分析，不能替代 BRP 私有结算。 |
| D-07 BRP position/imbalance | `MEDBC`（central-bus metered energy）、`POSFIN`（PHFC + IT）、`AJUDSV`（EB + ERTR，后续版本含 EPTR）、`DESV = MEDBC − (POSFIN + AJUDSV)`；PHFC、PHL、SALDOENE 作为派生项。 | QH（2025 ISP15）；MWh；Europe/Madrid CET/CEST | BOE-A-2025-13076 §13（HTML §§2624–2637）确认定义。BRP 明细在私有 `p48cierre`、`reganecuQH`；公共聚合/API 字段 **open**。 | 2025 需按 2024-20995/2025-5342/13076 日切片；2026 基准仍有定义，但公开可得性未确认。 |
| D-08 settlement ledgers and closure stages | `reganeu`（小时）/`reganecuQH`（QH）记录：Fecha, UPR, Energía MWh, Precio EUR/MWh, Importe EUR, Agente, Segmento, Facturación, EIC, cuenta, signos, códigos de magnitud/precio/apunte, tipo oferta/UPR 等；`EF_segmento_fechainicio_fechafin`、`liquicomun`。 | A1–A5/C1–C5 结算批次；QH/小时；EUR/MWh、EUR、MWh | REE 指南 pp.4–6、16–18；BRP 私有 ZIP（REE liquidación access §79），公开 `liquicomun` 为非机密汇总。新信息可在后续 closure 重算；确切 M+11/120日规则按 P.O.14.1 版本。 | 2025 历史结算文件可复核性取决于 BRP 权限；公共聚合保留 **open**。 |
| D-09 SIMEL / P.O.10.5 storage meter | `Activa saliente`（export/injection）、`Activa entrante`（import/consumption）、reactive quadrants；QH best energy、firm/estimated/invalid、meter type and incidence. | QH（storage/balance）；kWh/MWh；Europe/Madrid；计量记录精度由点表/设备规定。 | BOE-A-2025-6693 §§1348–1355、1925、1950、1930；缺失时 generation/storage 0 kWh outgoing and max incoming estimation rules需按具体情形；SIMEL 访问/字段 **open**。 | 2025-05-01 起 P.O.10.x 全量接口；2025-01—04 需使用前版/telemetry fallback。2026 基准字段仍有效，具体 API **open**。 |
| D-10 real-time telemetry / P.O.9.2 | `THIPh`/`THIQh`（active/reactive integrated telemetry）及 `EHRPh`/`EHRQh`（registered hourly energy），storage outgoing/incoming separately; quality valid-hour flag. | 原始实时 4–12 s（2026-14009）；发布聚合 M+1；MWh、MVArh；时区本地。 | BOE-A-2026-14009 §§388–391、419–430、491–492；其规则 **2026-09-01 才生效**，基准日不得倒填。2025 适用的 4 s/telemetry fallback 见 P.O.9.2/P.O.10.5，字段公开性 **open**。 | 2025 可用计量积分/遥测验证，但上述新字段只标 provisional；2026-08-11 为 future-effective。 |
| D-11 participant/UP/BSP structural data | BSP/UP/UF codes, holder/representative, start/end dates, aFRR BSP ownership; P.O.14.2 lists fields. | 事件/结构变更；无固定频率；单位 N/A | P.O.14.2 data fields in BOE-A-2024-11535 pp.195–196；部分 structural downloads eSIOS/private. 按日期公开聚合和关系历史 **open**。 | 2025/2026 可用于参与者识别，但不能推断独立储能 FCR/SRAD 资格。 |
| D-12 European platform EDI | PICASSO/MARI/TERRE/IGCC bid, activation, allocation-result, schedule and cross-border capacity message schemas. | 平台产品各自 QH/MTU；schema timestamp UTC 约定需逐 message 核验。 | ENTSO-E EDI library only gives schema entry; schema version, deprecation, historical archive and API limits **provisional/open**。 | 2025 TERRE cut at 2025-12-30; 2026 TERRE replacement unresolved。 |

### 3.1 关键字段字典（不把候选缩写当成接口已核验）

| 字段/缩写 | 已确认含义 | 证据定位 | 状态 |
|---|---|---|---|
| `MEDBC_brp` | BRP 在 barras de central 的计量，汇总其发电/消费 UP（必要时含自发自用 surplus）。 | BOE-A-2025-13076 P.O.14.4 §13.1；HTML §§2624–2627 | **F-confirmed** |
| `POSFIN_brp` / `PHFC` | `POSFIN = Σ PHFC + Σ IT`；PHFC 为最终程序，IT 为 BRP 间程序变更。 | BOE-A-2025-13076 §§2629–2634 | **F-confirmed**；公开文件名/字段 **D-open** |
| `AJUDSV_brp` | 平衡能量 EB、实时技术约束 ERTR；2025-13076 版本还含 aFRR BSP 的 EPTR 情形。 | BOE-A-2025-13076 §§2636–2637；BOE-A-2024-7254 | **F-confirmed** |
| `DESV_brp` | `MEDBC − (POSFIN + AJUDSV)`。 | BOE-A-2025-13076（P.O.14.4 §13） | **F-confirmed** |
| `PDESV`, `PDESVS`, `PDESVB` | 任务要求的候选不平衡价格字段/文件缩写；官方公开页仅确认 `prdvdatos`、`prdvusuqh`、`prdvbaqh` 文件用于价格核对，未给逐字段定义。 | REE settlement guide PDF p.9；eSIOS volume 2 尚未逐项核验 | **open/provisional**，不得写入模型 |
| `reganecuQH` | QH account entries: Fecha, UPR, Energía, Precio, Importe, Segmento, Facturación, EIC, signs and codes 等。 | REE settlement guide PDF pp.4、16 | **D-confirmed fields**；公开权限 **restricted** |
| `rp48preccierre` / `p48cierre` | 结算指南用于查看 mFRR/tertiary programmed assignment、price 和 BRP final position/imbalance adjustment。 | REE settlement guide PDF pp.6–9 | **D-confirmed file role**；字段版本/历史下载 **open** |
| `AS` / `AE` | P.O.10.5 中 Active saliente / Active entrante；storage 两者都适用。 | BOE-A-2025-6693 §§1348–1355、2573–2577 | **F-confirmed** |
| `THIPh` / `THIQh` / `EHRPh` / `EHRQh` | 2026-14009 中实时有功/无功积分和小时计量记录；storage 出/入分别计算。 | BOE-A-2026-14009 §§421–439 | **F future-effective (2026-09-01)** |

## 4. 发布时滞、闭算、修订、缺失和权限

### 4.1 已确认的官方时滞/缺失规则

1. **最佳值**：P.O.10.5 规定在收到数据后最大 24 小时内计算/提供 best energy（S-MITECO-2025-ISP §§1929–1932）。
2. **storage 日发布**：类型 3/4/5 的 storage（由 distributor 负责读表）在 D+1 08:00 前可发布；主集中器/分布式集中器有 M+1 日程（§§2205–2213）。
3. **M+1 闭算**：P.O.10.5 §8 在 M+1 第五个工作日发布 closure；随后可提交 incidence/objection，具体窗口按版本切片（§§2255–2261、2334）。
4. **缺失值**：generation/storage 点在连续无有效值且无法估计时，outgoing 可按 0 kWh、incoming 按最大入口功率情形估计；这只适用于规则中列明的估计分支，不能当作所有储能缺失值通用填补（§§1528–1540、1925）。
5. **balance verification fallback**：前版 P.O.10.5/P.O.14.4 对没有 QH 表计的 RR/tertiary/storage 可用实时 active-power telemetry 的 QH integral；BOE-A-2024-7254 Annex III，需与 2025-05-01 后新计量规则分段。
6. **结算批次**：REE 指南 pp.8–9 区分 A1/C1、A2/C2、A3/C3、A4/C4、A5/C5；不同批次可获得不同测量数据。A1–A5/C1–C5 不是单一实时接口，应保留批次标签。
7. **私有访问**：`reganeu/reganecuQH` 等 BRP 明细和 settlement ZIP 在 eSIOS 私有区；公开 `liquicomun` 是非机密汇总。没有 BRP 权限不能宣称可重建某个 participant 的结算（REE liquidación access §§71–80）。
8. **2026 实时质量**：BOE-A-2026-14009 规定至少 75% 有效记录才形成有效小时积分，M+1 发布 telemetered integral/不合规；但在基准日尚未生效，不能回填 2025（§§419–430、491–492，生效 2026-09-01）。

### 4.2 尚未核验且必须保持 open/provisional 的项目

* eSIOS indicator ID、指标名称的历史版本、API key 申请/配额、HTTP 缓存、实时刷新频率和每个数据集发布延迟；API 文档只证明路由和 JSON 结构。
* aFRR/mFRR/RR/IGCC 的公开字段（尤其 activation volume、direction、CBMP/local price、BSP/UP）与欧洲平台 message ID 的逐字段映射。
* `PDESV/PDESVS/PDESVB`、`MEDBC/POSFIN/AJUDSV` 是否以同名公共指标暴露；目前只有 BOE 定义和私有结算文件角色得到确认。
* 2025-12-30 TERRE 最后 MTU 在 REE/eSIOS 归档中的标识、历史下载保留期和 republication；2026 RR replacement 的平台、产品、数据字段和储能准入均未找到闭环官方规则。
* API 实际时区、夏令时重复/缺失小时处理、负值/空值/估计值标识、revisionNumber 和更正后数据是否覆盖原值。

## 5. 2025 历史期与 2026-08-11 基准时间线

| 日期/时段 | 版本或平台事件 | 数据目录影响 | 证据/状态 |
|---|---|---|---|
| 2024-03-01 | P.O.10.5 第一阶段：balance verification 可用 15-min meter；此前使用 telemetry integral。 | 2025-01—04 的 RR/tertiary/storage verification 需保留前版 fallback 标签。 | BOE-A-2025-6693 前言 §§64–67；**F-confirmed historical boundary** |
| 2024-10-03 发布，2024-12-01 适用（ES-05登记） | BOE-A-2024-20995 调整 P.O.14.1/14.4 以适应 ISP15。 | BRP `PHFC/POSFIN/AJUDSV/DESV` 与结算批次自 ISP15 版本切片；逐日 MTU15 触发仍 open。 | [BOE-A-2024-20995](https://www.boe.es/eli/es/res/2024/10/03/%281%29)；**F version relation / daily slice open** |
| 2024-12 | 西班牙接入 MARI（mFRR）月度边界。 | D-03 mFRR 序列须区分 local fallback 与 MARI；确切连接日/首个有效 MTU open。 | REE platform page/source S-REE-PLATFORMS-2026；**F month / exact day open** |
| 2025-03-06/17 | BOE-A-2025-5342 发布 QH P.O.3.1/3.3/14.4 修订。 | 2025 规则中的 RR/PHFC/结算字段不可直接按旧 2024 文本全期套用；生效与 OMIE MTU15 生产日绑定。 | S-CNMC-2025-QH；**F publication / applicability open** |
| 2025-04-02，2025-05-01 生效 | BOE-A-2025-6693 新 P.O.10.1/10.2/10.4/10.5/10.6/10.11，完成 ISP15 第二阶段。 | D-09 storage AS/AE/reactive、QH best energy、缺失/估计和 D+1/M+1 发布切换；历史回测须在 2025-05-01 分段。 | S-MITECO-2025-ISP §§88–108、1348–1355、1929–1932；**F-confirmed** |
| 2025-06（月份） | 西班牙接入 PICASSO（aFRR）。 | D-02 aFRR energy 需 local/SRS→PICASSO 分段；精确连接日及 fallback notice open。 | REE platform page/source S-REE-PLATFORMS-2026；**F month / exact day open** |
| 2025-06-26 | BOE-A-2025-13076 发布控制电压相关 P.O. 修改，含 P.O.14.4 §13 版本。 | BRP 字段定义保持，但日期适用和后续 deferred elements 需按 ES05-Q01；不能把发布日当所有段落生效日。 | S-CNMC-2025-VOLTAGE-13076；**F version boundary / date slice open** |
| 2025-01-01—12-30 | 2025 历史期：MARI、PICASSO 与 TERRE 并行，P.O.14.4/ISP15 和 P.O.10.5 计量分段。 | 历史数据目录必须带 `rule_version`, `platform`, `meter_version`, `settlement_stage` 四个标签。 | **I workflow** based on above sources; no model assumption |
| 2025-12-30 约 09:00–10:00 MTU | TERRE/LIBRA 停止，REE/REN 变为 former member。 | D-04 RR 历史截断；最后 MTU/归档下载待确认。 | S-ENTSOE-TERRE-2026 §§127–151、208–229；**F-confirmed stop / archive open-critical** |
| 2026-01-01 | 西班牙不再为 TERRE member。 | 2026 RR 替代平台/本地机制不可由 2025 TERRE 外推。 | S-ENTSOE-TERRE-2026；**F-confirmed status / replacement open-critical** |
| 2026-06-27 发布，2026-09-01 生效（基准日之后） | BOE-A-2026-14009 更新 P.O.9.2/P.O.14.4，新增实时信息罚则结算和 storage 双向 `THIPh/THIQh/EHRPh/EHRQh` 字段。 | 2026-08-11 基准仍使用旧版；2026-09-01 后才可引入新的质量/罚则字段。 | S-CNMC-2026-RT §§419–430、491–492、分析行1125–1127；**F future-effective** |
| 2026-08-11 | 规则基准日。 | 本目录冻结在该日：保留已发布但未生效的 2026-14009 为 future；ES05-Q01–Q06、ES04-U01/U04/U06/U08 继续 open。 | 项目基准；**F/I boundary** |

## 6. 欧洲平台—西班牙本地数据映射（研究解释）

| 平台/过程 | 欧洲层数据 | 西班牙本地/结算映射 | 边界 |
|---|---|---|---|
| PICASSO / aFRR | aFRR bid/activation/allocation、跨区边际价和 exchange | REE P.O.7.2、`SEC`/aFRR settlement、BRP `AJUDSV`；本地 aFRR capacity 仍是独立 D-1/QH 入口 | 不能把 PICASSO energy price 当 aFRR capacity price；逐字段 ID **open** |
| MARI / mFRR | mFRR standard bid/activation/allocation | REE P.O.7.3、`TER` 段、`rp48preccierre`/`reganecuQH` | MARI outage fallback 和切换日 **open** |
| TERRE / RR（至 2025-12-30） | RR bid/activation/allocation | P.O.3.3 24 horizons、D-1 12:00/H-55′、`TER`/RR settlement | 停止后 2026 替代未确认；不能外推 |
| IGCC / IN | TSO–TSO imbalance netting | P.O.7.2/14.4 system balance adjustment；不是 BSP offer | 公开 price/volume API **open** |

## 7. 与 ES-04/ES-05 的交叉核对（不得重写为数据事实）

* FCR/SRAD 资格、SOC、持续时长、补能/恢复、可用率和预认证限制仍按 ES-04 `ES04-U01/U04/U05/U06` 保持 `open-critical`；本目录没有从计量字段反推这些规则。
* 2026 RR replacement 与 TERRE 停止后的激活/结算输入仍按 ES-04-U08、ES05-Q06 `open-critical`。
* `ES05-Q01`（2025 P.O.14.4 日切片）、`ES05-Q02`（eSIOS 字段/API/时区/延迟/历史覆盖）、`ES05-Q03`（计量更正与重算）、`ES05-Q04`（SOC/持续/可用率）、`ES05-Q05`（FCR/SRAD storage 接口）保持未决；本目录仅补充证据入口，不关闭问题。

## 8. 可复现性风险清单与后续核验

1. **高风险**：eSIOS indicator ID、公共/私有文件权限、2025 archive、revision/republication、TERRE 最后 MTU 均未逐项请求核验；不得在历史回测中假设完整覆盖。
2. **高风险**：P.O.14.4 版本在 2025 年内有 2024-20995、2025-5342、2025-13076 等切换；必须按生效日/MTU15 生产日建立日级 version key。
3. **中风险**：REE API 示例的 `datetime`/`datetime_utc` 结构已确认，但指标实际 CET/CEST、DST 处理、空值和负值标志未确认。
4. **中风险**：公开 REE/eSIOS balancing 页面是入口目录，不等于每个数据集提供 15-min、价格、激活量和修订号；未核验项只能写 `open/provisional`。
5. **范围控制**：不下载大批量原始时序、不修改 `data/raw/`；若后续获得访问授权，先保存 API/文件 schema 和版本元数据，再由主线程批准数据抓取。
