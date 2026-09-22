# 西班牙数据接口官方来源登记（ES-DATA-01）

访问日期统一为 **2026-09-04（Europe/Madrid）**。本登记只把监管机构、TSO、NEMO/交易所的一方资料作为关键事实证据；候选 indicator ID 若没有一方指标表或实测元数据支持，保持“待确认”。eSIOS 文档中的示例 `x-api-key` 未复制，未读取、暴露或写入任何真实 token。

## 1. 一方来源清单

| source_id | 机构 | 标题/类型 | 发布日期或生效日期 | 官方 URL | 原文位置 | 本任务采用的证据 | 可信度 |
|---|---|---|---|---|---|---|---|
| `S-OMIE-FILE-ACCESS-2026` | OMIE | File access / Acceso a ficheros（动态目录） | 持续维护；目录样本改动时间为 2026-08-01—09-03 | [OMIE file access](https://www.omie.es/en/file-access-list)；[DA目录](https://www.omie.es/en/file-access-list?dir=+Day-ahead+market+hourly+prices+in+Spain&parents=%2FDay-ahead+Market%2F1.+Prices&realdir=marginalpdbc)；[IDA目录](https://www.omie.es/es/file-access-list?dir=Precios+del+mercado+intradiario+de+subastas+en+Espa%C3%B1a&parents=%2FMercado+Intradiario%2F1.+Precios&realdir=marginalpibc)；[IDC目录](https://www.omie.es/en/file-access-list?dir=Maximum%2C+minimum+and+weighted+price+for+each+period+of+the+continuous+intraday+market&parents=%2FContinuous+Intraday+Market%2F1.+Prices&realdir=precios_pibcic) | 各目录的文件名表；DA目录列出 `marginalpdbc_20260801.1`—`...20260831.1`，IDA目录列出每日 `marginalpibc_20260801{01,02,03}.1`—`...20260831{01,02,03}.1`，IDC目录列出 `precios_pibcic_20260801.1`—`...20260831.1` | 无凭据、逐日文件存在和 2026-08 可下载性；直接下载 URL 的 `filename`/`parents` 参数 | 已确认 |
| `S-OMIE-FORMATS-V31-2025` | OMIE | *Formatos de intercambio de información del mercado eléctrico* Vol. I–Mercado, v3.1 | 2025-04-07（PDF版本日期） | [OMIE format PDF](https://www.omie.es/sites/default/files/2024-03/Formatos_Intercambio_OM_Vol_I-Mercado.pdf) | §3.3.14（PDF p.112）MARGINALPDBC；§3.3.15（p.113）MARGINALPIBC；§3.3.16（p.114）PRECIOS_PIBCIC；目录还列出 PDBC/PIBC/PIBCIC 程序与曲线 | 文件名模式、ES/PT边际价、IDC最大/最小/加权均价字段、EUR/MWh；规范中的 period 示例为历史 hourly 1–100，不能替代当前 15-MTU 文件验证 | 已确认（格式）；当前 period 数需按文件核对 |
| `S-OMIE-IDA-INSTRUCTION-2024` | OMIE | Instrucción 1/2024，IDA implementation | 2024-06-07发布；IDA运行 2024-06-13，首个交付日 2024-06-14 | [OMIE Instrucción 1/2024](https://www.omie.es/sites/default/files/2024-06/INSTRUCCION_1_2024_ES.pdf) | §§2–4 / pp.1–4；IDA1、IDA2、IDA3 的时序及 provisional/definitive结果时间 | 三个拍卖会话的官方名称和启动时点；这是制度启动证据，不把旧 hourly horizon 外推至 2026 | 已确认 |
| `S-OMIE-SIDC-15MTU-2024` | OMIE | Nota informativa: Go-live 15 MTU in SIDC | 2024-10-29；15-MTU运行 2025-03-18（交付 2025-03-19） | [OMIE 15-MTU SIDC notice](https://www.omie.es/sites/default/files/2024-10/241029_NOTA_INFORMATIVA_GOLIVE_15MTU_SIDC_PT.pdf) | PDF正文 | 连续日内和 IDA 15分钟制度断点 | 已确认 |
| `S-OMIE-MD-15MTU-2025` | OMIE | Go-live MTU15 Mercado Diario | 2025-10-01；2025-09-30出清产生首个交付日的 96 个季度价格 | [OMIE MTU15 MD notice](https://www.omie.es/sites/default/files/2025-10/2501001_go_live_mtu15_md_es_vf.pdf) | PDF pp.1–2、正文“30 September/1 October 2025”段落 | 日前原生 15分钟断点；2025-10-01 前日前主要 hourly | 已确认 |
| `S-OMIE-MARKET-RESULTS-2026` | OMIE | Market results – IDA/continuous intraday price per contract | 持续维护；页面访问 2026-09-04 | [OMIE price per contract](https://www.omie.es/es/market-results/daily/continuous-intradaily-market/price-per-contract?date=2026-01-01&scope=daily) | “Subastas intradiarias/Price by session”；“Mercado intradiario continuo”说明 | IDC每合约 min/max/VWAP，成交量；IDA按 session/period 价格 | 已确认（字段概念）；下载文件字段以格式 PDF为准 |
| `S-ESIOS-API-HOME-2026` | REE/e·sios | API e·sios Documentation | 页面无单一发布日期；持续维护 | [eSIOS API docs](https://api.esios.ree.es/) | 首页 L0–L12（Indicator/Archive目录）；首页明确 “Personal token request (consultasios@ree.es)” | Indicator、Archive API入口和个人 token 要求；不把公开网页视为免认证 bulk API | 已确认 |
| `S-ESIOS-IND-RANGE-2026` | REE/e·sios | Indicator API – specific indicator filtering values by date range | 页面无单一发布日期；持续维护 | [Indicator date-range docs](https://api.esios.ree.es/doc/indicator/getting_a_specific_indicator_filtering_values_by_a_date_range.html) | 参数表 §§5–16；Request §§19–39；Response §§41–64 | `start_date/end_date`、`time_trunc`（含 fifteen_minutes/five_minutes/hour）、`geo_trunc`、`magnitud`、`datetime`、`datetime_utc`、`values_updated_at`；`x-api-key`认证头 | 已确认（路由/字段）；指标级覆盖开放 |
| `S-ESIOS-IND-SEARCH-2026` | REE/e·sios | Indicator API – search indicators by name | 页面无单一发布日期；持续维护 | [Indicator search docs](https://api.esios.ree.es/doc/indicator/search_indicators_by_name.html) | 参数/route/response sections；`GET /indicators?text=<text>&locale=<es|en>`，返回 name/short_name/id | 用于在拿到 token 后闭合 aFRR需求、激活、不平衡候选ID；不能使用二手列表替代搜索结果 | 已确认（搜索路由） |
| `S-ESIOS-ARCHIVE-2026` | REE/e·sios | Archive API – list by start/end/date_type | 页面无单一发布日期；持续维护 | [Archive `date_type=datos`](https://api.esios.ree.es/doc/archive/getting_a_list_of_archives_by_start_date%2C_end_date_and_date_type_datos.html)；[Archive `date_type=publicacion`](https://api.esios.ree.es/doc/archive/getting_a_list_of_archives_by_start_date%2C_end_date_and_date_type_publicacion.html)；[Download archive](https://api.esios.ree.es/doc/archive/download_archive.html) | 参数 §§7–15；route §§24–38；response §§40–63 | `date_type=datos|publicacion`、archive id、数据日期、`date_times`、`publication_date`、download URL；可分离数据日期和发布日期 | 已确认（归档元数据路由）；具体数据文件开放性待确认 |
| `S-ESIOS-QH-ADAPT-2022` | REE/e·sios | *Updating of the e.sios public website to the 15-min scheduling project (QH)* | 生效 2022-05-24；PDF未给单独发布日 | [QH adaptation PDF](https://api.esios.ree.es/documents/658/download?locale=en) | p.1（正文/生效日）；p.2 / Annex I（682/683/632/633/634、P48 71–105）；p.2–4/Annex II tertiary IDs | 指标官方名称和 ID：容量分配/价格、aFRR能量价格及 P48 技术计划；generation/consumption curve 改为 5分钟 | 已确认（官方表）；不代表每个 ID仍有完整公开历史 |
| `S-ESIOS-SRS-GUIDE-2024` | REE/e·sios / System Operator | *Guía de implantación del Servicio de Regulación Secundaria en el sistema eléctrico español* | 2024-10（文档封面/页脚） | [SRS/aFRR guide PDF](https://api.esios.ree.es/documents/2399/download?locale=es) | p.3（§4.1，次日QH需求、14:45前）；pp.4–5（容量分配、MW、€/MW、独立上下边际价）；p.46（capacity settlement range/price）；pp.50–52（4秒控制周期、225 cycles/QH、ESECS/ESECB/PＭSECS/PＭSECB）；p.53（未遵循能量投标的 incumplimiento） | 需求发布时间、容量市场定价、能量激活计算与QH聚合、容量/能量单位语义；不虚构 indicator ID | 已确认（规则/字段语义）；公共接口映射待确认 |
| `S-ESIOS-PUBLIC-DOWNLOAD-2026` | REE/e·sios | Public downloads / Descargas | 持续维护；访问 2026-09-04 | [eSIOS downloads](https://www.esios.ree.es/es/descargas) | 页面过滤项“Publicación”（发布日期）与“Datos”（数据日期） | 公开文件检索入口；动态页面未作为整月文件清单唯一证据 | 已确认（入口） |
| `S-ESIOS-SUPPLY-CURVES-2024` | REE/e·sios | aFRR reserve bid curves public page | 2024-11-20起公开 `Curvas_Ofertas_aFRR`（页面说明） | [eSIOS supply curves](https://www.esios.ree.es/es/curvas-de-ofertas?date=2025-12-21T01%3A00&id=29) | 页面说明/曲线选择器 | 证明 aFRR offer curve 有公开下载文件；不是 awarded/activated energy 的替代品 | 已确认（offer curve范围） |
| `S-REE-REDATA-API-2026` | REE / Red Eléctrica | REData API | 页面无单一发布日期；持续维护 | [REData API](https://www.ree.es/en/datos/apidata) | “REData API” §§14–22；headers §§46–50；query §§71–126；examples §§143–161；response §§163–200 | GET `/lang/datos/{category}/{widget}`；ISO start/end；hour/day/month/year；electric_system/geo_limit；JSONAPI `last-update`、`magnitude`、values、cache meta；无 token说明 | 已确认（通用接口） |
| `S-REE-GEN-STRUCTURE-2026` | REE / REData | Estructura de la generación por tecnologías | 页面持续维护；访问 2026-09-04 | [Generation structure](https://www.ree.es/es/datos/generacion/estructura-generacion) | 页面技术选择、系统选择、下载按钮及 “Provisionales/Programados/Previstos”；无下划线日期为 definitive 的页面说明 | 实际按技术发电结构的官方 widget；页面为 GWh口径并有 provisional/definitive 提示。但本轮公开 API 实测中，2026-08 `time_trunc=hour` 返回 HTTP 400，`time_trunc=day` 虽成功但 `magnitude=null`；不能作为当前小时级实际出力源 | 已确认（widget/页面字段）；当前小时响应不可用 |
| `S-REE-REALTIME-CURVES-2026` | REE / System Operation | Curvas de demanda y producción en tiempo real | 页面持续维护；访问 2026-09-04 | [Real-time demand and production curves](https://www.ree.es/es/operacion/sistema-electrico/demanda-y-produccion-en-tiempo-real) | 正文第 23–26 行：“curves update every five minutes”; demand real/forecast/scheduled and technology components；第40–41行 operational program定义 | 实时负荷和技术曲线 5分钟公开可视化；不自动等于历史 bulk API | 已确认（实时页面）；历史 API 待确认 |
| `S-ENTSOE-A75-ITEM-2026` | ENTSO-E Transparency Platform | *Actual Generation per Production Type [16.1.B&C]* | 2026-06-29更新 | [Actual Generation per Production Type](https://transparencyplatform.zendesk.com/hc/en-us/articles/16648290299284-Actual-Generation-per-Production-Type-16-1-B-C-) | “Aggregated generation per type” §§20–32；Spain (ES)说明 §§45–60 | 官方定义：实际聚合净发电 MW/市场时段/技术；H+1；平均瞬时净出力；小规模可估计；Spain公开值说明为 public grid 的 aggregated real-time set points、not updated | 已确认（但 Spain setpoint 语义不是项目结算计量） |
| `S-ENTSOE-A75-R3-SPEC-2025` | ENTSO-E Transparency Platform | `AggregatedGenerationPerType_16.1.B_C_r3` File Library specification | 2025-06-24更新 | [R3 CSV extract specification](https://transparencyplatform.zendesk.com/hc/en-us/articles/36493702227729-AggregatedGenerationPerType-16-1-B-C-r3) | 表格 §§23–43 | CSV字段：DateTime(UTC)、ResolutionCode PT15M/PT30M/PT60M、AreaCode/AreaType、ProductionType、ActualGenerationOutput[MW]、UpdateTime(UTC)；Spain ES示例 | 已确认（字段/粒度） |
| `S-ENTSOE-DDD-V3R4-2024` | ENTSO-E | *Detailed Data Descriptions* MoP v3r4 | 约2024（PDF v3r4；访问 2026-09-04） | [MoP Ref2 DDD v3r4 PDF](https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf) | §3.12，PDF pp.74–75（网页解析 P72–P74） | A75/16.1.b&c的 H+1、MW、locally aggregated、average instantaneous output、small-scale estimate和“usually no update”；风光允许按测量多次更新 | 已确认（规则/计算语义） |
| `S-ENTSOE-DOC-TYPE-2023` | ENTSO-E Transparency Platform | DocumentType code list | 2023-05-30更新 | [DocumentType](https://transparencyplatform.zendesk.com/hc/en-us/articles/15857043092756-DocumentType) | 表格 | `A75=Actual generation per type`；并列列出 A73、A74、A83/A84/A85 等，防止把 actual generation、forecast、balancing 混淆 | 已确认 |
| `S-ENTSOE-GEN-LOAD-PIG-2013` | ENTSO-E | *Generation and Load Process Implementation Guide* | 2013-09-20（V3R0） | [Generation and Load Process Implementation Guide](https://eepublicdownloads.entsoe.eu/clean-documents/pre2015/resources/Transparency/MoP_Ref_05_-_gl-market-document_V3R0-2013-09-20.pdf) | §4.3.5.1，PDF p.17，generation dependency table | 旧版技术依赖表将 `A75`、realised `A16`、`InBiddingZone_Domain`、`mktPSRType.psrType` 和 PT15M/PT30M/PT60M列为 actual-generation请求属性；A01/A93/A94等业务类型需以当前服务端响应复核 | 已确认（技术线索；版本较旧） |
| `S-ENTSOE-PSRTYPE-2024` | ENTSO-E Transparency Platform | PsrType code list | 2024-10-11更新 | [PsrType](https://transparencyplatform.zendesk.com/hc/en-us/articles/15856995130004) | 表格 | B01–B20技术类型；B25 Energy storage；A75按 `psrType`筛选时的官方枚举 | 已确认（代码表）；西班牙每项是否返回待实测 |
| `S-ENTSOE-AREA-EIC-2023` | ENTSO-E Transparency Platform | Area List with Energy Identification Code (EIC) | 2023-05-30更新 | [Area/EIC list](https://transparencyplatform.zendesk.com/hc/en-us/articles/15885757676308-Area-List-with-Energy-Identification-Code-EIC) | “Area type” definitions；EIC table `10YES-REE------0` row | Spain (ES)的 EIC `10YES-REE------0` 同时映射 `BZN\|ES`、`CTA\|ES`、`LFA\|ES`、`LFB\|ES`、`MBA\|ES`、`SCA\|ES`；A75请求需明确 area type/parameter含义 | 已确认 |
| `S-ENTSOE-REST-ENDPOINT-2023` | ENTSO-E Transparency Platform | Request Endpoint / Query via Web Browser | 2023-06-05更新 | [Request Endpoint](https://transparencyplatform.zendesk.com/hc/en-us/articles/15696677194644-Request-Endpoint)；[Query via browser](https://transparencyplatform.zendesk.com/hc/en-us/articles/15854421431060-Query-via-Web-Browser) | Production endpoint、GET示例 | REST生产端点 `https://web-api.tp.entsoe.eu/api`；查询使用 `securityToken`、documentType/processType/area/time参数 | 已确认（认证接口） |
| `S-ENTSOE-REST-TIME-2026` | ENTSO-E Transparency Platform | Request Parameters – Time Interval / Response Time Zone | 2025-12-04至2026-02-17更新 | [Time interval](https://transparencyplatform.zendesk.com/hc/en-us/articles/12783280128404-Request-Parameters-Time-Interval)；[Response timezone](https://transparencyplatform.zendesk.com/hc/en-us/articles/12786431986964-Response-Time-Zone) | §§关于 `periodStart/periodEnd`、`timeInterval`、UTC | GET `periodStart/periodEnd=yyyyMMddHHmm`；所有时间响应UTC；日/周/月返回按区域市场日映射，需保留 Spain CET/CEST | 已确认 |
| `S-ENTSOE-REST-TOKEN-2026` | ENTSO-E Transparency Platform | How to get security token | 2026-01-28更新 | [Security token process](https://transparencyplatform.zendesk.com/hc/en-us/articles/12845911031188-How-to-get-security-token) | §§23–87 | 先注册，再发邮件申请 RESTful API access，约3个工作日后在 My Account 生成 token；本任务不申请/读取真实 token | 已确认 |
| `S-ENTSOE-FMS-GUIDE-2026` | ENTSO-E Transparency Platform | File Library Guide | 2026-04-10更新 | [File Library guides](https://transparencyplatform.zendesk.com/hc/en-us/sections/36528267409169-File-Library-guides) | File Library Guide 的 extract table、API、limits、format章节 | `AggregatedGenerationPerType_16.1.B_C_r3`为 monthly CSV；FMS使用 Keycloak登录 token；CSV UTF-8、tab-delimited；100 requests/min/user limit | 已确认（下载机制）；2026-08文件未实测 |
| `S-ENTSOE-TP-HELP-2026` | ENTSO-E Transparency Platform | Help page / distribution channels | 2026-03-31更新 | [Transparency Platform Help](https://transparencyplatform.zendesk.com/hc/en-us/articles/17260622859412-Transparency-Platform-Help-page) | §§27–55；Generation extract table | 官网提供网页导出、REST API和File Library CSV；Generation中列出 `AggregatedGenerationPerType_16.1.B_C_r3` | 已确认（渠道） |
| `S-ENTSOE-RATE-REJECTION-2025` | ENTSO-E Transparency Platform | Request Rejections / API Rate Limit | 2025-12-24更新 | [Request rejections](https://transparencyplatform.zendesk.com/hc/en-us/articles/12783463360532-Request-Rejections)；[API rate limits](https://transparencyplatform.zendesk.com/hc/en-us/articles/12783148966036-API-Rate-Limit-Part-1) | date range/rejection examples；rate-limit §§1–4 | 旧/通用帮助确认超一年窗口会拒绝；R3 API token限额400 requests/min、超限约10分钟临时封禁；实际生产应以当前响应为准 | 已确认（限制页面） |
| `S-CNMC-BAL-DISCLOSURE-2022` | CNMC | CNMC/BOE balancing-information disclosure resolution | 2022 PDF；正式生效版本和修订需按 BOE 再核对 | [CNMC balancing disclosure PDF](https://www.cnmc.es/sites/default/files/4005106.pdf) | §1.12 “Banda de regulación secundaria”；§1.13.1 RR；PDF约 p.41309（网页检索版） | OS在容量分配后约30分钟公布需求/结果/边际价，RR能量结果不迟于30分钟；参与者级细节有公开时点要求 | 部分确认（PDF需与现行BOE版本复核）；不用于闭合 eSIOS indicator ID |
| `S-REE-MARKETS-PRICES-2026` | REE | Mercados y precios page | 持续维护；页面访问 2026-09-04 | [REE markets and prices](https://www.esios.ree.es/es/mercados-y-precios?date=31-07-2026&q=%2F) | “Programación en Mercado de Producción”；“Precio de los desvíos en tiempo real” | 市场结构、偏差=计划与实测差额、P.O.14.4价格概念；不据此推断 763/764 ID | 已确认（概念） |

### 1.1 本轮公开接口可访问性实测（本地验证，不是第一方定义）

验证日期：**2026-09-04**。对 REData 官方 widget 使用同一 2026-08 日期窗口做了最小 GET 验证：

```text
https://apidatos.ree.es/es/datos/generacion/estructura-generacion
  ?start_date=2026-08-01T00:00&end_date=2026-08-31T23:59&time_trunc=hour
=> HTTP 400

https://apidatos.ree.es/es/datos/generacion/estructura-generacion
  ?start_date=2026-08-01T00:00&end_date=2026-08-31T23:59&time_trunc=day
=> HTTP success; JSON `magnitude=null`
```

该观测只说明本次请求无法形成可解释的小时级序列；没有保存整月响应，也不能据此断言 REE 历史数据不存在。真实响应如后续保存，应记录 URL 参数、HTTP 状态、响应哈希和获取时间；本轮未写入 `data/raw/ES`。

### 1.2 本轮带 REE key 的 eSIOS 实测（2026-09-05）

从项目外部凭据文件 `data/API_Key.md` 的 `## REE APIKey` 段落读取 key（不写入仓库输出）。indicator 1293 元数据和 15 分钟历史样本均返回 HTTP 200；随后对 37 个指标按月执行 481 个请求，全部 HTTP 200。处理结果和缺口统计见 `project/review_ES_ESIOS_20250701_20260731_2026-09-05.md`。

本轮确认的可请求指标包括：aFRR 630/631/632/633/634/2130/680/681/682/683，失衡价格 763/764，负荷 1293，P48 技术计划 71–94。响应中保留 `magnitud`、`datetime`、`datetime_utc`、`geo_id`、`geo_name` 和 `values_updated_at`；`magnitud` 文本没有统一 SI 单位字段，不能自行把所有 `Energía` 转换为 MW/MWh。P48 名称为 `Generación programada`，本轮作为计划序列，不作为实际测量出力。

## 2. 关键事实—证据映射

| claim_id | 规则/数据事实（仅事实） | 证据 source_id / 位置 | 研究解释与边界 | 置信度 |
|---|---|---|---|---|
| `ES-DATA-C01` | OMIE公开目录存在 DA 文件 `marginalpdbc_20260801.1`—`...20260831.1` | `S-OMIE-FILE-ACCESS-2026`，DA目录文件名表 | 样本/目录存在不等于下载后每行均无空值；应保留文件版本 | confirmed |
| `ES-DATA-C02` | 2026-08每个交付日存在 IDA1/2/3 文件 | `S-OMIE-FILE-ACCESS-2026`，IDA目录（如 08-01 p.行 141–143、08-31 行 52–54） | 18 bytes 的空文件/无成交 session 不能当成缺失下载；解析应记录文件大小与状态 | confirmed |
| `ES-DATA-C03` | 2026-08每日存在 IDC max/min/VWAP 文件 | `S-OMIE-FILE-ACCESS-2026`，IDC目录文件名表 | VWAP是交易量加权字段，不是简单平均；以 `MedioES/PT/MO` 原字段为准 | confirmed |
| `ES-DATA-C04` | IDA与连续日内 15-MTU 于 2025-03-18运行 | `S-OMIE-SIDC-15MTU-2024`正文 | 2025-03-18前 IDA/IDC历史须按小时/制度旧版本切片 | confirmed |
| `ES-DATA-C05` | 日前 15-MTU 于 2025-10-01运行，首个交付日有96季度价格 | `S-OMIE-MD-15MTU-2025`正文 pp.1–2 | 2025-10-01前 DA不应插值后伪装为原生 QH | confirmed |
| `ES-DATA-C06` | OMIE文件名与 price字段规范：`marginalpdbc`、`marginalpibc`、`precios_pibcic`，价格 EUR/MWh | `S-OMIE-FORMATS-V31-2025` §§3.3.14–3.3.16，pp.112–114 | PDF period示例历史上1–100，当前文件需按实际 period解析 | confirmed |
| `ES-DATA-C07` | eSIOS Indicator API允许日期范围和 fifteen_minutes/five_minutes/hour聚合，并返回本地/UTC datetime | `S-ESIOS-IND-RANGE-2026` §§5–16、§§41–64 | API支持的 `time_trunc` 是通用选项，不保证每项指标都有原生QH/完整历史 | confirmed |
| `ES-DATA-C08` | eSIOS需 personal token，申请邮箱为 consultasios@ree.es | `S-ESIOS-API-HOME-2026` L0–L2；`S-ESIOS-IND-RANGE-2026` Request headers | 无 token 时不下载 eSIOS 指标，不复制示例 key | confirmed |
| `ES-DATA-C09` | eSIOS Archive API可以按数据日期或发布日期查询，并返回 publication_date和download | `S-ESIOS-ARCHIVE-2026` 参数/response章节 | 可建立发布延迟审计，但不能从 archive schema推断最终性 | confirmed |
| `ES-DATA-C10` | 632/633/634分别为 aFRR secondary reserve band allocation up/down及 band price；682/683为 secondary regulation price up/down；P48 IDs 71–105和合计IDs在 QH附件 | `S-ESIOS-QH-ADAPT-2022` p.2 Annex I | 官方附件确认名称/ID，不确认当前 response 的 magnitude、公开权限和历史完整性 | confirmed（ID表） |
| `ES-DATA-C11` | aFRR次日需求按QH发布，14:45前；上/下容量独立边际价，能量计算4秒并按QH聚合225 cycles | `S-ESIOS-SRS-GUIDE-2024` p.3 §4.1、p.4/46、pp.50–52 | 规则字段可用于数据语义；需求候选 630/631、激活候选680/681需通过官方搜索/API闭合 | confirmed（规则）；ID unresolved |
| `ES-DATA-C12` | REData仅GET，路径 `/lang/datos/{category}/{widget}`，可 hour/day/month/year，JSONAPI含last-update/cache | `S-REE-REDATA-API-2026` §§14–22、§§71–126、§§163–200 | 请求粒度和 widget 路由不等于原始测量粒度；要保存 magnitude和last-update | confirmed |
| `ES-DATA-C13` | REData `generacion/estructura-generacion`页面提供按技术发电结构、GWh、provisional/definitive提示；本轮 2026-08 `time_trunc=hour` 公开请求 HTTP 400，`day` 请求成功但 `magnitude=null` | `S-REE-GEN-STRUCTURE-2026` 页面说明；本地公开 API 验证记录（2026-09-04） | 失败响应是当前访问状态记录，不是 REE 对数据不存在的规则声明；在获得可解释 `magnitude` 前，不能用该 widget 形成小时 MW/GWh 序列 | confirmed（页面和失败实测）；小时源不可用 |
| `ES-DATA-C14` | REE实时需求/生产曲线每5分钟更新，含real/forecast/scheduled demand和技术组件 | `S-REE-REALTIME-CURVES-2026` 正文第23–26、40–41行 | 公共实时图适合人工核对；历史下载需另找 indicator/widget | confirmed |
| `ES-DATA-C15` | 公开材料说明二次调频容量/部分RR结果有约30分钟披露要求 | `S-CNMC-BAL-DISCLOSURE-2022` §1.12/§1.13.1 | CNMC PDF版本和现行修订需复核；不能将约30分钟当成API实际延迟 | provisional |
| `ES-DATA-C16` | REE市场页确认实时偏差价格按 P.O.14.4、偏差为计划与实测的差额 | `S-REE-MARKETS-PRICES-2026` “Precio de los desvíos en tiempo real” | 不能用页面概念确认候选 763/764 的 ID、单/双价或 finality | confirmed（概念）；ID unresolved |
| `ES-DATA-C17` | REData `estructura-generacion` 的 2026-08 小窗口公开验证：`time_trunc=hour` 返回 HTTP 400；`time_trunc=day` HTTP成功但 JSON `magnitude=null` | `S-REE-GEN-STRUCTURE-2026`；本地验证日期 2026-09-04（不含 token、未保存凭据） | 这是可复现性/可用性记录，不是官方数据定义；替代源优先使用 ENTSO-E A75，REData仅保留失败控制记录 | confirmed（访问观测） |
| `ES-DATA-C18` | ENTSO-E 的 `A75` 是 Actual generation per type；`A16` 为 realised process；`A01`（Production）以及旧依赖表中的 A93/A94（风/光业务类型）可作为请求属性线索；技术实际数据支持 PT15M/PT30M/PT60M | `S-ENTSOE-DOC-TYPE-2023` 表；`S-ENTSOE-GEN-LOAD-PIG-2013` §4.3.5.1 p.17；`S-ENTSOE-DDD-V3R4-2024` §3.12 pp.74–75；`S-ENTSOE-A75-R3-SPEC-2025` 字段表 | A93/A94来自较旧依赖表，当前服务端是否仍接受需以响应复核；最终请求仍应检查返回 `ResolutionCode` | confirmed（规范/旧版属性线索）；API响应待 token |
| `ES-DATA-C19` | R3 monthly extract字段包括 `DateTime(UTC)`、`ResolutionCode`（PT15M/PT30M/PT60M）、`AreaCode`/`AreaTypeCode`、`ProductionType`、`ActualGenerationOutput[MW]`、`UpdateTime(UTC)` | `S-ENTSOE-A75-R3-SPEC-2025` 表格 §§23–43 | `ActualGenerationOutput[MW]`是平台聚合净实际出力字段；不得将它误标成项目电表或结算量 | confirmed（字段）；2026-08文件待下载 |
| `ES-DATA-C20` | Spain (ES) EIC 为 `10YES-REE------0`，Area list 映射到 `BZN\|ES`、`CTA\|ES`、`LFA\|ES`、`LFB\|ES`、`MBA\|ES`、`SCA\|ES` | `S-ENTSOE-AREA-EIC-2023` Area type definitions 和 EIC table | BZN/CTA/CTY不是同一层级；采集时应保留 `AreaTypeCode`，不能只保存 ES文字标签 | confirmed（代码表）；具体 A75区域返回待实测 |
| `ES-DATA-C21` | A75聚合值按市场时段平均可用瞬时净出力计算，通常 H+1；未知/小规模可估计；通常不更新，风光可按测量多次更新。Spain说明称公开数据是 public grid aggregated real-time set points，且不更新 | `S-ENTSOE-A75-ITEM-2026` §§20–60；`S-ENTSOE-DDD-V3R4-2024` §3.12 pp.74–75 | H+1是官方发布目标/定义，不等于本地首次可见时间；Spain setpoint语义使该序列只能称平台 actual，不应直接称结算计量 actual | confirmed（定义）；适用性需业务核对 |
| `ES-DATA-C22` | ENTSO-E REST生产端点为 `https://web-api.tp.entsoe.eu/api`；REST/FMS需 security/Keycloak token；官方流程为注册并申请 RESTful API access；本任务未读取真实 token | `S-ENTSOE-REST-ENDPOINT-2023`；`S-ENTSOE-REST-TOKEN-2026`；`S-ENTSOE-FMS-GUIDE-2026` | 因无凭据，本轮不能证明 2026-08 的 API响应、文件存在、记录数或完整性；只能确认接口和数据项可请求路径 | confirmed（认证要求）；2026-08待实测 |

## 3. 请求参数和样本 URL登记

### 3.1 OMIE 2026-08无凭据文件样本

以下 URL 均来自官方目录的 `file-download` 链接；HTTP 文件内容应由实际抓取端保存，不将网页抓取失败误判为文件不存在。

| 数据 | 示例直接 URL | 官方目录样本 |
|---|---|---|
| DA 2026-08-01 | `https://www.omie.es/en/file-download?filename=marginalpdbc_20260801.1&parents=marginalpdbc` | [DA目录](https://www.omie.es/en/file-access-list?dir=+Day-ahead+market+hourly+prices+in+Spain&parents=%2FDay-ahead+Market%2F1.+Prices&realdir=marginalpdbc) |
| IDA1 2026-08-01 | `https://www.omie.es/es/file-download?filename=marginalpibc_2026080101.1&parents=marginalpibc` | [IDA目录](https://www.omie.es/es/file-access-list?dir=Precios+del+mercado+intradiario+de+subastas+en+Espa%C3%B1a&parents=%2FMercado+Intradiario%2F1.+Precios&realdir=marginalpibc) |
| IDA2 2026-08-01 | `https://www.omie.es/es/file-download?filename=marginalpibc_2026080102.1&parents=marginalpibc` | 同上 |
| IDA3 2026-08-01 | `https://www.omie.es/es/file-download?filename=marginalpibc_2026080103.1&parents=marginalpibc` | 同上 |
| IDC 2026-08-01 | `https://www.omie.es/en/file-download?filename=precios_pibcic_20260801.1&parents=precios_pibcic` | [IDC目录](https://www.omie.es/en/file-access-list?dir=Maximum%2C+minimum+and+weighted+price+for+each+period+of+the+continuous+intraday+market&parents=%2FContinuous+Intraday+Market%2F1.+Prices&realdir=precios_pibcic) |

### 3.2 eSIOS 请求模板（无真实 token）

```text
GET https://api.esios.ree.es/indicators/{ID}
    ?start_date=2026-08-01T00:00:00+02:00
    &end_date=2026-08-31T23:59:59+02:00
    &time_trunc=fifteen_minutes
    &locale=es
Header: Accept: application/json, application/vnd.esios-api-v1+json
Header: Content-Type: application/json
Header: x-api-key: <PERSONAL_TOKEN_NOT_STORED>
```

归档元数据：

```text
GET https://api.esios.ree.es/archives
    ?start_date=2026-08-01T00:00:00+00:00
    &end_date=2026-08-31T23:59:59+00:00
    &date_type=datos
    &locale=es
```

### 3.3 REData 请求模板（无 token）

```text
GET https://apidatos.ree.es/es/datos/generacion/estructura-generacion
    ?start_date=2026-08-01T00:00
    &end_date=2026-08-31T23:59
    &time_trunc=hour
```

可选区域参数：`geo_trunc=electric_system&geo_limit=peninsular&geo_ids=<官方 geo_id>`；不要自行猜测 `geo_id`。API文档明确无地域参数时由 widget 决定 national 或 peninsular 默认值。

### 3.4 ENTSO-E Actual Generation per Production Type 请求模板（无真实 token）

REST 查询使用官方生产端点；下面仅登记参数形状，不执行也不保存真实凭据：

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

官方 R3 File Library 抽取名：`AggregatedGenerationPerType_16.1.B_C_r3`。文件为 UTF-8、tab-delimited monthly CSV，字段包含 `DateTime(UTC)`、`ResolutionCode`、`AreaTypeCode`、`ProductionType`、`ActualGenerationOutput[MW]` 和 `UpdateTime(UTC)`。本轮未用 token 取得 REST XML/CSV 或 2026-08 文件，故下载状态记为待确认；不要把上述模板中的占位符替换成仓库内密钥。

## 4. 研究解释和建模边界（不是规则事实）

- OMIE 文件可直接做市场层回测，但 OMIE ES价格、PT价格、共同耦合结果和跨区容量不应被混成单一“西班牙系统价”。
- aFRR capacity price、capacity awarded、activation energy、energy price 是不同字段；`632/633/634`不能替代 activation volume，`682/683`不能自动解释为 accepted energy volume。
- REData `estructura-generacion`页面的 GWh 是能量口径；本轮 hour=HTTP 400、day=`magnitude=null`，因此当前不能转换出力或宣称小时可下载。若后续接口恢复，仍必须以 API `magnitude`和时间长度确认并保留原始 GWh。
- ENTSO-E A75 是当前最明确的官方 15 分钟/小时技术聚合替代源；但 Spain页面的 setpoint/no-update说明意味着它更适合系统级曲线、交叉核对和建模输入，不能未经核对替代项目级计量或不平衡结算数据。
- eSIOS `datetime`（带偏移）和 `datetime_utc`必须同时保留。Europe/Madrid 的 DST 变化意味着本地日不一定能用固定 24 小时/96 QH 处理。
- `publication_date`、文件修改时间、`values_updated_at`/`last-update`只能形成发布轨迹，不能自行标记最终结算值；所有最终性和 revision 处理属于待确认问题。

## 5. 二手资料使用限制

本任务没有把二手博客、论文或开源库作为关键字段证据。旧研究中列出的 `630/631`、`680/681`、`763/764`保留为候选线索，但由于本次未从官方 ID表或带认证 API response闭合，目录和问题清单都标为待确认；不得直接写入生产采集口径。

## 6. 检索日志

| 日期 | 方向 | 官方检索/核验内容 | 结果 |
|---|---|---|---|
| 2026-09-04 | OMIE | file-access 目录、`marginalpdbc`、`marginalpibc`、`precios_pibcic` | 找到 2026-08-01—31 全部目标文件名和 file-download URL |
| 2026-09-04 | OMIE | format PDF v3.1、IDA/SIDC/MD 15-MTU 通知 | 闭合文件字段、单位和三个制度断点 |
| 2026-09-04 | REE/eSIOS | API首页、Indicator range/search、Archive docs | 闭合路由、参数、token要求、响应元数据；指标级 token 查询未执行 |
| 2026-09-04 | REE/eSIOS | QH adaptation PDF、SRS guide Oct 2024 | 闭合 632/633/634、682/683、P48 以及 QH/4-sec/225 cycles 规则语义 |
| 2026-09-04 | REE | REData API、generation structure、real-time curves | 闭合无 token GET、hour/day API选项、GWh/状态标记、实时5分钟曲线；小时整月 response未保存 |
| 2026-09-04 | REE | 对 `generacion/estructura-generacion` 做公开小窗口 API 验证（不读取 token） | `time_trunc=hour` 返回 HTTP 400；`time_trunc=day` HTTP成功但 `magnitude=null`；未写入 raw 文件，作为失败/可复现性记录 |
| 2026-09-04 | ENTSO-E Transparency Platform | A75数据项页、R3 CSV specification、DDD v3r4、DocumentType/PsrType/Area EIC、REST/FMS帮助 | 闭合 A75/A16/A01、PT15M/PT30M/PT60M、MW字段、Spain EIC、H+1/估计/更新语义及认证流程；未用 token，2026-08未实测 |
| 2026-09-04 | CNMC/REE | balancing disclosure、markets/prices pages | 取得约30分钟披露和P.O.14.4概念线索；正式版本/指标ID仍需复核 |
