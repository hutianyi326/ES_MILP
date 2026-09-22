# 西班牙电力数据 API 目录（ES-DATA-01）

> 研究对象：西班牙（ES）公开可取得的市场价格、平衡/调频、系统负荷和发电数据。访问核验日：**2026-09-04（Europe/Madrid）**。本文只登记数据接口和可下载性，不写采集程序。
>
> 状态枚举：`已确认` = 官方资料直接给出接口/文件和字段；`部分确认` = 官方入口与样本文件存在，但指标级字段、完整性或认证尚未闭合；`待确认` = 只有候选 ID/名称或需要带 token 的逐指标请求。`2026-08 可下载`指交付日 2026-08-01 至 2026-08-31 的公开端点或 API 查询可能性，不等于已将整月文件保存到本仓库。

## 1. 结论摘要

1. **OMIE 现货价格可以直接下载且无需凭据。** 日前文件 `marginalpdbc_YYYYMMDD.1`、IDA 文件 `marginalpibc_YYYYMMDDSS.1`（`SS=01/02/03`）和连续日内文件 `precios_pibcic_YYYYMMDD.1` 均有官方文件目录。官方目录逐日列出了 2026-08-01—31 的 DA、IDA1/2/3 和 IDC 文件；因此这部分可作为第一批无 token 的回测输入。[OMIE 日前文件目录](https://www.omie.es/en/file-access-list?dir=+Day-ahead+market+hourly+prices+in+Spain&parents=%2FDay-ahead+Market%2F1.+Prices&realdir=marginalpdbc)、[OMIE IDA 文件目录](https://www.omie.es/es/file-access-list?dir=Precios+del+mercado+intradiario+de+subastas+en+Espa%C3%B1a&parents=%2FMercado+Intradiario%2F1.+Precios&realdir=marginalpibc)、[OMIE IDC 文件目录](https://www.omie.es/en/file-access-list?dir=Maximum%2C+minimum+and+weighted+price+for+each+period+of+the+continuous+intraday+market&parents=%2FContinuous+Intraday+Market%2F1.+Prices&realdir=precios_pibcic)
2. **现货制度断点必须切片。** IDA/连续日内 15 分钟产品自 2025-03-18（交付日 2025-03-19）运行；日前 15 分钟 MTU 自 2025-10-01（首个 96 个季度时段对应 2025-09-30 出清）运行。更早数据不能直接当成原生 15 分钟。[OMIE 15-MTU 日内通知](https://www.omie.es/sites/default/files/2024-10/241029_NOTA_INFORMATIVA_GOLIVE_15MTU_SIDC_PT.pdf)、[OMIE 15-MTU 日前通知](https://www.omie.es/sites/default/files/2025-10/2501001_go_live_mtu15_md_es_vf.pdf)
3. **eSIOS API 有官方 15 分钟请求语法，需要个人 token；本轮已验证 token 可用。** 官方文档确认 indicator、archive、日期范围、`time_trunc=fifteen_minutes`、`datetime_utc` 和 `values_updated_at` 等字段；本轮从 `data/API_Key.md` 读取 REE key，indicator 1293 元数据和 15 分钟样本均返回 HTTP 200。[eSIOS API 文档首页](https://api.esios.ree.es/)、[Indicator 日期范围接口](https://api.esios.ree.es/doc/indicator/getting_a_specific_indicator_filtering_values_by_a_date_range.html)
4. **aFRR、失衡价格、负荷和 P48 指标已通过官方名称搜索/元数据及历史样本请求闭合。** 本轮 37 个指标按月共 481 个请求全部 HTTP 200，完整期原始响应和处理结果已保存；部分 P48 月份无 values，已作为数据缺口保留，不能当作零出力。
5. **REE REData 的 `estructura-generacion` 不能作为本项目当前的小时级实际出力源。** 本轮实测中，2026-08 的 `time_trunc=hour` 请求返回 HTTP 400；`time_trunc=day` 虽成功，但 `magnitude=null`，无法据此安全解释单位或形成逐小时出力。因此改用 ENTSO-E Transparency Platform 的 `Actual Generation per Production Type [16.1.B&C]` 作为替代：官方定义为按市场时段/技术的实际净发电 MW，并支持 PT15M/PT30M/PT60M；但 REST API/FMS 需要注册和 token，本轮未读取 token，2026-08 响应未实测。[REE REData API](https://www.ree.es/en/datos/apidata)、[REE 发电结构页面](https://www.ree.es/es/datos/generacion/estructura-generacion)、[ENTSO-E A75 数据项页](https://transparencyplatform.zendesk.com/hc/en-us/articles/16648290299284-Actual-Generation-per-Production-Type-16-1-B-C-)、[ENTSO-E R3字段规范](https://transparencyplatform.zendesk.com/hc/en-us/articles/36493702227729-AggregatedGenerationPerType-16-1-B-C-r3)

## 2. 公共接口和请求约定

### 2.1 OMIE 文件

- 文件索引：<https://www.omie.es/en/file-access-list>。索引页面可按类别和 `realdir` 定位文件；官方说明公共仓库覆盖最近六个滚动年度，旧文件需向 OMIE Assistance Portal 申请。
- 直接下载模式（无需 token）：

  ```text
  https://www.omie.es/{es|en}/file-download?filename=<文件名>&parents=<realdir>
  ```

  例如：

  ```text
  https://www.omie.es/en/file-download?filename=marginalpdbc_20260801.1&parents=marginalpdbc
  https://www.omie.es/es/file-download?filename=marginalpibc_2026080103.1&parents=marginalpibc
  https://www.omie.es/en/file-download?filename=precios_pibcic_20260801.1&parents=precios_pibcic
  ```

- `Formatos_Intercambio_OM_Vol_I-Mercado.pdf`（OMIE，v3.1，2025-04-07）给出固定宽度文件的字段和单位。规范的示例仍以 period 1–100 表示历史小时口径；抓取 2025-03/10 后实际文件应按文件头和 period 值识别 15 分钟，不能盲用 1–100。
- OMIE 本地交付日期/period 与文件修改时间不是同一字段。应保存文件名中的交付日、文件头 `Fecha Emisión`（如有）、下载时间和原始文件哈希。

### 2.2 eSIOS Indicator/Archive API

基础域名：<https://api.esios.ree.es/>。

```text
GET https://api.esios.ree.es/indicators/{indicator_id}
    ?start_date=2026-08-01T00:00:00+02:00
    &end_date=2026-08-31T23:59:59+02:00
    &time_trunc=fifteen_minutes
    &locale=es
```

日期范围接口允许：`start_date`、`end_date`、`datetime`、`time_agg=sum|average`、`time_trunc=five_minutes|ten_minutes|fifteen_minutes|hour|day|month|year`、`geo_agg=sum|average`、`geo_ids` 和 `geo_trunc=country|electric_system|autonomous_community|province|electric_subsystem|town|drainage_basin`。返回结构至少应保留 `indicator`、`magnitud`、`geos`、`values`、`value`、本地偏移的 `datetime`、UTC 的 `datetime_utc` 和 `values_updated_at`。

认证：请求头为 `x-api-key`；官方 API 首页要求个人 token，并给出 `consultasios@ree.es` 作为申请邮箱。文档中的 key 仅为样例，未写入本目录。

归档元数据：

```text
GET https://api.esios.ree.es/archives
    ?start_date=2026-08-01T00:00:00+00:00
    &end_date=2026-08-31T23:59:59+00:00
    &date_type=datos|publicacion
```

返回 `archive id`、`date.date_type`、数据日期起止、`date_times`、`publication_date`、taxonomy/vocabulary 及 `download` URL；下载为 `GET /archives/{id}/download`。这可区分“数据日期”和“发布日期”，但不能由接口定义本身推断每项数据全年完整、不可修订或最终化。

### 2.3 REData API

官方 API：<https://www.ree.es/en/datos/apidata>；主机为 `apidatos.ree.es`，仅允许 GET，JSONAPI 格式：

```text
GET https://apidatos.ree.es/{lang}/datos/{category}/{widget}
    ?start_date=2026-08-01T00:00
    &end_date=2026-08-31T23:59
    &time_trunc=hour
    [&geo_trunc=electric_system&geo_limit=peninsular&geo_ids=<id>]
```

官方允许 `time_trunc=hour|day|month|year`，地理粒度目前为 `electric_system`；`geo_limit` 可为 `peninsular|canarias|baleares|ceuta|melilla|ccaa`。响应 `included[].attributes` 含 `title`、`description`、`magnitude`、`values` 和 `last-update`，meta 含 cache 信息。接口文档给出的 `estructura-generacion` 示例证明 widget 路径，不证明每种 `time_trunc` 对每个指标都有同样历史覆盖。

### 2.4 ENTSO-E Transparency Platform（实际发电替代源）

数据集：**Actual Generation per Production Type [16.1.B&C]**；R3 File Library 抽取名为 `AggregatedGenerationPerType_16.1.B_C_r3`，官方提供月度 CSV；REST API生产端点为 `https://web-api.tp.entsoe.eu/api`。官方帮助页将 `A75`定义为 Actual generation per type，`A16`定义为 realised process；旧版 generation dependency table把 `A01`（Production）、`in_Domain`、`psrType`和 PT15M/PT30M/PT60M 列为请求属性，A93/A94风光业务类型须以当前响应复核。

无真实 token 的请求模板（仅记录接口，不执行）：

```text
GET https://web-api.tp.entsoe.eu/api
    ?securityToken=<ENTSOE_TOKEN_NOT_STORED>
    &documentType=A75
    &processType=A16
    &businessType=A01
    &in_Domain=10YES-REE------0
    &periodStart=202608010000
    &periodEnd=202609010000
    &resolution=PT15M
    &psrType=B16
```

`resolution=PT15M`、`PT30M`或`PT60M`需按平台返回/当前参数字典确认；`psrType`按技术筛选，省略时可返回所有已发布技术。官方 R3 FMS CSV字段为 `DateTime(UTC)`、`ResolutionCode`、`AreaCode`、`AreaDisplayName`、`AreaTypeCode`、`ProductionType`、`ActualGenerationOutput[MW]`、可选 `ActualConsumption[MW]` 和 `UpdateTime(UTC)`。西班牙区域 EIC 为 `10YES-REE------0`，可显示为 `BZN|ES`、`CTA|ES`或 `CTY`，请求时要明确 AreaType。

认证和下载：REST API要求注册后向 `transparency@entsoe.eu` 申请 RESTful API 权限，再在 My Account 生成 security token；FMS 月度 CSV 使用 Keycloak/FMS登录 token。平台网页可查看 Spain/ES 与 `BZN|ES`，但导出需要登录。API日期参数均为 UTC；官方帮助说明单次 GET 请求时间范围不得超过一年，2026-08在范围内。平台帮助页列出该数据集的月度 CSV extract，但它没有在本次证据中给出可确认的历史起始日期/保留年限；本轮没有 token，因此**2026-08 文件/响应仅为接口可请求，未实测确认**。

## 3. 数据可下载性矩阵

| 数据集（统一 ID） | 官方名称/字段 | 指标 ID 或文件名 | API/下载 URL 与请求参数 | 原始/可请求粒度 | 单位、币种、区域 | 认证 | 发布时间/临时性 | 历史/制度断点 | 2026-08-01—31 可下载结论 |
|---|---|---|---|---|---|---|---|---|---|
| `OMIE_DA_PRICE_ES` | MARGINALPDBC；Spanish daily market marginal price，字段通常含交付年/月/日/period、`MarginalES`（另有 PT） | `marginalpdbc_YYYYMMDD.1` | [文件目录](https://www.omie.es/en/file-access-list?dir=+Day-ahead+market+hourly+prices+in+Spain&parents=%2FDay-ahead+Market%2F1.+Prices&realdir=marginalpdbc)；直接 `file-download?filename=marginalpdbc_YYYYMMDD.1&parents=marginalpdbc` | 2025-10-01 起原生 MTU15（通常 96/QH）；此前主要小时；请求按单日文件，不是 API 聚合 | EUR/MWh；ES 与 PT 区域列，研究字段取 ES | 无 | 文件日后公开；定稿/重发标识和修订规则须保留文件头/索引（官方未给统一延迟承诺） | 15 分钟日前断点：交付 2025-10-01；公共仓库最近六年 | **已确认。** 官方目录逐日列出 `marginalpdbc_20260801.1` 至 `...20260831.1`。 |
| `OMIE_IDA1_PRICE_ES` | IDA1 price by session/period，取西班牙区边际价 | `marginalpibc_YYYYMMDD01.1` | [IDA 文件目录](https://www.omie.es/es/file-access-list?dir=Precios+del+mercado+intradiario+de+subastas+en+Espa%C3%B1a&parents=%2FMercado+Intradiario%2F1.+Precios&realdir=marginalpibc)；直接 `file-download?filename=marginalpibc_YYYYMMDD01.1&parents=marginalpibc` | 2025-03-18 起 15 分钟；此前 IDA 时段为小时；按 session 文件 | EUR/MWh；ES/PT/同一市场结果，取 ES | 无 | 结果文件的正式/临时状态与每日发布时间未在格式规范统一承诺；保留索引“修改时间” | IDA 机制 2024-06-13 启动，15-MTU 2025-03-18 | **已确认。** 目录显示 2026-08 每日 `...01.1`。 |
| `OMIE_IDA2_PRICE_ES` | IDA2 同上 | `marginalpibc_YYYYMMDD02.1` | 同上，`SS=02` | 同上 | 同上 | 无 | 同上 | 同上 | **已确认。** 目录显示 2026-08 每日 `...02.1`。 |
| `OMIE_IDA3_PRICE_ES` | IDA3 同上 | `marginalpibc_YYYYMMDD03.1` | 同上，`SS=03` | 同上 | 同上 | 无 | 同上 | 同上 | **已确认。** 目录显示 2026-08 每日 `...03.1`。 |
| `OMIE_IDC_STATS_ES` | PRECIOS_PIBCIC；连续日内每个合约/period 的最大、最小、加权平均成交价 | `precios_pibcic_YYYYMMDD.1` | [IDC 文件目录](https://www.omie.es/en/file-access-list?dir=Maximum%2C+minimum+and+weighted+price+for+each+period+of+the+continuous+intraday+market&parents=%2FContinuous+Intraday+Market%2F1.+Prices&realdir=precios_pibcic)；直接 `file-download?filename=precios_pibcic_YYYYMMDD.1&parents=precios_pibcic` | 2025-03-18 起 15 分钟合约；规范字段包括 `MaximoES/PT/MO`、`MinimoES/PT/MO`、`MedioES/PT/MO` | EUR/MWh；ES/PT/MO（市场区/区域字段按格式文件） | 无 | 当日交易结束后发布；精确延迟、修订/最终标志未统一承诺 | 连续日内 15-MTU 2025-03-18 | **已确认。** 官方目录逐日列出 `precios_pibcic_20260801.1`—`...20260831.1`。 |
| `REE_AFRR_REQUIREMENT_UP_DOWN` | Reserva de regulación secundaria requerida a subir/a bajar（aFRR capacity requirement） | 先前研究候选 `630/631`；**官方 QH 实施指南确认需求概念，不确认这两个 ID** | eSIOS `/indicators/{id}` 或 `/archives`，带 `start_date/end_date/time_trunc=fifteen_minutes`；先用 `/indicators?text=` 搜索官方名称 | 规则为次日每 QH；暂未确认公开指标的原生粒度、聚合方式 | 规则语义 MW、peninsular、上/下方向；接口 `magnitud`/geo 需实际元数据确认 | eSIOS personal token（`x-api-key`） | OS 指南称次日需求在 D-1 **14:45 前**发布；临时/修订字段未确认 | QH SRS 指南（2024-10）；“引入 QH 能量产品前每小时内需求相同”是历史临时安排 | **待确认。** 没有 token，且 630/631 未在本次第一方 PDF 的指标表中核准；不可声称整月可下。 |
| `REE_AFRR_CAPACITY_AWARDED_UP_DOWN` | Asignación Banda de regulación secundaria a subir/bajar | **632/633** | eSIOS Indicator API `/indicators/632`、`/indicators/633`；参数 `start_date`、`end_date`、`time_trunc=fifteen_minutes`、可选 `geo_trunc=electric_system` | 2022 QH 适配附件列为小时指标转 QH；按 QH、上/下 | 规则/名称是 MW；地区为 Spanish peninsular system；接口单位需读取 `magnitud` | token | 指南称按 QH 结果；公开给 BSP 的发送时间与公共 API 延迟需逐项确认；是否 provisional/final 未闭合 | 2022-05-24 eSIOS QH 页面适配；2024 SRS 规则/2025+需检查版本 | **部分确认。** 官方 ID 与 API 路由确认，但未带 token 读取 2026-08 响应。 |
| `REE_AFRR_CAPACITY_PRICE` | Precio Banda de regulación secundaria | **634** | eSIOS `/indicators/634?...time_trunc=fifteen_minutes` | QH | EUR/MW；peninsular；上/下方向可能分别由 632/633结果关联；接口 `magnitud`需验证 | token | 指南确认独立上/下边际容量价；可能范围 [0,15,000] EUR/MW；API最终状态未确认 | 2022-05-24 QH 附件；2024-10 SRS 规则 | **部分确认。** 指标 ID 官方确认，整月请求需 token。 |
| `REE_AFRR_ACTIVATED_ENERGY_UP_DOWN` | ESECS/ESECB（aFRR energy settled/activated up/down） | 先前研究候选 `680/681`；**未在本次一方 ID 表中确认** | eSIOS Indicator API 路由模式已确认；需以 `/indicators?text=...` 找到正式 ID后查询 | 物理/结算原始控制周期 4 秒，官方 SRS 聚合为 QH（225 cycles/QH）；公共指标粒度与是否 MWh 未确认 | 规则能量为 MWh、价格为 EUR/MWh、peninsular、上/下；接口单位/方向字段待确认 | token | 2024-10 SRS §9.2.5明确每 4 秒计算、QH 聚合；公共 API 发布延迟和最终性未确认 | SRS Phase I (national) 与跨境 PICASSO/后续阶段需切片 | **待确认。** 规则计算方式已确认，指标 ID/公开整月序列未确认。 |
| `REE_AFRR_ENERGY_PRICE_UP_DOWN` | Precio de regulación secundaria subir/bajar；SRS energy price | **682/683** | eSIOS `/indicators/682`、`/indicators/683`；QH 参数同上 | QH 页面指标；底层 4-sec 计算，QH 汇总 | 名称对应 EUR/MWh；接口 `magnitud`、是否 weighted price/settlement price需验证 | token | SRS说明能量价格随控制周期并按 QH 汇总；公共 API final/provisional 未确认 | 2022-05-24 Annex I；2024-10 SRS | **部分确认。** ID与名称在官方 PDF确认，但不能代替激活量 680/681，且未带 token取 August。 |
| `REE_IMBALANCE_PRICE_UP_DOWN` | Precio de los desvíos a subir/a bajar（imbalance/deviation price） | 先前研究候选 `763/764`；**本次未取得官方指标表确认**。结算文件候选 `prdvbaqh/prdvusuqh` 也不得直接当成字段定义 | eSIOS indicator/archive入口；候选 `/indicators/763|764` 必须先用名称搜索和元数据核对；归档用 `/archives?date_type=datos|publicacion` | P.O.14.4 后一般 ISP/QH；API粒度与是否单价/双价待确认 | EUR/MWh、Spanish peninsular/BRP scope；上下方向/单价双价待确认 | token（公开汇总）；BRP 项目结算详情可能是私有 | REE市场页面解释按 P.O.14.4计算；统一公开延迟、修订和 final 标记未确认 | 2025 ISP15 / P.O.14.4 切点；不能将实时显示值和结算最终值混用 | **待确认。** 公开概念确认，ID、字段和 2026-08 逐日可用性未闭合。 |
| `REE_DEMAND_REAL` | Demanda real；实时系统负荷 | eSIOS Widget/indicator **1293**（名称在官方 Cached Widget V2/页面线索确认，需 indicator metadata复核） | eSIOS `/indicators/1293?...time_trunc=five_minutes|fifteen_minutes|hour`；REE实时曲线页面为公开可视化入口 | 原始实时曲线 5 分钟；eSIOS API可请求 5m/15m/hour（是否 1293 每种聚合均可用待请求） | MW（页面称 demand curve；接口 `magnitud`需保留）；全国/peninsular scope 要按 geo 元数据确认 | eSIOS token；网页可视化不等同无 token bulk API | REE 页面称曲线每 5 分钟更新，含 real/forecast/scheduled；历史值最终/修订未定义 | 5-minute curve adaptation 2022-05-24；DST保留 offset | **部分确认/待 token。** 公开实时入口和 indicator 候选明确，整月历史下载与 finality未验证。 |
| `REE_GENERATION_ACTUAL_TECH` | Estructura de la generación por tecnologías（REE REData） | REData widget `generacion/estructura-generacion` | `GET https://apidatos.ree.es/es/datos/generacion/estructura-generacion?...&time_trunc=hour|day`；本轮 hour=HTTP 400，day=成功但 `magnitude=null` | API文档通用支持 hour/day/month/year，但该 widget 的 2026-08 hour 实测不可用；day响应不能安全解释单位 | 页面展示 GWh/技术结构；本轮未取得可用 magnitude，不能当作 MW 出力 | 无 token GET | 页面有 provisional/definitive提示；本轮响应不足以判断 finality | 2026-08 hour路径失败；历史粒度/单位待 REE修复或另行接口 | **不可作为当前小时出力源。** 保留为失败记录，不能用 day 响应推导小时。 |
| `ENTSOE_ACTUAL_GENERATION_PER_TYPE` | Actual Generation per Production Type [16.1.B&C] / Aggregated Generation per Type | `documentType=A75`；`processType=A16`；`businessType=A01`（A93/A94风光为旧依赖表线索，需响应确认）；R3 `AggregatedGenerationPerType_16.1.B_C_r3` | REST `https://web-api.tp.entsoe.eu/api?securityToken=<...>&documentType=A75&processType=A16&businessType=A01&in_Domain=10YES-REE------0&periodStart=202608010000&periodEnd=202609010000&resolution=PT15M&psrType=B16`；FMS月度CSV | 官方依赖表和R3 specification支持 PT15M/PT30M/PT60M；`DateTime(UTC)`；按 `psrType/ProductionType` | `ActualGenerationOutput[MW]`（净实际出力；小规模可能估计）；区域 EIC `10YES-REE------0`，AreaType BZN/CTA/CTY；生产类型 B01–B20，Energy storage B25 | REST security token；FMS Keycloak/FMS token；网页查看可用但导出/批量下载需登录 | 官方数据规范要求 H+1；实际类型通常 no update；风光允许按测量值多次更新。Spain-specific note称公开值为 public grid 的 aggregated real-time set points，且不更新 | 2026-06-29官方数据项页仍列Spain；平台R3/FMS月度文件目录有该数据项。2026-08整月尚未用token实测 | **推荐替代，接口/字段已确认；2026-08可下载性待凭据实测。** 这是“平台定义的 actual”，不等于西班牙项目级结算计量。 |
| `REE_GENERATION_P48_TECH` | Generación programada P48 by technology（scheduled generation） | eSIOS QH Annex I IDs：71–93；94–105为 waste/interconnection；10008–10027、10042、10061、10063、10237、10238、10257为合计/分组（详见字段表） | eSIOS `/indicators/{id}`，日期范围 + `time_trunc=fifteen_minutes|hour`；可用 archive/download 找公共文件 | 2022 QH 页面适配后按 QH；历史更早可能小时；P48 是 schedule，不是 measured actual | 通常 MW 计划功率；每个 indicator 的 `magnitud`、区域和是否 generation/consumption must verify | token | P48计划按运行调度发布；公共延迟、修订和 finality未统一确认 | QH adaptation effective 2022-05-24；P48分类/技术字典可能随市场制度改变 | **待 token/逐项请求。** ID与名称官方确认，不能在无 token时声称 2026-08 整月公开响应可下载。 |

## 4. P48 技术指标字典（REE eSIOS Annex I）

以下名称来自 REE 官方《Updating of the e.sios public website to the 15-min scheduling project》附件 I；括号内是数据语义，不是建模假设。

| ID | 官方名称（西文简写） | 用途/注意 |
|---:|---|---|
| 71 | Generación programada P48 Hidráulica UGH | 水电 UGH 计划 |
| 72 | Generación programada P48 Hidráulica no UGH | 非 UGH 水电计划 |
| 73 | Generación programada P48 Turbinación bombeo | 抽水发电计划；不要与抽水用电混淆 |
| 74 | Generación programada P48 Nuclear | 核电 |
| 75–76 | Hulla antracita / sub-bituminosa Anexo II RD 134/2010 | 监管煤种旧分类；历史断点需保留 |
| 77–78 | Hulla antracita / sub-bituminosa | 煤种 |
| 79 | Ciclo combinado | 联合循环 |
| 80–81 | Fuel / natural gas | 燃油、天然气 |
| 82–83 | Eólica terrestre / marina | 陆上/海上风电 |
| 84–85 | Solar fotovoltaica / solar térmica | 光伏、光热 |
| 86 | Oceanográfica y geotérmica | 海洋能/地热 |
| 87 | Cogeneración gas natural | 天然气热电联产 |
| 88–90 | Derivados petróleo/carbón; residuos mineros; energía residual | 化石/副产物/残余能量 |
| 91–94 | Biomasa; biogás; residuos domésticos/similares; otros residuos | 生物质、沼气、垃圾 |
| 95 | Consumo bombeo | 抽水用电计划，负值/符号必须按原始定义处理 |
| 96–97 | Enlace HVDC Baleares; genérico | 电网/其他 |
| 98–105 | Import/export France, Portugal, Morocco, Andorra | 互联计划，不应并入技术发电 |
| 10008–10013 | P48 coal; fuel-gas; wind; cogeneration; non-renewable waste; other renewable | 分组指标 |
| 10014–10017 | Interconnection balances France/Portugal/Morocco/Andorra | 互联净额 |
| 10024–10027 | generation + pumping + HVDC; P48 adjustment; total interconnection balance; total scheduled demand | 汇总指标 |
| 10042 | Total generation + total interconnections | 汇总 |
| 10061 | Coal under RD 134/2010 | 旧监管煤分类 |
| 10063 | UGH + no UGH | 水电汇总 |
| 10237–10238 | Total import / total export | 汇总 |
| 10257 | Total scheduled generation | P48总计划 |

## 4.1 ENTSO-E 实际发电技术代码

ENTSO-E `PsrType` 官方代码表用于 `A75` 的 `psrType`筛选；R3 CSV同时给出可读的 `ProductionType`。下表是按技术实际发电的可用代码；`B25` Energy storage 是否在西班牙 A75 2026-08 返回，需要实测确认。

| psrType | 官方名称 |
|---|---|
| B01 | Biomass |
| B02 | Fossil Brown coal/Lignite |
| B03 | Fossil Coal-derived gas |
| B04 | Fossil Gas |
| B05 | Fossil Hard coal |
| B06 | Fossil Oil |
| B07 | Fossil Oil shale |
| B08 | Fossil Peat |
| B09 | Geothermal |
| B10 | Hydro Pumped Storage |
| B11 | Hydro Run-of-river and poundage |
| B12 | Hydro Water Reservoir |
| B13 | Marine |
| B14 | Nuclear |
| B15 | Other renewable |
| B16 | Solar |
| B17 | Waste |
| B18 | Wind Offshore |
| B19 | Wind Onshore |
| B20 | Other |
| B25 | Energy storage（平台代码表新增/可选；是否纳入 A75 西班牙数据待确认） |

## 5. 时间、单位和下载使用规则

- **时区**：OMIE 文件交付日按西班牙市场日；eSIOS同时返回本地带偏移 `datetime` 与 UTC `datetime_utc`，统一保存二者和原始 period。`Europe/Madrid` 夏令时为 UTC+02:00、冬令时为 UTC+01:00；不得把 DST 重复小时压成唯一本地字符串。
- **价格与能量**：OMIE价格文件的规范单位为 EUR/MWh；容量带价格规则单位为 EUR/MW；eSIOS必须优先读取每个指标的 `magnitud`，不能因中文名称自行套单位。REData发电结构页面使用 GWh，但本轮小时请求失败、日请求 `magnitude=null`，不能把该 widget 当作 MW；ENTSO-E A75 R3字段明确为 `ActualGenerationOutput[MW]`。
- **区域**：OMIE至少区分 ES/PT；eSIOS指标的 `geo_trunc`/`geos`决定 country/electric system/peninsular；REData显式使用 `geo_limit=peninsular` 或 national 默认值。不得把 peninsular、national、Iberian bidding zone 和单个 UP 混为一个区域。
- **临时/最终**：`values_updated_at`、REData `last-update`、文件修改时间和 `publication_date` 都是时间线索，不是统一 final flag。最终性必须按各指标或文件版本核对。
- **历史与回测**：OMIE 可见公共文件目前覆盖最近六个滚动年度；eSIOS/REData的“可查询”不自动证明完整历史。决策输入与事后最终结算序列须分开保存。

## 6. 推荐的第一批分析输入

1. 先下载并哈希保存 OMIE 2026-08 全部 DA、IDA1/2/3、IDC 文件；文件目录已经证明整月文件名存在且无认证要求。
2. 无 token 先验证 ENTSO-E网页的 Spain/BZN|ES A75 页面；随后申请 REST/FMS 权限，用 `A75+A16+A01+in_Domain=10YES-REE------0` 请求 2026-08 月度/逐日数据，保存 `UpdateTime(UTC)`和原始 CSV/XML哈希。
3. 申请 eSIOS personal token 后，只做元数据请求：indicator name、ID、`magnitud`、`geos`、values、`values_updated_at`；不得把 token 写入仓库或日志。
4. 依次验证 632/633/634、682/683、1293 和各 P48 ID；再用名称搜索闭合 aFRR requirement、activation energy、imbalance price 的候选 ID。
5. REData `estructura-generacion` 当前仅作为失败/对照记录；待REE修复 HTTP 400或提供明确的可用 widget 后再重新验证，不用 day响应推导小时出力。

## 7. 证据和未决项指引

完整来源登记见 [spain_data_api_sources.md](spain_data_api_sources.md)，逐项待确认、关闭测试和优先级见 [spain_data_api_open_questions.md](spain_data_api_open_questions.md)。
