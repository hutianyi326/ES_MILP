# ES-01 官方制度、规则版本与证据地图

> 研究基线：西班牙（ES）辅助服务及其直接相关平衡能量/不平衡机制；历史期 2025-01-01—2025-12-31；规则基准日 2026-08-11；研究对象为独立电化学储能。既有来源多于 2026-08-11 访问，ES-04/ES-05/ES-06 增补来源按各自 source block 的 `accessed_at` 记录（本轮增补主要为 2026-08-18）。现货子项目 ES-SP-01 的 OMIE/CNMC/BOE/REE/ENTSO-E/JAO 来源在文末以 `S-SP-*` 登记，专用于制度、主体和平台架构，不提前替代 ES-SP-02/03 的日前/日内参数研究。

## 1. 机构与规则层级（已确认）

| 层级/机构 | 作用（本项目范围） | 官方入口 |
|---|---|---|
| 欧盟委员会/ EUR-Lex | 《Regulation (EU) 2017/2195》（EBGL）规定平衡容量、平衡能量、欧洲平台、BRP/BSP 和 15 分钟 ISP 的共同框架（Arts. 1, 17–22, 49–55）。 | [EUR-Lex consolidated EBGL](https://eur-lex.europa.eu/eli/reg/2017/2195) |
| ACER | 批准跨 TSO 欧洲平衡平台实施框架（mFRRIF/aFRRIF/RRIF/INIF）及方法；2024 年西班牙 CNMC 决议引用 ACER 2020 框架。 | [ACER mFRR IF register](https://www.acer.europa.eu/electricity/market-rules/electricity-balancing/balancing-energy-platforms/5-mFRR-IF) |
| ENTSO-E | TSO 协作、欧洲平台技术/数据规范与平台状态；TERRE 页面记录 RR 平台 2025-12-30 停止运行。 | [ENTSO-E TERRE](https://www.entsoe.eu/network_codes/eb/terre/); [EDI balancing schemas](https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/) |
| MITECO/Secretaría de Estado de Energía | 以 BOE 决议批准系统运行程序（P.O.10.x 等）及计量/结算实施；2025-03-28 决议使十五分钟偏差结算计量程序生效。 | [BOE-A-2025-6693](https://www.boe.es/eli/es/res/2025/03/28/%282%29) |
| CNMC | 国家监管机构；批准 EBGL Art.18 的西班牙 BSP/BRP 条件、P.O. 方法和本地特定平衡产品。 | [CNMC Circular 3/2019 expediente](https://www.cnmc.es/expedientes/cirde01019); [CNMC balance conditions (2019)](https://www.cnmc.es/sites/default/files/2784234_0.pdf) |
| Red Eléctrica de España（REE） | 西班牙 TSO/系统运营商（OS）；提出条件和 P.O.、进行 BSP 预认证/激活/履约监测、运营 eSIOS 与平衡平台接口。 | [REE regulatory framework](https://www.ree.es/es/conocenos/marco-regulatorio); [REE balancing participation](https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance) |
| OMIE（OMI-Polo Español） | 西班牙/葡萄牙指定 NEMO，管理日前和日内市场；在本任务只作为平衡计划输入接口登记，现货机制排除。 | [OMIE about us](https://www.omie.es/es/sobre-nosotros) |

**层级解释（研究解释）**：EBGL/ACER 框架约束跨境标准产品；CNMC 决议将其转化为西班牙条件和 P.O.；MITECO/能源国务秘书处批准计量等系统运行 P.O.；REE 负责执行、数据和运营。来源之间不是并列“参考资料”，而是欧盟框架→国家监管决定/BOE→REE 操作文件的链条。

## 2. 来源登记（第一方）

### S-EBGL-2017（confirmed）

```yaml
source_id: S-EBGL-2017
institution: European Commission / EUR-Lex
title: Commission Regulation (EU) 2017/2195 of 23 November 2017 establishing a guideline on electricity balancing (consolidated 19 June 2022)
document_type: EU regulation (consolidated legal text)
publication_date: 2017-11-23
effective_from: 2017-12-18
effective_to: null
url: https://eur-lex.europa.eu/eli/reg/2017/2195
accessed_at: 2026-08-11
language: English (official EU text)
relevant_pages: HTML consolidated text
relevant_sections: Arts.1-2 (scope/definitions); 17 (BRP); 18 (national BSP/BRP terms); 19-22 (RR/mFRR/aFRR/IN platforms); 49-55 (imbalance calculation, ISP and prices)
notes: Binding EU baseline. The EUR-Lex consolidated page is an official reading/administrative consolidation tool; for legal effect, the original Regulation (EU) 2017/2195 and each amending regulation remain the controlling Official Journal texts. Article 18 national BSP/BRP terms and Articles 19-22 platform frameworks require Spanish CNMC/BOE implementation evidence.
historical_2025: yes
version_relation: EU baseline for all Spanish P.O./CNMC conditions
evidence_status: confirmed
```

### ES-06 官方数据接口与版本证据增补（访问日 2026-08-18）

以下来源只补充数据目录/版本元数据。`S-CNMC-2026-RT` 已发布但在 2026-08-11 基准日尚未生效，不得覆盖 2025 历史或基准日规则。

### S-REE-REData-API-2026（confirmed route; widget fields open）

```yaml
source_id: S-REE-REData-API-2026
institution: Red Eléctrica de España (REE)
title: REData API
document_type: public REST API documentation
publication_date: continuously maintained page; no single publication date shown
effective_from: current page at access; endpoint version not stated
effective_to: unknown
url: https://www.ree.es/es/datos/apidatos
accessed_at: 2026-08-18
relevant_sections: §§15-24 (GET /{lang}/datos/{category}/{widget}); §§79-126 (ISO start/end, hour/day/month/year, geo filters); §§164-200 (JSONAPI, last-update and cache-control)
notes: Confirms public GET widget endpoint and response metadata. It does not prove that a balancing widget, indicator ID, refresh delay, unit or 2025 retention is stable.
historical_2025: unknown; date filters exist but full balancing archive not verified
version_relation: data-portal interface layer
evidence_status: confirmed route; fields/delay/history open
```

### S-eSIOS-API-IND-2026（confirmed route; indicator metadata open）

```yaml
source_id: S-eSIOS-API-IND-2026
institution: REE / eSIOS
title: Indicator API — Search indicators by name
document_type: public API documentation
publication_date: continuously maintained page; example response has no publication date
effective_from: current API documentation at access
effective_to: unknown
url: https://api.esios.ree.es/doc/indicator/search_indicators_by_name.html
accessed_at: 2026-08-18
relevant_sections: §§8-12 (locale/text); §§15-34 (GET /indicators?text, x-api-key, JSON id response)
notes: API key and route are documented. The data catalogue does not assign indicator IDs until each target indicator is queried and its metadata/units/date coverage captured.
historical_2025: unknown
version_relation: eSIOS indicator interface
evidence_status: confirmed route; indicator IDs, units, delay, limits and revision policy open
```

### S-REE-DOWNLOAD-2026（confirmed access pattern; historical coverage open）

```yaml
source_id: S-REE-DOWNLOAD-2026
institution: REE / eSIOS
title: eSIOS public downloads (Descargas)
document_type: public data download portal
publication_date: continuously maintained page; no single publication date shown
effective_from: current portal at access
effective_to: unknown
url: https://www.esios.ree.es/es/descargas
accessed_at: 2026-08-18
relevant_sections: page controls for publication date/data date filters; public categories for markets, prices and operation
notes: Confirms public download access pattern only. Full 2025 retention, balancing-file completeness and republication history remain open.
historical_2025: unknown
version_relation: public data portal layer
evidence_status: confirmed access pattern; coverage/history open
```

### S-REE-LIQ-ACCESS-2026（confirmed private settlement access boundary）

```yaml
source_id: S-REE-LIQ-ACCESS-2026
institution: REE
title: Te ayudamos con tu liquidación
document_type: participant settlement access page
publication_date: continuously maintained page; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.ree.es/es/clientes/generador/acceso-a-tu-liquidacion
accessed_at: 2026-08-18
relevant_sections: §§53–64 (REE settlement responsibility and P.O.14.1/P.O.14.4 entry); §§71–80 (BRP private settlement ZIP access)
notes: Confirms that detailed BRP settlement files are permissioned; it does not make private files publicly downloadable.
historical_2025: participant access/history not verified
version_relation: settlement access layer for P.O.14.1/P.O.14.4
evidence_status: confirmed access boundary; public fields/history open
```

### S-REE-RT-FAQ-2026（confirmed operational entry; normative status limited）

```yaml
source_id: S-REE-RT-FAQ-2026
institution: REE
title: Cómo participar en los servicios de balance / FAQ
document_type: REE operational FAQ and participation page
publication_date: page accessed 2026-08-18; no single publication date shown
effective_from: current page at access; BOE/CNMC rules control legal effect
effective_to: unknown
url: https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance/como-participar-en-los-servicios-de-balance
accessed_at: 2026-08-18
relevant_sections: page statements on 1 MW, structural data, real-time telemetry, control centre, P.O.3.8 testing and SRAD habilitación
notes: Operational/interpretive entry only; it does not replace BOE/CNMC product qualification rules.
historical_2025: current FAQ; historical application not assumed
version_relation: REE operational entry for CNMC/BOE requirements
evidence_status: D/interpretive entry; normative status limited
```

### S-REE-LIQ-GUIDE-2024（confirmed as non-normative data guide）

```yaml
source_id: S-REE-LIQ-GUIDE-2024
institution: REE
title: Guía de ayuda para la comprobación de la liquidación de los servicios de ajuste del sistema (December 2024)
document_type: participant settlement verification guide (non-normative)
publication_date: 2024-12
effective_from: explanatory guide; P.O.14.1/P.O.14.4 remain controlling
effective_to: later versions may supersede guide
url: https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/normativa_guias/Guia_comprobacion_liquidacion_servicios_ajuste_sistema.pdf
accessed_at: 2026-08-18
relevant_pages: p.3 disclaimer; pp.4-6 reganeu/reganecuQH, rp48preccierre; pp.8-10 A1-A5/C1-C5, p48cierre, SIMEL, prdvsuqh/prdvbaqh/prdvdatos; pp.16-18 field table and rp48preccierre example
notes: Confirms file roles, settlement-stage labels and field names used to reproduce a BRP check. It does not make private BRP files public or define undocumented PDESV variants.
historical_2025: files may exist by participant access; public retention not verified
version_relation: data/settlement guide for P.O.14.1/14.4
evidence_status: confirmed file roles; access/history/revision open
```

### S-CNMC-2026-RT（confirmed future version; not effective at baseline）

```yaml
source_id: S-CNMC-2026-RT
institution: CNMC / BOE
title: Resolución de 19 de junio de 2026 (BOE-A-2026-14009), P.O.9.2 and P.O.14.4 real-time information penalties
document_type: CNMC resolution / operating-procedure amendment
publication_date: 2026-06-27 (BOE no.156, pp.89489-89524)
effective_from: 2026-09-01
effective_to: unknown
url: https://www.boe.es/eli/es/res/2026/06/19/(3)
accessed_at: 2026-08-18
relevant_pages: HTML §§388-391 (4–12-second realtime provision); §§419-439 (THIPh/THIQh, EHRPh/EHRQh, storage active saliente/entrante, 75% valid records); §§491-492 (M+1 publication); analysis lines 1125-1127 (effects 2026-09-01)
notes: Future-effective boundary only. Do not use its THIPh/THIQh/EHRPh/EHRQh fields, quality threshold or penalties for 2025 historical calculations or the 2026-08-11 baseline.
historical_2025: no
version_relation: future amendment to P.O.9.2/P.O.14.4 after S-CNMC-2025-VOLTAGE-13076
evidence_status: confirmed publication/effective date; future only
```

### ES-06 数据入口汇总（与 `data_catalog_and_version_timeline.md` 对齐）

| 数据层 | 官方入口 | 可确认内容 | 未确认内容（保持 open/provisional） |
|---|---|---|---|
| REData/eSIOS 公共 API | S-REE-REData-API-2026；S-eSIOS-API-IND-2026 | GET 路由、日期过滤、JSON response、indicator ID 查询入口 | 平衡指标 ID、单位、时区、刷新/发布延迟、revision、历史覆盖、API 限额 |
| 结算/偏差 | S-REE-LIQ-GUIDE-2024；REE liquidación access | `reganecuQH`/`reganeu`、`p48cierre`、`prdv*`、SIMEL、A1–A5/C1–C5；BRP 私有访问 | `PDESV/PDESVS/PDESVB` 精确含义、公共下载权限、修订覆盖 |
| QH/storage 计量 | S-MITECO-2025-ISP | 2025-05-01 生效；storage Activa saliente/entrante/reactiva、best value ≤24h、M+1/D+1 流程 | SIMEL 字段名、公开历史、异常/更正标志 |
| 2026 realtime | S-CNMC-2026-RT | 发布 2026-06-27，生效 2026-09-01；THIPh/THIQh/EHRPh/EHRQh 和 75% valid rule | 基准日以前不可使用；字段公开性 open |

### S-ACER-aFRR-IF（confirmed; EU framework, not standalone Spanish rule）

```yaml
source_id: S-ACER-aFRR-IF
institution: ACER
title: Implementation framework for the European platform for the exchange of balancing energy from aFRR (PICASSO), ACER Decisions 02/2020, 15/2022 and 08/2024
document_type: ACER implementation framework / amendment decisions
publication_date: 2020-01-24; amendments 2022-09-30 and 2024-07-05
effective_from: framework deadline 2022-07-24; latest amendment 2024-07-24 implementation deadline
effective_to: current framework status shown by ACER at access; future amendments must be checked
url: https://www.acer.europa.eu/electricity/implementation-monitoring/eb
accessed_at: 2026-08-11
language: English
relevant_pages: web §§118-133 (Article 21(1), Decision 02/2020, 15/2022, 08/2024); related approved framework link in ACER balancing platforms page
relevant_sections: aFRR Implementation Framework (PICASSO); ACER Decisions 02/2020, 15/2022, 08/2024
notes: Auditable EU platform framework and status source. It does not by itself determine Spanish BSP eligibility, capacity procurement or settlement; those require CNMC/BOE and REE implementation sources.
historical_2025: yes (PICASSO framework applicable after Spanish connection)
version_relation: EU platform layer under EBGL Art.21; Spanish implementation in S-CNMC-2024-MP/P.O.7.2
evidence_status: confirmed
```

### S-ACER-mFRR-IF（confirmed; EU framework, not standalone Spanish rule）

```yaml
source_id: S-ACER-mFRR-IF
institution: ACER
title: Implementation framework for the European platform for the exchange of balancing energy from mFRR (MARI), ACER Decisions 03/2020 and 14/2022
document_type: ACER implementation framework / amendment decisions
publication_date: 2020-01-24; amendment 2022-09-30
effective_from: implementation deadline 2022-07-24; amendment deadline 2022-09-30
effective_to: current framework status shown by ACER at access
url: https://www.acer.europa.eu/electricity/implementation-monitoring/eb
accessed_at: 2026-08-11
language: English
relevant_pages: web §§105-116 (Article 20(1), Decision 03/2020, 14/2022); latest framework direct document linked by ACER
relevant_sections: mFRR Implementation Framework (MARI); ACER Decisions 03/2020 and 14/2022
notes: Auditable EU platform framework and status source. Spanish P.O.7.3 determines local offer, qualification and fallback details.
historical_2025: yes (MARI operational in Spain from Dec-2024)
version_relation: EU platform layer under EBGL Art.20; Spanish implementation in S-CNMC-2024-11535-PO/P.O.7.3
evidence_status: confirmed
```

### S-ACER-RR-IF（confirmed; EU framework, historical Spanish use）

```yaml
source_id: S-ACER-RR-IF
institution: ACER / relevant NRAs
title: Implementation framework for the European platform for the exchange of balancing energy from Replacement Reserves (RR), amended 2023
document_type: RR implementation framework approved by relevant regulatory authorities
publication_date: initial approval 2019-01-15; amendment approval 2023-03-23; approved framework dated 2023-03-10
effective_from: 2020 platform operation; amended framework status through 2025-12-30 Spanish participation
effective_to: Spanish TERRE participation ended 2025-12-30; EU framework platform discontinuation boundary is separately recorded in S-ENTSOE-TERRE-2026
url: https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/MARKET-CODES/ELECTRICITY-BALANCING/02%20RR%20IF/Action-3a-RR-IF-Amended-proposal-approved.pdf
accessed_at: 2026-08-11
language: English
relevant_pages: PDF pp.1-2 (scope and contents); p.12 (Art.7 bid gate closure); pp.12-13 (Art.8 TSO gate closure); ACER status page §§88-104
relevant_sections: RRIF Arts.1,3,6-8,13; ACER balancing-platform status table
notes: Framework governs cross-TSO RR energy exchange and bid gates; it is not evidence of a Spanish local capacity market. Spanish P.O.3.3 and TERRE status control national applicability.
historical_2025: yes (Spanish TERRE operation until 2025-12-30)
version_relation: EU platform layer under EBGL Art.19; Spanish implementation in P.O.3.3
evidence_status: confirmed
```

### S-ACER-IN-IF（confirmed; EU framework, not BSP product）

```yaml
source_id: S-ACER-IN-IF
institution: ACER
title: Implementation framework for the European platform for the imbalance netting process (IN/IGCC), ACER Decisions 13/2020 and 16/2022
document_type: ACER implementation framework / amendment decisions
publication_date: 2020-06-24; amendment 2022-09-30
effective_from: implementation deadline 2021-06-24; operational status current at access
effective_to: current framework status shown by ACER at access
url: https://www.acer.europa.eu/electricity/implementation-monitoring/eb
accessed_at: 2026-08-11
language: English
relevant_pages: web §§135-147 (Article 22(1), Decision 13/2020, 16/2022); ACER balancing platforms page §§56-64
relevant_sections: IN Implementation Framework; imbalance-netting platform operation and status
notes: IN is TSO-to-TSO netting of opposite aFRR needs, not a local BSP capacity product. Spanish storage revenue cannot be inferred from this framework.
historical_2025: yes (IGCC interface active)
version_relation: EU platform layer under EBGL Art.22; Spanish interface in P.O.7.2/REE platform sources
evidence_status: confirmed
```

### S-CNMC-2019-BAL（confirmed）

```yaml
source_id: S-CNMC-2019-BAL
institution: CNMC
title: Resolución de 11 de diciembre de 2019: Condiciones relativas al balance para BSP y BRP en el sistema eléctrico peninsular español (DCOOR/DE/012/18)
document_type: CNMC resolution + approved national terms and conditions
publication_date: 2019-12-23 (BOE publication; resolution signed 2019-12-11)
effective_from: 2020-01-22 (30 days after BOE publication; confirm publication calculation in ES-02)
effective_to: amended by S-CNMC-2024-MP
url: https://www.cnmc.es/sites/default/files/2784234_0.pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: pp.1-3 (resolution); approved annex is linked from CNMC case DCOOR/DE/012/18
relevant_sections: Resolution pp.1-3, especially approval under EBGL Art.18 and CNMC competence; annex Art.2 (generation, demand and storage; aggregation)
notes: CNMC PDF contains the three-page resolution; full 30-page annex is available as associated document [CNMC Condiciones de balance](https://www.cnmc.es/sites/default/files/2784236_0.pdf), pp.13-14 (Art.1-3).
historical_2025: yes (subject to 2024 amendment)
version_relation: original national terms; amended by S-CNMC-2024-MP
evidence_status: confirmed
```

### S-CNMC-2024-MP（confirmed）

```yaml
source_id: S-CNMC-2024-MP
institution: CNMC
title: Resolución de 25 de abril de 2024 por la que se modifican las condiciones relativas al balance y los P.O. para la participación del sistema eléctrico peninsular español en MARI y PICASSO (BOE-A-2024-11535)
document_type: CNMC resolution / BOE consolidated annex
publication_date: 2024-06-06 (BOE); disposition signed 2024-04-25
effective_from: 2024-07-06 for amended conditions (30 days after publication); P.O. provisions tied to SRS or effective MARI/PICASSO connection
effective_to: current unless later amendment identified
url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE PDF pp.1-3 (legal basis); pp.26-33 (Arts.4-15); pp.71-86 (P.O.3.8 storage scope and balance-service tests); pp.195-196 (BSP/BRP data fields); 2024-06-06 BOE pp.66281-66524
relevant_sections: Art.5(1-2) (FCR/aFRR/mFRR/RR crosswalk and P.O.7.1/7.2/7.3/3.3); Art.7(1)(c) storage BSP, Art.7(4) general 1 MW UP/BSP offer floor, Art.7(5) aFRR BSP 100 MW sum of up/down habilitated reserve; Art.8 aggregation; Art.9(2)-(4) storage habilitation, real-time control-centre data, product profiles and P.O.3.8 tests; Arts.10,13,14 (aFRR reserve market, marginal capacity allocation, energy obligation and non-compliance); Art.16 (storage BRP responsibility)
notes: Binding BOE conditions explicitly state FCR=regulación primaria, aFRR=regulación secundaria, mFRR=regulación terciaria; storage holders may be BSPs subject to service-specific habilitation. Art.10 confirms only the secondary/aFRR service has an associated reserve market; mFRR and RR product procedures below are energy-offer/activation rules. Procedures become effective on SRS/MARI/PICASSO connection dates as stated in Resuelve.
historical_2025: yes (MARI connected Dec-2024; PICASSO Jun-2025 per REE)
version_relation: amendment/replacement of 2019 national terms for European platform participation
evidence_status: confirmed
```

### S-CNMC-2020-PO（provisional）

```yaml
source_id: S-CNMC-2020-PO
institution: Secretaría de Estado de Energía / BOE
title: Resolución de 29 de diciembre de 2020 por la que se aprueban P.O. para adaptación a las condiciones relativas al balance (BOE-A-2021-142)
document_type: Secretary of State BOE resolution / P.O.
publication_date: 2021-01-05
effective_from: check each P.O. effective clause; historical bridge to 2022/2024 revisions
effective_to: superseded in part by later P.O. resolutions
url: https://www.ree.es/sites/default/files/2024-02/PO_10_7_BOEA2021_142.pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE PDF pp.976 onward; preamble pp.1-2
relevant_sections: adaptation of P.O. 3.1/3.3/7.2/7.3/14.4 and storage/demand participation; consult each annex in ES-02–ES-05
notes: Historical rule entry; do not use as 2025 current rule when superseded by 2024/2025 amendments.
historical_2025: partially (version timeline required)
version_relation: implements 2019 CNMC conditions, later replaced/amended
evidence_status: provisional
```

### S-CNMC-2021-RR（confirmed）

```yaml
source_id: S-CNMC-2021-RR
institution: CNMC
title: Resolución de 14 de enero de 2021 por la que se modifica P.O.3.3 (RR)
document_type: CNMC resolution / P.O.3.3 amendment
publication_date: 2021-01-16 (BOE PDF)
effective_from: day after BOE publication
effective_to: amended by later P.O.3.3 versions
url: https://www.boe.es/buscar/doc.php?id=BOE-A-2021-701
accessed_at: 2026-08-11
language: Spanish
relevant_pages: preamble and P.O.3.3 §§1,4,9.3, Annex II
relevant_sections: elastic/inelastic RR needs and OS activation/qualification (lines 104-108, 132-158 in BOE HTML)
notes: Retain as historical RR pricing/need safeguard entry; full parameters belong ES-03/ES-05.
historical_2025: yes until 2025 P.O.3.3 amendment
version_relation: amendment of RR P.O.3.3
evidence_status: confirmed
```

### S-CNMC-2022-QH（confirmed）

```yaml
source_id: S-CNMC-2022-QH
institution: CNMC
title: Resolución de 17 de marzo de 2022 por la que se aprueban P.O. adaptados a programación cuarto-horaria (BOE-A-2022-4969)
document_type: CNMC resolution / P.O.1.5, 3.1, 3.2, 3.3, 7.2, 7.3, 9.1, 14.4
publication_date: 2022-03-29 (BOE)
effective_from: date of QH start announced by REE (before four months after BOE publication)
effective_to: amended/replaced by S-CNMC-2024-MP and S-CNMC-2025-QH
url: https://www.boe.es/eli/es/res/2022/03/17/(3)
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§370-416 (P.O.1.5 definitions); §§3237 onward (P.O.7.3 object); §§3224-3235 (IN settlement)
relevant_sections: P.O.1.5 §§3-4 (primary/secondary/tertiary/RR levels); P.O.7.3 §§1-2 (tertiary service); P.O.14.4 (settlement)
notes: 2022 decision declared the Spanish secondary band a national specific product pending SRS/PICASSO adaptation because up/down capacity was not separately procured (preamble §§337-346).
historical_2025: yes as predecessor/version context
version_relation: supersedes 2020/2021 P.O. set at QH start; later amended by 2024/2025 decisions
evidence_status: confirmed
```

### S-CNMC-2024-11535-PO（confirmed）

```yaml
source_id: S-CNMC-2024-11535-PO
institution: CNMC / BOE
title: P.O. 7.2, 7.3, 14.2 and 14.4 amendments for MARI/PICASSO (included in BOE-A-2024-11535)
document_type: P.O. technical procedures
publication_date: 2024-06-06
effective_from: MARI/PICASSO connection dates communicated by REE; Spanish system MARI Dec-2024, PICASSO Jun-2025
effective_to: current subject to 2025 revisions
url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§2211-2241 (P.O.7.2 scope and definitions); §§2635-2718 (Annex I §§1.1-1.2 reserve-capacity offers and §§2.1-2.2 energy offers); §§2719-2820 (Annex II §§1-5 PTR/programme construction); §§2820-3287 (Annex III §§8.1-8.2 telemetry/delivered power and §§9.1-9.3 reserve/REOF/REMOF calculations); PDF pp.99-115 and pp.122-124 (P.O.7.2 aFRR reserve/energy offers, allocation, local/PICASSO/IGCC and Annex I-III); pp.155-160 and pp.164-166 (P.O.7.3 mFRR local/MARI activation, FAT/product table, gates, fallback and Annex I-II); pp.195-196 (P.O.14.2/14.4 data and settlement fields)
relevant_sections: P.O.7.2 §§1,6,8-9; Annex I §§1.1-1.2 and 2.1-2.2; Annex II §§1-5; Annex III §§8.1-8.2 and 9.1-9.3; P.O.7.3 §§1,4,6-10 and Annex I-II §§1-4; P.O.14.2/14.4 settlement and data interfaces
notes: 2024 P.O. 7.3 table gives mFRR standard labels and local product details, including distinct delivery profiles for suppliers also participating in secondary/aFRR and mFRR-only suppliers. For P.O.7.2, Annex I sets the separate Up/Down reserve-capacity and energy offer structures, including the 25-block and one-indivisible-block limits, while Annex II defines PTR construction/following and Annex III defines Pout, storage-consumption telemetry treatment, RESAUP/RESADW, REOF and piecewise REMOF. The formulas are reproduced with caveats in `countries/ES/spain_spot_market_research.md` §§6–7; project-level SOC, duration and qualification items remain open.
historical_2025: yes (MARI/PICASSO operational during 2025)
version_relation: implementation of S-CNMC-2024-MP
evidence_status: confirmed
```

### S-CNMC-2025-QH（confirmed）

```yaml
source_id: S-CNMC-2025-QH
institution: CNMC / BOE
title: Resolución de 6 de marzo de 2025 adapting P.O. to 15-minute trading (BOE-A-2025-5342)
document_type: CNMC resolution / P.O.3.1, 3.2, 3.3, 3.8, 14.3, 14.4
publication_date: 2025-03-17 (BOE pp.35857-35994)
effective_from: MTU15 production date determined by market operator (Resuelve Primero); RR/mFRR/aFRR clauses also refer to OS connection notices
effective_to: current unless later P.O. amendments
url: https://www.boe.es/eli/es/res/2025/03/06/(12)
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§595-614 (RR/mFRR/aFRR); §§674-704 (P.O.3.1 Annex I); §§1341-1361 (P.O.3.1 §13.1 RR stop and §13.2–13.3 mFRR/aFRR); §§1694-1737 (P.O.14.4 definitions/signs/units); §§2154-2286 (P.O.14.4 BRP deviation and single/dual prices); §§1940-2058 and §§2391-2453 (aFRR/RR/tertiary non-delivery); PDF pp.123-127 (P.O.3.3 RR product, H-55′ gate, 40-block limit, 24 horizons and 0.01 €/MWh); Resolution table of contents §§80-93; Resuelve §§321-325
relevant_sections: P.O.3.1 §13 (RR/mFRR/aFRR activation); P.O.3.3 §§6,8,10,13.1 and Annex I §§1-2; P.O.14.4 §§2.3, 3, 7, 8, 12–14, 17.3; local fallback algorithm; mFRR/aFRR offers up to 25 minutes before QH
notes: In 2025 it kept RR use until 96 continuous intraday closures; RR Annex I specifies D-1 12:00 opening, H-55′ e·sios gate, 40 blocks/UP/direction/hour, 24 horizons, FAT30 and 0.01 €/MWh. Exact 2026 replacement after TERRE closure is unresolved.
historical_2025: yes
version_relation: amends 2024 P.O. set
evidence_status: confirmed
```

### S-SP-PO31-2024-STORAGE（confirmed storage programming and settlement interface）

```yaml
source_id: S-SP-PO31-2024-STORAGE
institution: CNMC / BOE
title: Resolución de 6 de marzo de 2024 por la que se modifican los procedimientos de operación eléctricos para la participación de la demanda y el almacenamiento en los servicios de no frecuencia y en la solución de restricciones técnicas e integración de la hibridación de tecnologías en el proceso de programación (BOE-A-2024-6215)
document_type: CNMC resolution / P.O.3.1, P.O.14.1 and P.O.14.8 amendments
publication_date: 2024-03-27 (BOE no.76, pp.35910-36063)
effective_from: 2024-03-28 for the general approved procedures; use of storage-specific programming and non-frequency/restrictions provisions no later than December 2024, on the date separately communicated by REE; superseded/amended by later P.O. versions where applicable
effective_to: versioned by S-CNMC-2025-QH and later P.O. amendments
url: https://www.boe.es/eli/es/res/2024/03/06/(3)
accessed_at: 2026-08-21
language: Spanish
relevant_pages: BOE HTML §§116-129 and §§184-195 (approval/effective dates); P.O.3.1 §§1-4 and §§6-8; P.O.3.1 Annex II §§1, 2.3(b)-(c); P.O.14.1 §§2-3; P.O.14.1 Annex II; P.O.14.8 §§3-6
relevant_sections: storage/non-hydraulic storage differentiated delivery and uptake UPs; one UP per BRP and market participant for each direction; PM/representative management of UPs; UO/UP/UF programme nominations and breakdowns; BRP designation; direct/indirect representation and guarantee/payment responsibility; storage measurement and settlement interfaces
notes: Primary system-operator procedure source for the storage-specific UP/BRP/settlement architecture. The resolution itself says the exact date of use of storage provisions would be communicated by REE no later than December 2024; therefore the 2025 historical slice must retain the relevant P.O. version/date boundary. It does not establish a single project’s completed registration or metering approval.
historical_2025: yes, subject to the version/effective-date boundary and later amendments
version_relation: storage programming/settlement baseline; amended by S-CNMC-2025-QH and later P.O. changes
evidence_status: confirmed for the cited rule text and version boundary; project-level implementation fields remain open
```

### S-CNMC-2024-ISP15（confirmed）

```yaml
source_id: S-CNMC-2024-ISP15
institution: CNMC
title: Resolución de 3 de octubre de 2024 por la que se modifican los procedimientos de operación 14.1 y 14.4 para la adaptación de la liquidación al ISP cuarto-horario (BOE-A-2024-20995)
document_type: CNMC resolution / P.O.14.1 and P.O.14.4
publication_date: 2024-10-14
effective_from: 2024-12-01
effective_to: replaced by S-CNMC-2025-QH at the MTU15 production date specified by OMIE; later modified in 2025
url: https://www.boe.es/eli/es/res/2024/10/03/(1)
accessed_at: 2026-08-18
language: Spanish
relevant_pages: BOE HTML §§95-108 (ISP15 phases); §§145-152 (P.O.14.4 changes); §§226-234 (Resuelve and 2024-12-01 effects); P.O.14.4 §§2.3, 3.2, 12-15
relevant_sections: ISP15 implementation; P.O.14.4 §2.3 CET/CEST time basis; P.O.14.4 §3.2 aFRR BSP storage BRP exception; QH BRP imbalance settlement; single/dual price transition
notes: Governing ISP15 settlement version at the beginning of 2025. CNMC 2025-5342 links its effective date to OMIE MTU15 production, so historical data must retain a version slice rather than applying 2025-5342 from 1 January.
historical_2025: yes
version_relation: predecessor of S-CNMC-2025-QH; P.O.14.4 later amended by BOE-A-2025-13076
evidence_status: confirmed
```

### S-MITECO-2025-ISP（confirmed）

```yaml
source_id: S-MITECO-2025-ISP
institution: Secretaría de Estado de Energía / MITECO
title: Resolución de 28 de marzo de 2025 implementing 15-minute imbalance settlement period (BOE-A-2025-6693)
document_type: Secretary of State resolution / P.O.10.1, 10.2, 10.4, 10.5, 10.6, 10.11
publication_date: 2025-04-02 (BOE pp.45369-45543)
effective_from: 2025-05-01 (first day of month after publication)
effective_to: current unless amended
url: https://www.boe.es/eli/es/res/2025/03/28/(2)
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§60-67 (ISP transition); §§90-110 (approved P.O. and effects); P.O.10.5 storage/direction table §§1352-1358; P.O.10.5 missing/invalid measurement estimates §§1531-1543; QH UP measurement calculation §§1998-2000; P.O.10.x annexes for meters/communications
relevant_sections: 15-minute meter use for RR/tertiary and other QH balancing from 2024-03-01; final ISP implementation; storage boundary measures Activa saliente/entrante; direction-specific missing-measurement estimation and QH UP calculation
notes: Directly relevant to activation verification and imbalance settlement inputs; pricing formulas are deferred to ES-05.
historical_2025: yes (effective May 2025)
version_relation: replaces prior P.O.10.x versions and closes Spanish derogation to 15-minute ISP
evidence_status: confirmed
```

### S-SRAD-2025（confirmed; conditional scope）

```yaml
source_id: S-SRAD-2025
institution: CNMC / BOE
title: Resolución de 6 de noviembre de 2025 modifying P.O.7.5 and P.O.14.4 (SRAD)
document_type: CNMC resolution / local specific balancing product
publication_date: 2025-11-11 (BOE; decision signed 2025-11-06)
effective_from: day after publication; applies to SRAD auctions/service delivery from 2026-01-01
effective_to: amended by S-SRAD-2026
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-22853
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§119-138 (legal history); §§294-304 (effects); P.O.7.5 §§308-332
relevant_sections: local SRAD product, six-month contracting, mFRR-like demand response, auction/activation/measurement
notes: Product is demand-response specific; independent storage eligibility is not assumed and is listed as unresolved. The decision background records the preceding annual SRAD auction/service framework for 2023–2025; this amendment applies the revised cycle to service delivery from 2026-01-01.
historical_2025: preceding SRAD annual framework covered 2023–2025; this 2025 amendment's revised service cycle begins 2026-01-01
version_relation: modifies 2023 SRAD P.O.7.5/14.4
evidence_status: confirmed
```

### S-SRAD-2026（confirmed; conditional scope）

```yaml
source_id: S-SRAD-2026
institution: CNMC / BOE
title: Resolución de 11 de mayo de 2026 modifying P.O.7.5 for SRAD allocation efficiency (BOE-A-2026-10602)
document_type: CNMC resolution / P.O.7.5 amendment
publication_date: 2026-05-15
effective_from: 2026-05-16
effective_to: current at 2026-08-11
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-10602
accessed_at: 2026-08-11
language: Spanish
relevant_pages: BOE HTML §§123-146 (scope and changes); §§180-185 (effects); §§210-228 (publication)
relevant_sections: SRAD assignment tolerance and publication; confidential Annexes I-II
notes: Conditional/local product entry only; confidential annexes mean parameters are not usable without later official disclosure.
historical_2025: no (current-version map only)
version_relation: amendment of S-SRAD-2025
evidence_status: confirmed
```

### S-REE-GUIDE-2024（confirmed for scope; operational guidance）

```yaml
source_id: S-REE-GUIDE-2024
institution: Red Eléctrica de España
title: Guía descriptiva Ser proveedor de servicios de ajuste, versión 5.0 (Diciembre 2024)
document_type: TSO participation guide (non-binding explanatory/operational guide)
publication_date: 2024-12
effective_from: 2024-12 (guide version; verify against each P.O.)
effective_to: superseded when REE posts new version
url: https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/Guia_descriptiva_Ser_proveedor_servicios_de_ajuste.pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: pp.7-10 (FCR/aFRR/mFRR/RR/SRAD and platforms); pp.11-15 (1 MW, telemetry, control centre, tests); p.16 (aFRR BSP 100 MW technical condition)
relevant_sections: §6 services of balance; §7 admission/habilitation; footnotes 5-6
notes: Guide states generation, demand and storage may be BSPs for aFRR/mFRR/RR with at least 1 MW offer capacity (individual/aggregated), prior REE habilitation, telemetry/control centre and tests. Treat all product parameters as ES-02/ES-04 inputs, not final conclusions here.
historical_2025: yes (version issued Dec-2024)
version_relation: operational guide aligned to 2024 CNMC amendments
evidence_status: confirmed
```

### S-REE-FAQ-2026（confirmed for current scope）

```yaml
source_id: S-REE-FAQ-2026
institution: Red Eléctrica de España
title: Preguntas frecuentes – participación en servicios de balance
document_type: TSO web FAQ
publication_date: not stated (web page current at access)
effective_from: current web content; date of each requirement to be checked against P.O.
effective_to: unknown
url: https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance/preguntas-frecuentes
accessed_at: 2026-08-11
language: Spanish
relevant_pages: web §§20-37
relevant_sections: standard products (aFRR FAT 5 min, mFRR FAT 12.5 min, SRAD); storage/demand/generation eligibility >1 MW; habilitation, telemetry, control centre and tests
notes: Current operational summary; use BOE/P.O. for binding parameters.
historical_2025: not necessarily (web page undated)
version_relation: current REE explanatory entry
evidence_status: confirmed
```

### S-REE-PLATFORMS-2026（confirmed for connection dates; current page）

```yaml
source_id: S-REE-PLATFORMS-2026
institution: Red Eléctrica de España
title: Participa en los servicios de balance – European balancing platforms
document_type: TSO web information page
publication_date: not stated
effective_from: current web content
effective_to: unknown
url: https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance
accessed_at: 2026-08-11
language: Spanish
relevant_pages: web §§44-47
relevant_sections: MARI connection Dec-2024; PICASSO connection Jun-2025; IGCC connection Oct-2020
notes: Official REE connection dates used for 2025 historical timeline. RR/TERRE status after Dec-2025 is cross-checked against S-ENTSOE-TERRE-2026.
historical_2025: yes for MARI/PICASSO/IGCC dates
version_relation: current operational summary
evidence_status: confirmed
```

### S-REE-TERTIARY-2024（confirmed for terminology only）

```yaml
source_id: S-REE-TERTIARY-2024
institution: CNMC / BOE (published copy hosted by REE)
title: P.O.7.3 Regulación terciaria, BOE-A-2024-11535
document_type: P.O. technical procedure
publication_date: 2024-06-06
effective_from: MARI connection date for European mFRR clauses
effective_to: current subject to later amendment
url: https://www.ree.es/sites/default/files/2024-11/PO_7_3_BOE-A-2024-11535.pdf
accessed_at: 2026-08-11
language: Spanish
relevant_pages: pp.1-2 (scope); pp.8-9 (mFRR product table)
relevant_sections: mFRR manual activation, FAT, 1 MW offer size and local terminology; full parameter extraction deferred to ES-02/ES-03
notes: Used only to prove official terminology crosswalk and identify later module entry.
historical_2025: yes
version_relation: part of S-CNMC-2024-MP
evidence_status: confirmed
```

### S-REE-DATA-BAL-2026（confirmed as data entry point）

```yaml
source_id: S-REE-DATA-BAL-2026
institution: Red Eléctrica de España / eSIOS
title: Energía gestión desvíos / market data portal
document_type: TSO data portal
publication_date: continuously updated; no single publication date
effective_from: portal current at access
effective_to: unknown; historical downloads exposed by query
url: https://www.ree.es/es/datos/mercados/energia-gestion-desvios
accessed_at: 2026-08-11
language: Spanish
relevant_pages: web data selector; categories shown include balancing energy, RR, secondary/aFRR, tertiary/mFRR, IGCC/SEPE, prices and energy
relevant_sections: “Energía de balance”; “Energía y precios de regulación secundaria”; “Energía y precios de regulación terciaria”; “Energía y precios de reserva de sustitución (RR)”; “Energía intercambiada entre IGCC y SEPE”
notes: Official download/API entry for ES-06. Field names, timezone, resolution, units, publication lag and revisions require dedicated extraction.
historical_2025: likely yes; verify query coverage in ES-06
version_relation: live data portal
evidence_status: provisional
```

### S-eSIOS-PRICES-2026（provisional data entry）

```yaml
source_id: S-eSIOS-PRICES-2026
institution: Red Eléctrica de España / eSIOS
title: Mercados y precios – Precio de los desvíos en tiempo real
document_type: TSO transparency portal
publication_date: continuously updated
effective_from: current
effective_to: unknown
url: https://www.esios.ree.es/es/mercados-y-precios
accessed_at: 2026-08-11
language: Spanish
relevant_pages: web quick access; “Precio de los desvíos en tiempo real” and balancing P.O. documents
relevant_sections: imbalance price display and links to P.O.7.3 / settlement information
notes: Data field/timezone/quarter-hour and revision policy are not confirmed at ES-01; extract in ES-05/ES-06.
historical_2025: likely yes; verify
version_relation: live portal
evidence_status: provisional
```

### S-ENTSOE-TERRE-2026（confirmed for RR version boundary; accessed 2026-09-03）

```yaml
source_id: S-ENTSOE-TERRE-2026
institution: ENTSO-E
title: TERRE – Replacement Reserves platform status
document_type: ENTSO-E platform status page
publication_date: page updated through 2026 (specific page date not stated)
effective_from: 2025-12-30 operational stop; 2026-01-01 former-member status; project closure planned Mar-2026
effective_to: platform decommissioned by Mar-2026
url: https://www.entsoe.eu/network_codes/eb/terre/
accessed_at: 2026-09-03
language: English
relevant_pages: web §§126-153, 208-221
relevant_sections: RRIF basis; TERRE/LIBRA stopped 2025-12-30; REE and REN disconnected after MTU 09:00-10:00 on 2025-12-30; former-member status from 2026-01-01
notes: Creates a hard historical/current boundary: REE and REN participated through MTU 09:00-10:00 CET on 2025-12-30; TERRE/LIBRA operation stopped at 10:00 CET and both were former members from 2026-01-01. It does not identify a Spanish 2026 RR replacement product, qualification, fallback, metering or settlement path; those remain open-critical in SUP-03.
historical_2025: yes
version_relation: closes RR platform period
evidence_status: confirmed
```

### S-ENTSOE-EDI-2024（confirmed as data schema entry）

```yaml
source_id: S-ENTSOE-EDI-2024
institution: ENTSO-E
title: Electronic Data Interchange (EDI) Library – Electricity Balancing Processes
document_type: ENTSO-E implementation guide/schema library
publication_date: balancing process publication 2024
effective_from: schema version-dependent
effective_to: unknown
url: https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/
accessed_at: 2026-08-11
language: English
relevant_pages: web §§321-330
relevant_sections: TERRE, PICASSO, MARI implementation guides; schemas for historical activation, reserve bids, activation, reserve allocation result, resource schedule
notes: Data/API schema crosswalk for ES-06; not a Spanish rule by itself.
historical_2025: yes as platform data schema
version_relation: European data implementation layer
evidence_status: confirmed
```

## 3. 后续模块证据地图（仅入口，不提前提取完整参数）

| 模块 | 第一方入口 | 已可确认的边界 | ES-02/03/04/05/06 待提取 |
|---|---|---|---|
| 平衡容量 | S-CNMC-2024-MP Arts.7(1)(c), 7(4)-(5), 9-10; P.O.7.2 Annex I; P.O.7.3 | aFRR 本地容量市场（上/下独立、D-1/QH、边际容量费）；mFRR/RR为能量报价/激活而非独立容量市场；FCR为primary物理响应 | aFRR履约支付公式、mFRR/RR能量细节、储能SOC/持续时间/产品测试 |
| 平衡能量/激活 | **S-CNMC-2024-11535-PO** P.O.7.2 Annex I/III, P.O.7.3 §§4,7–10 Annex I/II; **S-CNMC-2025-QH** P.O.3.1 §13, P.O.3.3 §13.1/Annex I; REE guide pp.11-13 | aFRR能量：自动、FAT 5 min、15-min delivery、€/MWh；mFRR：手动、FAT 12.5 min，交付参数按aFRR参与状态和程序化/直接类型区分；RR：FAT 30 min、15–60-min delivery、€/MWh；平台故障按适用条件使用本地算法/系统fallback | 激活顺序、门槛、计量、结算、未交付及平台切换详见ES-03；不平衡公式留ES-05 |
| 欧洲平台 | S-REE-PLATFORMS-2026; S-ENTSOE-TERRE-2026; ACER mFRR IF | IGCC Oct-2020, MARI Dec-2024, PICASSO Jun-2025, TERRE 2025-12-30 stop | RR 2026 replacement、跨区容量/TSO-TSO 结算 |
| 独立储能准入 | **S-CNMC-2024-MP Arts.7–9（当前入口；S-CNMC-2019-BAL仅作历史背景）**; S-REE-GUIDE-2024 pp.11-16; S-REE-FAQ-2026 | generation/demand/storage可成为BSP；≥1 MW offer capacity、telemetry/control centre/tests；Art.9(2)(d)允许在规定比例内并入既有合格UP | 储能模式、BRP/BSP关系、SOC/持续供能、聚合限制和产品专门测试 |
| 遥测/计量/履约 | S-MITECO-2025-ISP; S-CNMC-2024-MP Arts.9,14; REE guide pp.14-16 | 15分钟计量用于平衡验证；OS持续监测并可暂停资格 | 数据点、时区、冗余、性能指标、罚则 |
| 不平衡结算 | S-EBGL Arts.17,49-55; S-CNMC-2024-MP Arts.16-24; **S-CNMC-2024-ISP15** P.O.14.1/14.4; **S-CNMC-2025-QH** P.O.14.4 §§2.3,3,7,8,12-14,17.3; **S-CNMC-2025-VOLTAGE-13076**; S-MITECO-2025-ISP | BRP对偏差承担财务责任；ISP15 自2024-12-01生效，计量P.O.10.x自2025-05-01生效 | 单/双价、方向、价格、净额、更正、储能适用；2025-13076仅作版本边界登记 |
| 官方数据 | S-REE-DATA-BAL-2026; S-eSIOS-PRICES-2026; S-ENTSOE-EDI-2024 | REE/eSIOS公开 balancing、RR、aFRR、mFRR、IGCC 和不平衡入口 | API字段、分辨率、时区、单位、延迟、历史覆盖/修订 |

## 4. 规则事实、解释和假设分层

### 规则事实（confirmed/provisional）

- CNMC 2024 条件 Art.5 将西班牙 regulación primaria/secondary/tertiary 分别对应 FCR/aFRR/mFRR，并将 RR 置于 P.O.3.3；P.O.14.4/14.6 为结算入口。
- BOE-A-2024-11535 Art.7(1)(c)明确储能持有人可成为BSP，Art.7(4)规定UP/BSP一般1 MW报价门槛，Art.7(5)规定aFRR BSP上、下方向已 habilitado reserve 合计至少100 MW；Art.8-9绑定聚合、实时控制中心、产品响应曲线和P.O.3.8测试入口。
- Art.10与P.O.7.2明确aFRR本地reserve/capacity market（上/下独立、D-1/QH、边际容量价格和能量支持义务）；P.O.7.3和P.O.3.3审阅范围内未发现独立mFRR/RR容量采购或容量费，只有可用备用/能量报价和激活结算。
- REE 官方资料给出 MARI（mFRR）2024-12、PICASSO（aFRR）2025-06、IGCC（IN）2020-10 接入；ENTSO-E 给出 TERRE/ LIBRA 在 2025-12-30 停止运行。
- REE guide/FAQ作为操作解释表明 generation、demand、storage 可申请 aFRR/mFRR/RR，一般最低offer capacity 1 MW、需REE habilitación、实时telemedida/控制中心和测试；约束性Art.7/9已补入，本文件仍将SOC、持续时间和产品专门资格留至ES-04。
- 2025-04-02 BOE 决议批准 P.O.10.1/10.2/10.4/10.5/10.6/10.11，规定发布后次月首日生效，完成 15 分钟 ISP 的计量接口。

### 研究解释

- 西班牙平衡产品存在“本地服务名称—欧洲标准产品—平台”三层关系；aFRR本地容量市场必须与PICASSO能量市场分开，不能把mFRR/RR预认证能力或reserve requirement写成容量市场收入。
- FCR/primary应表述为物理频率响应，不直接恢复ACE或进入BRP不平衡结算；独立储能FCR资格仍待确认。
- 2025 年是 MARI/PICASSO 同时运行且 RR/TERRE 仍运行至 12 月 30 日的过渡年；24个RR activation horizons与96次连续日内闭市触发条件分开，2026-01-01 后 RR 入口必须重新核实。

### 建模假设

- 本 ES-01 不作建模假设；任何最小功率、响应时间、持续时间、SOC 或罚则值须在后续模块以有效期明确的规则确认后登记。

## 5. ES-04 技术准入证据增补（访问日 2026-08-18）

本节把 ES-04 使用的页码/条款映射补充到既有来源登记；不创建新规则来源。

| source_id | ES-04 技术定位增补 | 证据边界 |
|---|---|---|
| S-CNMC-2024-MP / S-CNMC-2024-11535-PO | BOE PDF pp.26–36 Arts.6–16：BSP/储能持有人、UP/UF、1 MW、aFRR 上下合计 100 MW、控制中心、Art.9(2)(d) 免测、储能双向边界及 BRP；pp.71–95 P.O.3.8：储能适用范围、aFRR AGC、mFRR/RR 斜坡测试、Annex I 控制中心 O/R/I 项及 Annex II 预认证时限；pp.99–124 P.O.7.2：aFRR fallback、ON 义务和 K 系数；pp.155–166 P.O.7.3：mFRR 实时履约；pp.195–221 P.O.14.4：非交付支付义务。 | 绑定技术数值仅限上述条款；P.O.3.8 未给 SOC、持续时长或补能规则；Art.9(2)(d) 比例在公开 OCR 中缺失。BRP 的 aFRR 特殊委托规则另见 S-CNMC-2024-ISP15 P.O.14.4 §3.2。 |
| S-CNMC-2025-QH | BOE-A-2025-5342 P.O.3.8/P.O.3.1 四分之一小时修改及前言 ISP 说明（2025-03-17 发布）。 | 作为版本交叉核对；计量生效日以 S-MITECO-2025-ISP 为准。 |
| S-MITECO-2025-ISP | BOE-A-2025-6693（2025-04-02 发布，2025-05-01 生效）：储能 X/X/X 有功流出、流入、无功；QH 最佳能源；无 QH 表时实时有功遥测积分；部分计量缺失估计 0 kWh。 | 规定计量/ISP接口，不规定 SOC、能量持续时间或资格可用率。 |
| S-SRAD-2025 / S-SRAD-2026 | BOE-A-2025-22853 P.O.7.5（2025-11-11 发布）及 BOE-A-2026-10602（基准日版本检查）：需求 UP/UF、1 MW/0.1 MW 聚合及关联储能不得减少发电/增加充电。 | 独立储能直接成为 SRAD 需求 UF 的路径未找到；2026 版本不得反向覆盖 2025 年初。 |
| S-REE-GUIDE-2024 | v5.0 Dec-2024，PDF p.4 非规范声明；pp.10–16 产品说明；pp.17–20 BSP/CCGD 流程。 | 仅研究解释；FCR droop、产品响应时间等不能替代 BOE/P.O. 约束。 |

## 6. ES-05 不平衡结算证据增补（访问日 2026-08-18）

### S-CNMC-2025-VOLTAGE-13076（版本边界登记）

```yaml
source_id: S-CNMC-2025-VOLTAGE-13076
institution: CNMC / BOE
title: Resolución de 12 de junio de 2025 que modifica P.O.3.1, P.O.3.6, P.O.7.4, P.O.9.1 y P.O.14.4 para el servicio de control de tensión (BOE-A-2025-13076)
document_type: CNMC resolution / operating-procedure amendment
publication_date: 2025-06-26 (BOE no.153, pp.84733-84873; resolution signed 2025-06-12)
effective_from: publication for the amended procedures, subject to Resuelve Segundo deferred dates for specified voltage-control/penalty/zonal-market elements
effective_to: superseded or further amended by later BOE resolutions; exact P.O.14.4 date slice remains ES05-Q01
url: https://www.boe.es/eli/es/res/2025/06/12/(1)
accessed_at: 2026-08-18
language: Spanish
relevant_pages: BOE HTML §§253-257 (P.O.14.4 purpose); §§404-418 (Resuelve and effects); §§3805-3822 (later/previous references)
relevant_sections: P.O.3.1, P.O.3.6, P.O.7.4, P.O.9.1 and P.O.14.4 amendments; version boundary after BOE-A-2025-5342
notes: Used only to register the 2025 version boundary. It does not close the date-specific P.O.14.4 replacement question or change the 2025 historical claim without a day-level effects check.
historical_2025: yes (published June 2025; applicability is procedure/element-specific)
version_relation: later amendment to S-CNMC-2025-QH; later references include BOE-A-2025-22853 and 2026 amendments
evidence_status: confirmed for existence and version relation; date-specific settlement applicability remains open
```

## 7. ES-SP-01 现货制度、主体与平台架构来源（访问日 2026-08-21）

以下来源仅用于 ES-SP-01 的制度、主体、平台和竞价区架构。日前/日内订单参数、套利机制和储能结算细节留在 ES-SP-02—ES-SP-06；`effective_from` 未明确的页面不得被解释为日级规则。

### S-EU-CACM-2015（confirmed EU framework）

```yaml
source_id: S-EU-CACM-2015
institution: European Commission / EUR-Lex
title: Commission Regulation (EU) 2015/1222 of 24 July 2015 establishing a guideline on capacity allocation and congestion management (CACM)
document_type: EU regulation
publication_date: 2015-07-25
effective_from: 2015-08-14
effective_to: null
url: https://eur-lex.europa.eu/eli/reg/2015/1222/oj
accessed_at: 2026-08-21
language: English / official EU text
relevant_pages: HTML consolidated/original legal text
relevant_sections: Arts.2,4-5 (NEMO designation); Arts.6-9 (NEMO/TSO cooperation); Arts.12-15 (bidding zones and capacity); Arts.37-57 (single day-ahead and intraday coupling)
notes: EU legal framework for SDAC/SIDC, NEMOs, bidding zones and cross-zonal capacity. Spanish designation and operating rules require S-SP-BOE-2015-NEMO and S-SP-BOE-2025-RULES.
historical_2025: yes
version_relation: European framework under which OMIE operates as NEMO; amendments/consolidated text must be checked for later changes
evidence_status: confirmed
```

### S-EU-ELEC-2019（confirmed EU framework）

```yaml
source_id: S-EU-ELEC-2019
institution: European Parliament and Council / EUR-Lex
title: Regulation (EU) 2019/943 on the internal market for electricity
document_type: EU regulation
publication_date: 2019-06-14
effective_from: 2019-07-04
effective_to: null
url: https://eur-lex.europa.eu/eli/reg/2019/943/oj
accessed_at: 2026-08-21
language: English / official EU text
relevant_pages: HTML consolidated/original legal text
relevant_sections: Art.8 (trading intervals and market access); Arts.13-16 (dispatch, congestion and bidding zones); Arts.20-22 (resource adequacy/market design context)
notes: Provides the European market-design and trading-interval context cited by later CNMC/BOE decisions. It does not itself establish the Spanish storage registration workflow.
historical_2025: yes
version_relation: European market-design layer above Spanish CNMC/BOE implementation
evidence_status: confirmed
```

### S-SP-BOE-2015-NEMO（confirmed Spanish designation）

```yaml
source_id: S-SP-BOE-2015-NEMO
institution: Ministerio de Industria, Energía y Turismo / BOE
title: Orden IET/2732/2015, de 11 de diciembre, por la que se designa a OMIE como operador designado para el mercado eléctrico
document_type: ministerial order / NEMO designation
publication_date: 2015-12-17 (BOE no.301, pp.118959-118961)
effective_from: not separately stated in the order; designation published 2015-12-17
effective_to: null
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2015-13737
accessed_at: 2026-08-21
language: Spanish
relevant_pages: pp.118959-118961; Disposición Primero; preamble on MIBEL/OMI structure
relevant_sections: NEMO designation; MIBEL structure with OMIE as spot-market manager and OMIP as forward-market manager
notes: Primary Spanish designation source. It identifies OMIE as NEMO under CACM and distinguishes OMIE spot from OMIP forward activity; it does not define current order parameters.
historical_2025: yes
version_relation: legal designation still referenced by S-SP-BOE-2025-RULES
evidence_status: confirmed
```

### S-SP-LAW-24-2013（confirmed statutory allocation of roles）

```yaml
source_id: S-SP-LAW-24-2013
institution: Spanish Parliament / BOE
title: Ley 24/2013, de 26 de diciembre, del Sector Eléctrico
document_type: national law
publication_date: 2013-12-27 (BOE no.310)
effective_from: 2014-01-01 unless an article provides otherwise
effective_to: null
url: https://www.boe.es/buscar/act.php?id=BOE-A-2013-13645
accessed_at: 2026-08-21
language: Spanish
relevant_pages: consolidated HTML Arts.23-24 (offers/production market); Arts.28-30 (market operator and system operator); Arts.21,26 (registration/production obligations)
relevant_sections: Art.28 economic/technical management; Art.29 market-operator functions; Art.30 system-operator functions and coordination
notes: Statutory basis for separating OMIE economic market management from REE technical system operation. Current consolidated text may incorporate amendments; date-specific amendments are not used to infer storage details here.
historical_2025: yes
version_relation: national statutory layer beneath EU market design and above CNMC/OMIE implementation rules
evidence_status: confirmed
```

### S-SP-CNMC-2019-C3（confirmed regulatory methodology layer）

```yaml
source_id: S-SP-CNMC-2019-C3
institution: CNMC
title: Circular 3/2019, por la que se establecen las metodologías que regulan el funcionamiento del mercado mayorista de electricidad y la gestión de la operación del sistema
document_type: CNMC circular / regulatory methodology
publication_date: 2019-12-02 (CNMC publication; BOE publication and text referenced by later decisions)
effective_from: according to the circular and its implementing decisions; article/date slices require procedure-level check
effective_to: null
url: https://www.cnmc.es/novedad/Circular-definitiva-3-2019-mercado-mayorista-electricidad-20191202
accessed_at: 2026-08-21
language: Spanish
relevant_pages: CNMC page and linked Circular 3/2019; Arts.5,12,23 as cited in S-SP-BOE-2026-17285
relevant_sections: methodology for wholesale-market functioning; OM/OS cooperation; intraday coupling and congestion-management framework; approval process
notes: CNMC landing page confirms the circular's subject. For a claim about a concrete market hour, use the applicable BOE/OMIE rule rather than the landing page.
historical_2025: yes
version_relation: national regulatory-methodology layer; later procedure decisions implement/update it
evidence_status: confirmed for framework; article/date detail must be tied to the applicable BOE text
```

### S-SP-BOE-2025-RULES（confirmed market-rule architecture）

```yaml
source_id: S-SP-BOE-2025-RULES
institution: CNMC / BOE
title: Resolución de 28 de febrero de 2025, por la que se publican las reglas de funcionamiento de los mercados diario e intradiario para su adaptación a la negociación cuarto-horaria y a la nueva tipología de ofertas del mercado diario (BOE-A-2025-4908)
document_type: CNMC resolution / OMIE market rules
publication_date: 2025-03-12 (BOE no.61, pp.33382-33561)
effective_from: 2025-03-18 for the first MIBEL implementation of the revised rules; daily MTU15 was separately implemented 2025-10-01; the resolution itself ties application to OMIE production communication
effective_to: later CNMC/OMIE amendments; 2026-08-11 version requires separate check for 96-round implementation
url: https://www.boe.es/eli/es/res/2025/02/28/(2)
accessed_at: 2026-08-21
language: Spanish
relevant_pages: pp.33382-33561; Rules 1-2 (market/operator), 4 (agents), 12 (UO/UP registration and direct/indirect representation aggregation, HTML §§1045-1050), 27-28 (day-ahead object and bids), 32-36 (results, settlement and PDBC/PDBF/PDVP/PDVD), 37-43 (intraday auctions), 44-51 (continuous intraday, order types, portfolio disaggregation, PIBCIC, exceptional situations, settlement and PHF/PHFC), 57 (guarantees), 58/58.4 (OM/OS information exchange), 60-61 (entry/legislation), Annexes 1-3 (products, schedules, order types and price limits)
relevant_sections: market structure; OMIE as economic operator and central counterparty; agents including storage holders; Rule 12 registration coordination and biunívoca UO-UP association; indirect representation may aggregate multiple represented programs while direct representation is limited to one represented program; day-ahead bid types and validation; IDA three-session schedule and products; continuous 15-minute contracts, rounds, order conditions, shared-order-book/cross-zonal-capacity interface; PIBCI/PIBCA/PIBCIC/PIBCAC and PHF/PHFC programme hand-off; day-ahead and intraday settlement; guarantees and price-limit method
notes: Primary architecture and market-rule source. It contains the detailed bid, settlement, guarantee and programme provisions used in ES-SP-02 and ES-SP-03; storage-holder agent status is confirmed by Rule 4.1, while registration, UO/UP mapping and storage-specific settlement details remain ES-SP-04.
historical_2025: yes; revised-rule operation began in 2025 with separate intraday and daily MTU15 boundaries
version_relation: supersedes the 2024 IDA adaptation rules at the applicable production date; later 2026 amendments are not backfilled into 2025
evidence_status: confirmed
```

### S-SP-BOE-2024-IDAS（confirmed IDA layer）

```yaml
source_id: S-SP-BOE-2024-IDAS
institution: CNMC / BOE
title: Resolución de 23 de mayo de 2024, por la que se aprueban las reglas de funcionamiento de los mercados diario e intradiario para su adaptación a las subastas europeas intradiarias (BOE-A-2024-11958)
document_type: CNMC resolution / market-rule amendment
publication_date: 2024-06-12 (BOE no.142, pp.68858-69025)
effective_from: 2024-06-13 for European IDA operation according to OMIE's official European-market page; later replaced by S-SP-BOE-2025-RULES at the applicable production date
effective_to: 2025-03-17 for the historical slice; replaced by S-SP-BOE-2025-RULES at the 2025-03-18 production implementation
url: https://www.boe.es/eli/es/res/2024/05/23/(12)
accessed_at: 2026-08-21
language: Spanish
relevant_pages: pp.68858-69025; Rules 1-2, 4, 37-44, 51, 58 and Annex 1 (intraday hours) / Annex 2 (continuous-order types)
relevant_sections: three European intraday auctions (IDA) plus continuous intraday market; hourly intraday auction horizons and hourly continuous contracts before the 2025-03-18 quarter-hour go-live; OMIE/REE coordination; market-agent access and programme hand-off
notes: Used for the 2025-01-01—2025-03-17 historical intraday slice and the 2024-to-2025 IDA architecture boundary. Exact 2025 quarter-hour schedules and product parameters are taken from S-SP-BOE-2025-RULES and S-SP-OMIE-QH-ID-2025.
historical_2025: yes (historical background; 2025 revised rules apply from March 18)
version_relation: predecessor to S-SP-BOE-2025-RULES
evidence_status: confirmed
```

### S-SP-OMIE-NEMO-2026（confirmed operational architecture page）

```yaml
source_id: S-SP-OMIE-NEMO-2026
institution: OMIE
title: Mercado europeo / European market integration page
document_type: NEMO operational information page
publication_date: continuously maintained; page footer current at access
effective_from: page states day-ahead European coupling since 2014, intraday European coupling since 2018, IDAs since 2024-06-13
effective_to: current page; operational statements can change
url: https://www.omie.es/es/mercado-europeo
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web §§50-77
relevant_sections: OMIE NEMO role; SDAC/EUPHEMIA; SIDC shared order book and cross-zonal capacity module; IDAs and continuous intraday coordination
notes: Operational explanation, not a substitute for CNMC/BOE rule text. Used to explain the platform relationship and not to establish a storage qualification.
historical_2025: yes for the stated 2014/2018/2024 milestones; current platform counts are not used for 2025 parameters
version_relation: operational view of S-EU-CACM-2015 and S-SP-BOE-2025-RULES
evidence_status: confirmed for architecture; normative status limited
```

### S-SP-OMIE-AGENT-2026（confirmed access workflow, normative status limited）

```yaml
source_id: S-SP-OMIE-AGENT-2026
institution: OMIE
title: Cómo hacerse agente / becoming a market agent
document_type: OMIE participant-access page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.omie.es/es/como-hacerse-agente
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web §§50-67, §§80-83
relevant_sections: participant classes; requirement to become a system subject through REE; OMIE electronic registration and accession; separate DA/IDA/continuous platforms
notes: Operational access guidance. Legal requirements are controlled by S-SP-BOE-2025-RULES and applicable registration rules.
historical_2025: current guidance; historical workflow not assumed beyond the rules source
version_relation: implementation entry for the OMIE market-agent rules
evidence_status: confirmed for operational entry; normative status limited
```

### S-SP-OMIE-MARKET-2026（confirmed public market-operations page; normative status limited）

```yaml
source_id: S-SP-OMIE-MARKET-2026
institution: OMIE
title: Mercado de electricidad / Electricity market
document_type: NEMO public market-operations page
publication_date: continuously maintained; current page at access
effective_from: current page at access; operational descriptions may change by instruction or rule version
effective_to: unknown
url: https://www.omie.es/es/mercado-de-electricidad
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web §§108-147 and price-limit section at page start
relevant_sections: three European intraday auctions; continuous SIDC; adjustment until approximately one hour before delivery; 15-minute/market structure context; MIBEL intraday price limits and notification thresholds
notes: Operational explanation and current public values only. Normative claims and 2025 historical values must use the applicable BOE/CNMC rules and versioned OMIE instructions; current price-limit values are not backfilled into every 2025 delivery day.
historical_2025: current page; only stated 2025 milestones are cross-checked against dated official notices
version_relation: operational view of S-SP-BOE-2025-RULES and S-EU-CACM-2015
evidence_status: confirmed for current operational page; normative status limited
```

### S-SP-REE-ROLE-2026（confirmed TSO/system-operator entry）

```yaml
source_id: S-SP-REE-ROLE-2026
institution: Red Eléctrica de España (REE)
title: Normativa nacional y europea / national and European regulatory framework
document_type: TSO regulatory-framework page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.ree.es/es/conocenos/marco-regulatorio/normativa-nacional-y-europea
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web overview
relevant_sections: Law 24/2013; REE as sole TSO, system operator and transmission-grid manager; access/connection regulatory stack
notes: Used as a navigational/role source; statutory role claims are tied to S-SP-LAW-24-2013.
historical_2025: current page; role framework applicable in 2025
version_relation: REE operational layer under Law 24/2013
evidence_status: confirmed for institutional role; normative status limited
```

### S-SP-REE-MIBEL-2026（confirmed MIBEL scope page）

```yaml
source_id: S-SP-REE-MIBEL-2026
institution: Red Eléctrica de España (REE)
title: Informes MIBEL / MIBEL reports
document_type: TSO market-scope page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.ree.es/es/actividades/operacion-del-sistema-electrico/informes-mibel
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web overview
relevant_sections: MIBEL as joint Spain-Portugal initiative; consumers and producers/commercializers operate in an Iberian competitive market
notes: Scope/market-context source only; it does not define daily or intraday order rules.
historical_2025: yes for MIBEL institutional scope; current reports are not used as historical price evidence
version_relation: context for S-SP-BOE-2015-NEMO and S-SP-BOE-2025-RULES
evidence_status: confirmed for scope
```

### S-SP-REE-INTERCONNECTIONS-2026（confirmed physical and commercial boundary entry）

```yaml
source_id: S-SP-REE-INTERCONNECTIONS-2026
institution: Red Eléctrica de España (REE)
title: Interconexiones / international interconnections
document_type: TSO infrastructure and market-context page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.ree.es/es/transicion-ecologica/interconexiones
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web overview and interconnection sections
relevant_sections: Spanish mainland connections with France, Portugal, Andorra and Morocco; commercial capacity and market-price-difference context
notes: Confirms connected systems and separates physical interconnection from commercial exchange. It does not prove that non-EU borders participate in SDAC/SIDC.
historical_2025: physical connections yes; current capacity values not used for 2025
version_relation: infrastructure context for boundary table; normal market-coupling status comes from CACM/OMIE/BOE sources
evidence_status: confirmed for connections; border-specific platform classification partly open
```

### S-SP-ENTSOE-MCSC-2026（confirmed European governance entry）

```yaml
source_id: S-SP-ENTSOE-MCSC-2026
institution: ENTSO-E / Market Coupling Steering Committee
title: Market Coupling Steering Committee (MCSC)
document_type: ENTSO-E governance and project page
publication_date: continuously maintained; current work plan page at access
effective_from: current governance page
effective_to: unknown
url: https://www.entsoe.eu/network_codes/cacm/implementation/mcsc/
accessed_at: 2026-08-21
language: English
relevant_pages: web overview
relevant_sections: SDAC purpose; SIDC purpose; NEMO/TSO governance agreements (DAOA, ANDOA, TCMC, IDOA, ANIDOA)
notes: Platform-governance source. It does not decide Spanish participant eligibility or settlement.
historical_2025: yes for the SDAC/SIDC governance layer; current work plan changes are not backfilled
version_relation: European cooperation layer under S-EU-CACM-2015
evidence_status: confirmed for governance architecture
```

### S-SP-JAO-HAR-2024（confirmed long-term-rights classification for EU borders）

```yaml
source_id: S-SP-JAO-HAR-2024
institution: Joint Allocation Office (JAO)
title: List of bidding zone borders for HAR applicable for EU internal borders
document_type: JAO harmonised allocation rules / border list
publication_date: 2024-09 (file date)
effective_from: 2024 harmonised allocation rule list; applicable to 2025 EU internal-border products subject to yearly product documents
effective_to: later HAR updates may supersede
url: https://www.jao.eu/sites/default/files/2024-09/List%20of%20Bidding%20Zone%20borders_2024_HAR_applicable%20for%20EU%20internal%20borders%20with%20cap.pdf
accessed_at: 2026-08-21
language: English
relevant_pages: p.4 and border-list rows for Spain–Portugal; Spain–France rows where applicable
relevant_sections: responsible TSOs; long-term transmission-right type; curtailment-compensation cap field
notes: The JAO border list identifies ES–PT as FTR Options and FR–ES as PTRs. Long-term rights are separate from normal implicit SDAC/SIDC allocation and are not energy-market orders; the ES–FR financial/physical use options are further described in the REE 2025 annual-capacity notice.
historical_2025: yes, subject to the 2025 product/border list
version_relation: long-term-capacity layer separate from S-EU-CACM-2015 short-term coupling
evidence_status: confirmed for listed border classification; exact physical subset crosswalk requires later boundary/data work
```

### S-SP-OMIE-QH-ID-2025（confirmed 2025 intraday version boundary）

```yaml
source_id: S-SP-OMIE-QH-ID-2025
institution: OMIE
title: OMIE implementa con éxito la nueva tipología de ofertas en el mercado diario y la negociación cuarto-horaria en el mercado intradiario
document_type: OMIE implementation notice
publication_date: 2025-03-18
effective_from: 2025-03-18 (intraday quarter-hour operation in MIBEL; delivery from 2025-03-19)
effective_to: later intraday-market changes
url: https://www.omie.es/sites/default/files/2025-03/250318_sco_15mtu_vf-es_0.pdf
accessed_at: 2026-08-21
language: Spanish
relevant_pages: pp.1-2
relevant_sections: implementation of quarter-hour intraday auctions and continuous intraday; relation to SDAC/SIDC
notes: Used only to close the 2025 operational boundary. Product/auction timing details remain ES-SP-03.
historical_2025: yes
version_relation: implementation notice for S-SP-BOE-2025-RULES
evidence_status: confirmed
```

### S-SP-OMIE-MTU15-DA-2025（confirmed 2025 day-ahead version boundary）

```yaml
source_id: S-SP-OMIE-MTU15-DA-2025
institution: OMIE
title: OMIE implementa con éxito la negociación en intervalos de 15 minutos en el mercado diario
document_type: OMIE implementation notice
publication_date: 2025-10-01
effective_from: 2025-10-01 delivery (first auction 2025-09-30) for SDAC/MIBEL daily MTU15
effective_to: later SDAC/OMIE changes
url: https://www.omie.es/sites/default/files/2025-10/2501001_go_live_mtu15_md_es_vf.pdf
accessed_at: 2026-08-21
language: Spanish
relevant_pages: pp.1-2
relevant_sections: SDAC coordinated Big Bang; 96 quarter-hour prices for delivery day 2025-10-01
notes: Used only for the 2025 daily-market architecture/version timeline. It does not describe storage bidding or profitability.
historical_2025: yes
version_relation: completes the 2025 transition started by S-SP-OMIE-QH-ID-2025
evidence_status: confirmed
```

### S-SP-BOE-2025-21198（confirmed temporary PTR version; 2025 historical slice）

```yaml
source_id: S-SP-BOE-2025-21198
institution: CNMC / BOE
title: Resolución de 20 de octubre de 2025 por la que se modifican temporalmente varios procedimientos de operación eléctricos para la introducción de medidas urgentes para la estabilización de la tensión en el sistema eléctrico peninsular español (BOE-A-2025-21198)
document_type: CNMC resolution / temporary P.O. amendment
publication_date: 2025-10-21 (BOE no.253, pp.137795-137808; disposition signed 2025-10-20)
effective_from: 2025-10-22 (day after publication; BOE analysis states effects from 2025-10-22). The first extension source describes operational monitoring from 2025-10-23.
effective_to: 2025-11-20 initial 30-day period, subject to 15-day extensions up to a total maximum of three months; subsequent extensions are recorded by S-SP-BOE-2025-23407 and S-SP-BOE-2025-27212.
url: https://www.boe.es/eli/es/res/2025/10/20/(1)
accessed_at: 2026-09-04
language: Spanish
relevant_pages: BOE HTML §§47-62 (publication metadata); §§250-269 (Resuelve/application); §§318-344 (P.O.7.2 Annex II §5 PTR tracking and temporary OS requirement); PDF pp.137795-137808
relevant_sections: temporary changes to P.O.3.1, P.O.3.2 and P.O.7.2; P.O.7.2 Annex II §5 makes PTR tracking mandatory when valid aFRR offers exist, optional when no offers exist unless the OS temporarily requires tracking for security; initial 30-day term and extension limit
notes: This source is the legal start of the temporary PTR-tracking/ramp measure. It does not create a storage-specific SOC, duration or recharge rule, and it is not a permanent 2026 rule. Preserve the formal 2025-10-22 effect date separately from the 2025-10-23 operational-monitoring date cited in the first extension.
historical_2025: yes, 2025-10-22 through the initial term and only as extended by the dated follow-on agreements
version_relation: temporary amendment of P.O.7.2 Annex II under S-CNMC-2024-11535-PO; later extended by S-SP-BOE-2025-23407, S-SP-BOE-2025-24704, S-SP-BOE-2025-26207 and S-SP-BOE-2025-27212; superseded for the modified PTR paragraph by S-SP-BOE-2026-1377 from 2026-01-20
evidence_status: confirmed
```

### S-SP-BOE-2025-23407（confirmed first PTR extension; 2025 historical slice）

```yaml
source_id: S-SP-BOE-2025-23407
institution: CNMC / BOE
title: Acuerdo de 18 de noviembre de 2025 por el que se prorroga la modificación temporal de varios procedimientos de operación eléctricos para la introducción de medidas urgentes para la estabilización de la tensión en el sistema eléctrico peninsular español (BOE-A-2025-23407)
document_type: CNMC agreement / 15-day extension of temporary P.O. amendment
publication_date: 2025-11-19 (BOE no.278, pp.151718-151720; agreement dated 2025-11-18)
effective_from: after expiry of the initial 30-day term on 2025-11-20; first 15-day extension therefore covers 2025-11-21—2025-12-05 under the agreement's stated effect clause
effective_to: 2025-12-05 for this first extension, subject to later extensions within the original three-month maximum
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-23407
accessed_at: 2026-09-04
language: Spanish
relevant_pages: PDF pp.1-3; PDF p.1 Antecedentes §§1-2 (initial term and 2025-10-23 monitoring reference); PDF pp.2-3 Fundamentos II.2 and Acuerda §§1-2; BOE HTML/PDF lines stating the extension runs from expiry of the initial term
relevant_sections: 15-day extension of the P.O.3.1, P.O.3.2 and P.O.7.2 temporary changes; the agreement records the initial term as expiring 2025-11-20 and extends it from that expiry
notes: The agreement extends the same temporary PTR rule; it does not alter the P.O.7.2 formula or turn PTR tracking into a permanent rule. Its reference to monitoring from 2025-10-23 is an operational chronology and should not replace the formal effect date of 2025-10-22 in S-SP-BOE-2025-21198.
historical_2025: yes, first extension only
version_relation: extension of S-SP-BOE-2025-21198; later extensions are referenced in S-SP-BOE-2025-27212
evidence_status: confirmed
```

### S-SP-BOE-2025-27212（confirmed fourth PTR extension; 2025-12-31 publication）

```yaml
source_id: S-SP-BOE-2025-27212
institution: CNMC / BOE
title: Acuerdo de 29 de diciembre de 2025 por el que se prorroga la modificación temporal de procedimientos de operación eléctricos para la introducción de medidas urgentes para la estabilización de la tensión en el sistema eléctrico peninsular español (BOE-A-2025-27212)
document_type: CNMC agreement / fourth 15-day extension of temporary P.O. amendment
publication_date: 2025-12-31 (BOE no.315, p.181326 onward; agreement dated 2025-12-29)
effective_from: 2026-01-05, after the third 15-day extension expired on 2026-01-04, as stated in the official chronology and the agreement's "from expiry" clause
effective_to: 2026-01-19 (15 days from the expiry of the 2025-12-18 third extension), within the original maximum three-month temporary period
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-27212
accessed_at: 2026-09-04
language: Spanish
relevant_pages: BOE HTML §§68-73 (2025-10-23 monitoring reference); §§78-104 (successive extensions and 2026-01-04 expiry of the third extension); §§113-131 (fourth extension and publication metadata); PDF BOE no.315, p.181326 onward
relevant_sections: records the successive 15-day extensions dated 2025-11-18, 2025-12-01 and 2025-12-18; extends the temporary P.O.3.1/P.O.3.2/P.O.7.2 amendment from the expiry of the third extension; reference to the three-month maximum
notes: The literal effective-from field is expressed as 2026-01-05 based on the agreement's "from expiry" clause and the stated 2026-01-04 expiry; this is a date calculation from the official chronology, not a separate new rule text. The temporary PTR version ends at the 2026-01-19 boundary; S-SP-BOE-2026-1377 applies on 2026-01-20.
historical_2025: yes for the portion through 2025-12-31; the extension continues into 2026 and must not be backfilled into the 2025 historical rule baseline without its date label
version_relation: fourth extension of S-SP-BOE-2025-21198; followed by S-SP-BOE-2026-1377 for the modified P.O.7.2 PTR paragraph from 2026-01-20
evidence_status: confirmed
```

### S-SP-BOE-2026-1377（confirmed 2026 PTR replacement/extension boundary; not 2025）

```yaml
source_id: S-SP-BOE-2026-1377
institution: CNMC / BOE
title: Resolución de 19 de enero de 2026 por la que se modifican los procedimientos de operación eléctricos 3.1, 3.2 y 7.2 para facilitar la estabilización de la tensión en el sistema eléctrico peninsular español (BOE-A-2026-1377)
document_type: CNMC resolution / P.O. amendment
publication_date: 2026-01-20 (BOE no.18; disposition signed 2026-01-19)
effective_from: 2026-01-20 (date of BOE publication; the resolution expressly states that the modifications take effect on publication)
effective_to: unknown; review required within one year of publication, and later amendments may supersede it
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-1377&lang=es
accessed_at: 2026-09-04
language: Spanish
relevant_pages: BOE HTML §§210-228 (approval, effect, repeal of prior modified text); §§394-404 (P.O.7.2 Annex II §5 new PTR rule); analysis §§408-416 (publication/effective date and references)
relevant_sections: P.O.7.2 Annex II §5 requires PTR tracking in every programming period, requires 4-second tracking/consignment where valid aFRR offers exist, and states that BRP deviation settlement uses quarter-hour energy against the integral of the ramped PTR; P.O.3.1/P.O.3.2 changes for the same tension-stability package
notes: This is the 2026-01-20 replacement boundary for the paragraph temporarily amended in October 2025. It may be described as extending PTR tracking to all periods only from 2026-01-20; it must not be used to rewrite 2025. It does not close independent-storage qualification, SOC, duration, recharge or restoration questions.
historical_2025: no; post-historical source, with the 2025 temporary chain retained separately
version_relation: follows the 2025-10—2026-01-19 temporary PTR chain; modifies the P.O.7.2 paragraph originally in S-CNMC-2024-11535-PO
evidence_status: confirmed
```

### S-SP-BOE-2026-17285（confirmed publication; application date announced after baseline）

```yaml
source_id: S-SP-BOE-2026-17285
institution: CNMC / BOE
title: Resolución de 30 de julio de 2026, por la que se modifican procedimientos de operación para la implementación de 96 rondas de negociación en el mercado intradiario continuo (BOE-A-2026-17285)
document_type: CNMC resolution / system-operation amendment
publication_date: 2026-08-07 (BOE no.192, pp.111113-111207)
effective_from: date agreed between OMIE and the Iberian system operators and publicly communicated by OMIE; exact application date was not confirmed at the 2026-08-11 baseline
effective_to: unknown
url: https://www.boe.es/eli/es/res/2026/07/30/(4)
accessed_at: 2026-09-03
language: Spanish
relevant_pages: pp.111113-111207; BOE HTML §§301-328 (approval, application, P.O.3.3 without effect); P.O.3.1 §§339-468, 830-866, 928-954; P.O.7.2 §§773-808; P.O.14.4 §§2341-2366
relevant_sections: 96 continuous intraday rounds; TERRE procedure repeal after 2025-12-30; application tied to OMIE/RE/REN public date; programming and information-exchange updates
notes: Published before the baseline but not assumed operational on 2026-08-11. The decision makes P.O.3.3 (RR activation) without effect because Spanish OS participation in TERRE ended 2025-12-30, while modifying P.O.3.1/P.O.7.2/P.O.9.1/P.O.14.4 for the new 96-round environment. It is not backfilled into 2025. OMIE later announced a planned 2026-09-22 maintenance/start date in S-SP-OMIE-INST4-2026; actual completed go-live was not yet verifiable on 2026-09-03.
historical_2025: no (future/current-version amendment; 2025 only appears as background boundary)
version_relation: post-2025 amendment to S-SP-BOE-2025-RULES and system-operation procedures
evidence_status: confirmed publication and scope; application notice confirmed, completed operation still future/unverified at access
```

### S-SP-BOE-2026-17570（confirmed market-rule amendment; application notice identified）

```yaml
source_id: S-SP-BOE-2026-17570
institution: CNMC / BOE
title: Resolución de 30 de julio de 2026, de la Comisión Nacional de los Mercados y la Competencia, por la que se modifican las reglas de funcionamiento de los mercados diario e intradiario de electricidad para la implementación de 96 rondas de negociación en el mercado intradiario continuo (BOE-A-2026-17570)
document_type: CNMC resolution / day-ahead and intraday market rules amendment
publication_date: 2026-08-11 (BOE no.196, pp.113077-113268)
effective_from: date agreed between OMIE and the Iberian system operators and publicly communicated by OMIE; exact application date was not confirmed at the 2026-08-11 baseline
effective_to: unknown
url: https://www.boe.es/eli/es/res/2026/07/30/(8)
accessed_at: 2026-09-03
language: Spanish
relevant_pages: pp.113077-113268; BOE HTML §§689-720 (96-round rationale and 60-minute gate); §§813-824 (application-date notice); Annex 2 §§5106-5178 (IDA/continuous schedule and 96/92/100 contracts); §§5335-5390 (continuous order types)
relevant_sections: market-rule layer corresponding to the 96-round continuous intraday implementation; distinguish from S-SP-BOE-2026-17285 system-operation amendments
notes: Published on the 2026-08-11 baseline date. It is not backfilled into 2025 and is not treated as operational on the baseline date. Used together with S-SP-BOE-2026-17285, not as a substitute for the system-operation source. The later OMIE Instruction 4/2026 notice sets a planned 2026-09-22/23 operational transition; actual completion remained future at 2026-09-03.
historical_2025: no
version_relation: post-2025 amendment to S-SP-BOE-2025-RULES; paired with the system-operation amendment S-SP-BOE-2026-17285
evidence_status: confirmed publication and scope; application notice confirmed, completed operation still future/unverified at access
```

### S-SP-REE-ANNUAL-CAP-2025（confirmed EU-border long-term allocation context）

```yaml
source_id: S-SP-REE-ANNUAL-CAP-2025
institution: Red Eléctrica de España (REE)
title: Las interconexiones con Francia y Portugal ingresan 71,4 millones de euros al sistema eléctrico español / annual capacity auctions for 2025
document_type: TSO press release and capacity-allocation notice
publication_date: 2024-12-12
effective_from: 2025 annual capacity-right products
effective_to: 2025-12-31 for the reported annual product
url: https://www.ree.es/es/sala-de-prensa/actualidad/nota-de-prensa/2024/12/las-interconexiones-con-francia-y-portugal-ingresan-71-4-millones-euros-sistema-electrico-espanol
accessed_at: 2026-08-21
language: Spanish
relevant_pages: web overview; linked PDF if used
relevant_sections: JAO allocation of annual usage rights; financial use and optional physical use at the France border; Spain–Portugal/France operator coordination
notes: Used to distinguish long-term JAO rights from normal coupled spot allocation. It does not replace the JAO border list or define daily/intraday orders.
historical_2025: yes
version_relation: 2025 product notice under S-SP-JAO-HAR-2024
evidence_status: confirmed
```

### ES-SP-01 source-status summary

| Source ID | Architecture use | 2025 applicability | Status |
|---|---|---|---|
| S-EU-CACM-2015 / S-EU-ELEC-2019 | EU NEMO, SDAC/SIDC and market-design layer | yes | confirmed |
| S-SP-BOE-2015-NEMO / S-SP-LAW-24-2013 / S-SP-CNMC-2019-C3 | Spanish institutional and legal role allocation | yes | confirmed |
| S-SP-BOE-2025-RULES / S-SP-BOE-2024-IDAS | OMIE rules, agents, market-platform components | yes, with 2025 version slices | confirmed |
| S-SP-OMIE-NEMO-2026 / S-SP-OMIE-AGENT-2026 | Operational platform and access explanations | current page; milestones cross-checked | confirmed, normative status limited |
| S-SP-REE-ROLE-2026 / S-SP-REE-MIBEL-2026 / S-SP-REE-INTERCONNECTIONS-2026 | REE role, MIBEL scope and physical-border context | role/scope yes; current capacity not historical | confirmed, partly non-normative |
| S-SP-ENTSOE-MCSC-2026 / S-SP-JAO-HAR-2024 | European governance and long-term-right boundary | yes where versioned | confirmed |
| S-SP-OMIE-QH-ID-2025 / S-SP-OMIE-MTU15-DA-2025 | 2025 intraday/daily MTU version timeline | yes | confirmed |
| S-SP-BOE-2026-17285 | 96-round/TERRE future boundary | not applicable to 2025; published but application date open at 2026-08-11 | confirmed publication; application unresolved |
| S-SP-BOE-2026-17570 | 96-round market-rule amendment boundary | not applicable to 2025; published 2026-08-11 but application date open at baseline | confirmed publication; application unresolved |

## 8. ES-SP-02 西班牙日前市场规则来源（访问日 2026-08-21）

以下来源用于日前市场的历史版本、申报、出清、价格形成、计划接口、结算、保证金和违约后果。日内市场的详细交易参数不在 ES-SP-02 中提取。

### S-SP-BOE-2024-RULES（confirmed for the 2025-01-01—2025-03-17 historical slice）

```yaml
source_id: S-SP-BOE-2024-RULES
institution: CNMC / BOE
title: Resolución de 23 de mayo de 2024, por la que se aprueban las reglas de funcionamiento de los mercados diario e intradiario de electricidad para su adaptación a las subastas europeas intradiarias (BOE-A-2024-11958)
document_type: CNMC resolution / OMIE market rules
publication_date: 2024-06-12 (BOE no.142, pp.68858-69025)
effective_from: 2024-06-13 with the production of the European intraday auctions; the 2025-03-18 revised rules superseded it at the applicable production date
effective_to: 2025-03-17 for the historical daily-market slice used here
url: https://www.boe.es/eli/es/res/2024/05/23/(12)
accessed_at: 2026-08-21
language: Spanish
relevant_pages: BOE HTML §§44-57 (publication and validity); §§749-760 (Rules 1-2); §§1342-1360 (daily-market object and offers); §§1853-1977 (daily-market settlement); §3992 onward (Rule 59 sequence and information exchange)
relevant_sections: hourly day-ahead market periods; OMIE economic management and central-counterparty role; daily offers; marginal-price settlement and congestion income; market sequence and information exchange
notes: Primary historical rule text. It was marked Vigencia agotada after the 2025 rule revision. It is used only for the 2025-01-01—2025-03-17 version slice, not for later periods.
historical_2025: yes (first slice only)
version_relation: predecessor to S-SP-BOE-2025-RULES; the 2024 resolution expressly states that the 2023 rules cease to apply when IDA production starts
evidence_status: confirmed for historical version boundary and the cited daily-market provisions
```

### S-EU-ACER-HMMCP-2023（confirmed for 2025 SDAC reference price limits）

```yaml
source_id: S-EU-ACER-HMMCP-2023
institution: ACER
title: ACER Decision No 01/2023 on the NEMO proposal for the harmonised maximum and minimum clearing price methodology for the single day-ahead coupling
document_type: ACER decision / SDAC methodology
publication_date: 2023-01-10
effective_from: 2023-01-11 implementation of the amended SDAC price-limit methodology
effective_to: amended by S-EU-ACER-HMMCP-2026 for the current baseline; 2025 historical operation remains within this version
url: https://www.acer.europa.eu/Individual%20Decisions/ACER%20Decision%2001-2023%20on%20HMMCP%20SDAC.pdf
accessed_at: 2026-08-21
language: English / official ACER text
relevant_pages: pp.1-2 (decision and CACM basis); pp.13-16 (trigger conditions, 70% threshold, rolling 30-day window, 500 EUR/MWh increase and 28-day transition); pp.20-22 (approval, OMIE addressee and annex)
relevant_sections: harmonised SDAC maximum/minimum clearing price methodology and automatic adjustment mechanism
notes: The decision and ACER's accompanying official overview retain reference limits of +4000/-500 EUR/MWh. The Spanish rule text intentionally points agents to the current public OMIE values rather than hard-coding the numeric limit in the BOE annex.
historical_2025: yes
version_relation: implemented through CACM Article 41 and referenced by S-SP-BOE-2025-RULES Annex 3
evidence_status: confirmed
```

### S-EU-ACER-HMMCP-2026（confirmed for the 2026-08-11 rule baseline）

```yaml
source_id: S-EU-ACER-HMMCP-2026
institution: ACER
title: ACER Decision No 02/2026 on the NEMO proposal for the harmonised maximum and minimum clearing price methodology for the single day-ahead coupling
document_type: ACER decision / SDAC methodology
publication_date: 2026-02-04
effective_from: immediate implementation after ACER approval under Article 5 of the annexed methodology
effective_to: current at the 2026-08-11 rule baseline
url: https://www.acer.europa.eu/sites/default/files/documents/Individual%20Decisions/ACER-Decision-02-2026-harmonised-clearing-prices-day-ahead.pdf
accessed_at: 2026-08-21
language: English / official ACER text
relevant_pages: pp.1-3 (decision history and CACM basis); Annex I pp.4-6, Arts.1-5 (scope, +4000/-500 reference limits, automatic adjustment and publication)
relevant_sections: SDAC-wide harmonised clearing limits and adjustment procedure; OMIE is listed as an addressee
notes: Used for the current baseline only. It must not be backfilled into 2025; the historical 2025 limit/methodology is registered under S-EU-ACER-HMMCP-2023.
historical_2025: no (current-baseline source)
version_relation: amendment of S-EU-ACER-HMMCP-2023
evidence_status: confirmed for current baseline; historical applicability excluded
```

### ES-SP-07 数据目录与接口来源（访问日 2026-08-21）

### S-SP-OMIE-FILES-2026（confirmed catalogue; coverage/revision open）

```yaml
source_id: S-SP-OMIE-FILES-2026
institution: OMIE
title: Acceso a ficheros / Public file access list
document_type: NEMO public file catalogue
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access
effective_to: unknown
url: https://www.omie.es/index.php/es/file-access-list
accessed_at: 2026-08-21
relevant_pages: web §§35-127 (daily/IDA/continuous file categories); §129 (IDA note); §130 (six-year rolling repository and assistance portal)
relevant_sections: prices, programmes, curves, offers, capacities, trades, outages and recent/monthly public files
notes: First-party catalogue for the public data categories. It does not prove every 2025 file exists, a stable revision number, or public access to private participant settlement.
historical_2025: likely yes through rolling repository; file-by-file completeness open
version_relation: public file layer for S-SP-BOE-2025-RULES and OMIE implementation notices
evidence_status: confirmed catalogue; coverage/revision/IDA-continuous confidentiality open
```

### S-SP-OMIE-FORMATS-2024（confirmed format and time/unit metadata）

```yaml
source_id: S-SP-OMIE-FORMATS-2024
institution: OMIE
title: Modelo de Ficheros para la distribución pública de Información (Versión 1.35)
document_type: public-file format specification
publication_date: 2024-06 file-path version; exact signature date not stated
effective_from: current format document at access
effective_to: later format versions may supersede
url: https://www.omie.es/sites/default/files/2024-06/Formato_ficheros_inf_pub_135.pdf
accessed_at: 2026-08-21
relevant_pages: PDF pp.6-10 (headers/fields and daily/monthly/history format); p.12 (CET and IDA); pp.13-14 (daily offers, 90-day confidentiality, EUR/MWh)
relevant_sections: `Fecha Emisión`, data date, report name, semicolon fields, CET hour convention, continuous-market round/period aggregation
notes: Confirms file metadata, local-hour label, EUR/MWh price notation and the 90-day rule for daily-market offer files. It does not establish the same release period for IDA or continuous orders.
historical_2025: format/market-boundary context yes; historical file coverage open
version_relation: format layer for S-SP-OMIE-FILES-2026
evidence_status: confirmed cited sections; later format/version behavior open
```

### S-REE-ESIOS-API-2026（confirmed API routes; indicator metadata open）

```yaml
source_id: S-REE-ESIOS-API-2026
institution: Red Eléctrica de España / e·sios
title: API e·sios Documentation
document_type: public REST API documentation
publication_date: continuously maintained; no single publication date shown
effective_from: current documentation at access
effective_to: unknown
url: https://api.esios.ree.es/
accessed_at: 2026-08-21
relevant_pages: web §§3-18 (archive/date/date_type/download/JSON); §§60-90 (GET `/indicators/{id}`, `start_date`, `end_date`, `time_trunc`, indicator `value`, `datetime`, `datetime_utc`, `values_updated_at`, `magnitud` and geographic metadata, including hourly and 15-minute grouping); §2 (personal token request)
relevant_sections: `start_date`, `end_date`, `time_trunc`, `date_type=datos/publicacion`; indicator values and metadata; `datetime`/`datetime_utc`; 15-minute and hourly grouping; downloads and JSON
notes: Confirms API route families, indicator-value query fields and distinction between data date and publication date. Target indicator IDs, units, release lag, rate limits and public/private status remain open.
historical_2025: unknown until each archive/indicator is queried
version_relation: eSIOS API layer for S-REE-REData-API-2026 and S-REE-DOWNLOAD-2026
evidence_status: confirmed route; dataset-level fields/history/revision open
```

### S-ENTSOE-TP-API-2026（confirmed data-item guide; draft/operational details open）

```yaml
source_id: S-ENTSOE-TP-API-2026
institution: ENTSO-E
title: Transparency Platform Data Extraction Process Implementation Guide (version 0.3 draft)
document_type: Transparency Platform Web API/data-extraction guide
publication_date: version 0.3; exact date not stated on document page
effective_from: schema/API version-dependent; no historical 2025 go-live assumed
effective_to: unknown; draft may be superseded
url: https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fweb+api%2FIG-for-TP-data-extraction-process.pdf
accessed_at: 2026-08-21
relevant_pages: data-extraction tables pp.4-16; Art.12.1.d A44 day-ahead prices, 12.1.f A09 schedules, 12.1.g A11 physical flows, `TimeInterval`/domain dependencies
relevant_sections: Transparency Regulation data-item mapping and request dependencies
notes: Used only to register data-item codes and TimeInterval fields. It is not a Spanish rule and does not prove Spain EIC mapping, token scope, history, revision or balancing-settlement equivalence.
historical_2025: data-item concepts yes; endpoint/schema version and archive coverage open
version_relation: European transparency layer cross-checked with S-ENTSOE-EDI-2024 and local OMIE/REE sources
evidence_status: confirmed guide; draft/operational details open
```

### S-ENTSOE-TP-LIST-2022（confirmed reuse boundary; not a field dictionary）

```yaml
source_id: S-ENTSOE-TP-LIST-2022
institution: ENTSO-E
title: List of Data Available for Free Re-use
document_type: Transparency Platform reuse/licensing notice
publication_date: 2022-02-18
effective_from: notice date; current terms may supersede
effective_to: unknown
url: https://transparency.entsoe.eu/content/static_content/Static%20content/terms%20and%20conditions/220218_List_of_Data_available_for_reuse.pdf
accessed_at: 2026-08-21
relevant_pages: PDF pp.1-4 and data-item table
relevant_sections: open/free-reuse boundaries and attribution
notes: Access/licensing context only; it does not prove a specific Spanish item is available for all 2025 dates or is suitable for participant settlement.
historical_2025: platform reuse context; individual coverage open
version_relation: terms layer for S-ENTSOE-TP-API-2026
evidence_status: confirmed dated notice; current terms/dataset availability open
```

## SUP-01 FCR/SRAD 资格与预认证来源增补（访问日 2026-09-03）

### S-ENTSOE-FCR-COOP-2026（confirmed current membership; Spain entry not confirmed）

```yaml
source_id: S-ENTSOE-FCR-COOP-2026
institution: ENTSO-E / FCR Cooperation
title: Frequency Containment Reserves (FCR) Cooperation
document_type: official European TSO cooperation information page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access; historical membership boundary not stated
effective_to: unknown
url: https://www.entsoe.eu/network_codes/eb/fcr/
accessed_at: 2026-09-03
language: English
relevant_pages: web sections “Basic Principle” and “Organisational structure”; current list of 12 TSOs from 9 countries; daily four-hour symmetric product and TSO-TSO model
relevant_sections: FCR Cooperation participating TSOs; procurement principles; national BSP–TSO interaction
notes: The page lists Austria, Belgium, Czechia, Denmark, France, Germany, the Netherlands, Slovenia and Switzerland; Spain is not listed. It states that national TSO–BSP contracts and delivery responsibilities remain national. Absence from the current list is not by itself proof of the 2025 historical membership boundary or a permanent prohibition.
historical_2025: current page does not establish a full 2025 historical membership record; treat Spain’s 2025 FCR cross-border access as open unless supported by a dated Spanish/ENTSO-E source
version_relation: European FCR capacity cooperation layer; separate from PICASSO/aFRR, MARI/mFRR and TERRE/RR energy platforms
evidence_status: confirmed current page; historical/Spanish access boundary open
```

### S-CNMC-2024-6215-PO38（confirmed storage/test scope; FCR test path not listed）

```yaml
source_id: S-CNMC-2024-6215-PO38
institution: CNMC / BOE
title: Resolución de 6 de marzo de 2024 modifying P.O.3.1, P.O.3.2, P.O.3.8, P.O.3.11, P.O.14.1, P.O.14.4 and P.O.14.8 for demand, storage and hybrid participation (BOE-A-2024-6215)
document_type: CNMC resolution / operating-procedure amendment
publication_date: 2024-03-27 (disposition signed 2024-03-06)
effective_from: 2024-03-28, subject to stated transitional/application clauses; storage and demand participation in the affected processes no later than December 2024 as communicated by REE
effective_to: amended in part by later P.O. resolutions
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-6215
accessed_at: 2026-09-03
language: Spanish
relevant_pages: BOE HTML §§123-149 (P.O.3.1/3.8 changes and storage scope); P.O.3.8 annex in the attached text; publication pp.35910-36063
relevant_sections: P.O.3.8 scope includes production, demand and storage; balance-service tests are described for secondary regulation, tertiary regulation and RR; P.O.3.8 application/effective clauses in the resolution
notes: This source supports that storage is within the general testing framework for the listed balance services and that P.O.3.8 was updated for storage. The reviewed P.O.3.8 test catalogue does not provide an independent FCR/primary-storage prequalification route; this is an evidence gap, not a prohibition finding.
historical_2025: yes for the 2025 post-transition framework, subject to the precise P.O. application dates
version_relation: storage/test implementation layer under S-CNMC-2024-MP; later 2025 QH changes do not create an identified independent FCR route
evidence_status: confirmed scope; independent FCR qualification unresolved
```

### S-CNMC-2023-SRAD-22497（confirmed 2025 SRAD rule baseline）

```yaml
source_id: S-CNMC-2023-SRAD-22497
institution: CNMC / BOE
title: Resolución de 19 de octubre de 2023 approving P.O.7.5 SRAD and amending P.O.14.4 (BOE-A-2023-22497)
document_type: CNMC resolution / local specific balancing product
publication_date: 2023-11-02 (BOE no.262, pp.146972-147045); disposition signed 2023-10-19
effective_from: 2023-11-03 for the approved procedures, except the stated P.O.14.4 annex transition tied to P.O.10.5
effective_to: replaced for SRAD delivery from 2026-01-01 by S-SRAD-2025; historical 2025 annual service baseline
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2023-22497
accessed_at: 2026-09-03
language: Spanish
relevant_pages: BOE HTML §§381-446 (approval, product, eligible demand UP and habilitation); §§448-468 (structural data and auction unit); §§470-523 (annual period, offers, auction and marginal price); §§580-640 (activation, telemetry, measurement, compliance, inhabilitation and settlement); §§645-660 (publication)
relevant_sections: P.O.7.5 §§1-5.2, 6-7.5, 8-11.2, 12; P.O.14.4 SRAD payment/imbalance amendments
notes: This is the controlling SRAD P.O.7.5 baseline for the 2025 annual service, unless a later 2025 amendment is identified. It limits providers to demand programming units, requires demand CUPS/structural data/CCGD and real-time active-power telemetry, defines 15-minute activation and up to three-hour delivery, and contains auction, settlement and inhabilitation rules. Where demand is associated with storage, the text requires identifying the storage and preventing loss of storage production or increased storage consumption on activation.
historical_2025: yes; applies to the annual 2025 service period
version_relation: predecessor to S-SRAD-2025; not to be replaced by the 2026 six-month product when reconstructing 2025
evidence_status: confirmed
```

### S-CNMC-2024-SRAD-CAP-24096（confirmed 2025 auction price-cap decision）

```yaml
source_id: S-CNMC-2024-SRAD-CAP-24096
institution: CNMC / BOE
title: Resolución de 7 de noviembre de 2024 establishing the reserve price cap for the annual SRAD auction for the 2025 season (BOE-A-2024-24096)
document_type: CNMC resolution / SRAD auction price-cap decision
publication_date: 2024-11-19 (BOE no.279, pp.152591-152593); disposition signed 2024-11-07
effective_from: 2025 season auction; confidential price-cap values are not published in the non-confidential decision
effective_to: 2025 season only unless renewed
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2024-24096
accessed_at: 2026-09-03
language: Spanish
relevant_pages: BOE HTML §§66-73 (2025 annual auction basis and price-cap authority); §§81-97 (budget/unit-price rationale and approval)
relevant_sections: annual SRAD auction for 2025; confidential €/MW price cap and total budget
notes: Confirms that the 2025 SRAD framework used an annual auction and a confidential reserve price/price cap expressed in €/MW with two decimals. It does not disclose the numerical cap and does not establish independent-storage eligibility.
historical_2025: yes
version_relation: operational price-cap decision under S-CNMC-2023-SRAD-22497; later service design amended by S-SRAD-2025
evidence_status: confirmed; numeric cap confidential
```

### S-REE-BAL-PART-2026（confirmed operational entry; not a standalone FCR/SRAD qualification rule）

```yaml
source_id: S-REE-BAL-PART-2026
institution: Red Eléctrica de España
title: Cómo participar en los servicios de balance
document_type: TSO operational participation page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access; legal effect controlled by CNMC/BOE P.O. text
effective_to: unknown
url: https://www.ree.es/es/clientes/consumidor/participacion-en-servicios-de-balance/como-participar-en-los-servicios-de-balance
accessed_at: 2026-09-03
language: Spanish
relevant_pages: web participation checklist; references to minimum 1 MW, structural/real-time exchange, accredited control centre, habilitation and P.O.3.8 tests
relevant_sections: general service-entry checklist; P.O.3.8 test description for secondary and tertiary balancing energy
notes: Operational summary only. It is useful for the application sequence and contact route but cannot establish that independent storage is a qualifying provider for FCR or SRAD, nor override product-specific P.O.7.1/P.O.7.5 rules.
historical_2025: current page; historical application not assumed
version_relation: operational entry supporting S-CNMC-2024-MP and S-CNMC-2023-SRAD-22497
evidence_status: confirmed operational page; normative status limited
```

## SUP-02 SOC、持续时长、补能与恢复来源增补（访问日 2026-09-03）

### S-EU-SOGL-2017（confirmed EU technical baseline; not standalone Spanish qualification）

```yaml
source_id: S-EU-SOGL-2017
institution: European Commission / EUR-Lex
title: Commission Regulation (EU) 2017/1485 establishing a guideline on electricity transmission system operation (SOGL)
document_type: EU regulation / system-operation guideline
publication_date: 2017-08-25 in OJ L 220 (act dated 2017-08-02)
effective_from: 2017-09-14 (20th day after Official Journal publication; Articles 41-53 have their own later application clause)
effective_to: in force; consolidated version shown by EUR-Lex at access
url: https://eur-lex.europa.eu/eli/reg/2017/1485/oj/eng
accessed_at: 2026-09-03
language: English (Spanish language version available through EUR-Lex)
relevant_pages: HTML Articles 154-162, web lines 2822-3064 at access; official journal pp. 93-101 in the cited version
relevant_sections: Art.154 FCR technical minimums and data; Art.155 FCR prequalification; Art.156 FCR availability, limited-energy reservoirs and recovery; Arts.158-159 FRR requirements/prequalification; Arts.160-162 RR requirements/prequalification
notes: Applies as an EU system-operation baseline to the Continental Europe synchronous area, including Spain. It does not by itself create a Spanish BSP registration, product payment or independent-storage qualification route. Article 156's limited-energy-reservoir duration and recovery language must be read with the current CE methodology/decisions; it is not a Spanish battery SOC percentage rule.
historical_2025: yes; EU baseline in force throughout 2025
version_relation: upper-level EU framework supporting, but not replacing, Spanish CNMC/REE P.O.7.x and P.O.3.8 rules
evidence_status: confirmed EU text; Spanish implementation and independent-storage FCR route remain open
```

### S-ACER-2026-FCR-MIN-ACT（confirmed pending CE decision; baseline uncertainty）

```yaml
source_id: S-ACER-2026-FCR-MIN-ACT
institution: ACER
title: ACER to decide on minimum activation period for frequency containment reserves providers
document_type: official ACER news/decision-process notice
publication_date: 2026-07-21
effective_from: process notice; no final decision effective at the research baseline
effective_to: unknown; ACER states it intends to decide within six months of the CE NRA request
url: https://www.acer.europa.eu/news/acer-decide-minimum-activation-period-frequency-containment-reserves-providers
accessed_at: 2026-09-03
language: English
relevant_pages: web sections describing the 2026-07-07 CE NRAs request and the six-month decision intention
relevant_sections: minimum activation period for FCR providers with limited energy reservoirs in Continental Europe; CE includes Spain
notes: The notice confirms that the 15–30 minute limited-energy FCR activation-period question was still being decided in July 2026. It is not evidence of a final Spanish FCR/SOC requirement and must not be used to fix a battery duration at 2025 or 2026-08-11.
historical_2025: no; post-historical process notice only
version_relation: current process update to S-EU-SOGL-2017 Art.156; does not supersede the 2025 historical baseline
evidence_status: confirmed pending process; final value open-critical
```

### S-CNMC-2023-8113-PO92（confirmed historical storage telemetry; superseded after baseline）

```yaml
source_id: S-CNMC-2023-8113-PO92
institution: CNMC / BOE
title: Resolución de 16 de marzo de 2023 modifying P.O.3.8 and P.O.9.2 (BOE-A-2023-8113)
document_type: CNMC resolution / operating-procedure amendment
publication_date: 2023-03-30 (disposition signed 2023-03-16)
effective_from: 2023-03-31 under the resolution's publication/effect clauses
effective_to: P.O.9.2 replaced with effect from 2026-09-01 by S-CNMC-2026-14009; the present study baseline is 2026-08-11
url: https://boe.es/buscar/doc.php?id=BOE-A-2023-8113
accessed_at: 2026-09-03
language: Spanish
relevant_pages: BOE HTML P.O.9.2 Annex I storage-at-transmission provisions around §§1274-1300; Annex II distribution-storage provisions around §§1520-1545; effect clauses around §§1550-1562
relevant_sections: P.O.9.2 Annex I/II storage telemetry fields: active power in/out, reactive power, voltage, SOC as percentage of maximum capacity, actual producible power and expected production for the next four hourly periods; aFRR local/remote and control/no-control flags where applicable
notes: The text proves a telemetry/reporting field for SOC and expected production. It does not prescribe a minimum or maximum SOC, usable-energy duration, recharge window or restoration target. It applies to the 2025 historical period and 2026-08-11 baseline; do not use the later replacement as if effective earlier.
historical_2025: yes
version_relation: storage telemetry layer under Spanish P.O.9.2; replaced after the study baseline by S-CNMC-2026-14009
evidence_status: confirmed for historical/baseline boundary; later replacement noted
```

### S-CNMC-2026-14009-TELEMETRY（confirmed post-baseline boundary; not applicable to 2025 or 2026-08-11）

```yaml
source_id: S-CNMC-2026-14009-TELEMETRY
institution: CNMC / BOE
title: Resolución de 19 de junio de 2026 modifying P.O.9.2 and P.O.14.4 (BOE-A-2026-14009)
document_type: CNMC resolution / operating-procedure amendment
publication_date: 2026-06-27 (disposition signed 2026-06-19)
effective_from: 2026-09-01
effective_to: unknown
url: https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-14009
accessed_at: 2026-09-03
language: Spanish
relevant_pages: BOE HTML storage telemetry around §§753-770; P.O.14.4 §30 and penalty table around §§992-1050; effect clauses around §§1124-1131
relevant_sections: storage SOC/active-power/expected-production telemetry; monthly fixed and MW-linked penalties for telemetry quality, telemetry non-compliance and control-centre assignment from 2026-09-01
notes: This is a forward version-boundary source only. It cannot be backfilled to 2025 or the 2026-08-11 baseline. The penalty amounts are included to flag the post-baseline compliance change, not as historical model inputs.
historical_2025: no
version_relation: replaces the historical P.O.9.2 source S-CNMC-2023-8113-PO92 and modifies P.O.14.4 after the research baseline
evidence_status: confirmed future/post-baseline rule; not applicable to the requested historical/baseline period
```

## SUP-03 RR/96 轮连续日内过渡来源（访问日 2026-09-03）

### S-SP-OMIE-INST4-2026（confirmed planned go-live; completion future at access）

```yaml
source_id: S-SP-OMIE-INST4-2026
institution: OMIE
title: INSTRUCCIÓN 4/2026 — Detalle de la puesta en operación del Mercado Intradiario Continuo con 96 rondas
document_type: OMIE market instruction / operational go-live notice
publication_date: 2026-08-11
effective_from: planned 2026-09-22 after scheduled maintenance; first delivery day 2026-09-23
effective_to: unknown
url: https://www.omie.es/sites/default/files/2026-08/instruccion-4-2026-puesta-en-funcionamiento-de-la-negociacion-del-mercado-intradiario-continuo-en-96-rondas.pdf
accessed_at: 2026-09-03
language: Spanish
relevant_pages: PDF pp.1-6; pp.1-2 application notice and 2026-09-22/23 plan; pp.2-4 maintenance after round 24, no-offer window and IDA2; pp.4-6 disaggregation/defaults and IDA3 transition
relevant_sections: CNMC 2026-07-30 rule reference; OMIE/RE/REN coordination; LTS client; maintenance, portfolio disaggregation, default PIBCIC/PT values and round-45/47 exception
notes: This is the first located OMIE notice with a concrete date. At the 2026-09-03 access date the planned start and first delivery were still in the future, so it proves a planned application/go-live date, not completed operation. It does not create an RR replacement product.
historical_2025: no; 2025 appears only as prior-version context
version_relation: operational notice implementing S-SP-BOE-2026-17285 and S-SP-BOE-2026-17570
evidence_status: confirmed notice; completed go-live and first successful delivery open
```

### S-SP-REE-BALANCE-2026（confirmed current balance-service entry; no RR replacement identified）

```yaml
source_id: S-SP-REE-BALANCE-2026
institution: Red Eléctrica de España (REE)
title: Participación en servicios de balance / Participation in balancing services
document_type: TSO operational participation page
publication_date: continuously maintained; no single publication date shown
effective_from: current page at access; legal effect remains with CNMC/BOE procedures
effective_to: unknown
url: https://www.ree.es/es/clientes/generador/participacion-en-servicios-de-balance
accessed_at: 2026-09-03
language: Spanish
relevant_pages: web §§19-45; current service list and European platform connection summary
relevant_sections: aFRR/P.O.7.2, mFRR/P.O.7.3 and platform connections (IGCC, MARI, PICASSO); no new RR service entry shown on the reviewed current page
notes: Operational page used as a negative-evidence boundary only. Its omission of a 2026 RR replacement does not prove a legal prohibition; combined with P.O.3.3 repeal and ENTSO-E TERRE status, it supports keeping a named replacement, qualification, bid, activation and settlement path open-critical.
historical_2025: current page; not used to rewrite 2025
version_relation: current operational view supporting, but not replacing, P.O.7.x and BOE rules
evidence_status: confirmed current page; normative status limited; RR replacement remains open
```

### S-SP-REE-RR-96-PROP-2026（confirmed proposal timeline; not a final rule）

```yaml
source_id: S-SP-REE-RR-96-PROP-2026
institution: Red Eléctrica de España (REE)
title: Consultas públicas — propuesta de modificación de P.O.3.1, P.O.3.3, P.O.7.2, P.O.9.1 y P.O.14.4 para 96 rondas y post-TERRE
document_type: TSO public-consultation register
publication_date: 2026-01-30 consultation; definitive proposal entry published 2026-04-16
effective_from: consultation/proposal process only; not itself an effective rule
effective_to: unknown
url: https://www.ree.es/es/clientes/consultas-publicas
accessed_at: 2026-09-03
language: Spanish
relevant_pages: current page 2026 entries; entry dated 2026-04-16 and consultation dated 2026-01-30
relevant_sections: proposal title explicitly joining 96-round adaptation with post-TERRE P.O.3.3 treatment
notes: Confirms the regulatory workstream and timing, but cannot establish a final RR replacement product or its qualification/settlement terms. Final normative evidence is S-SP-BOE-2026-17285 and related P.O. text.
historical_2025: no; process occurred after the 2025 historical period
version_relation: consultation/proposal precursor to S-SP-BOE-2026-17285
evidence_status: confirmed proposal timeline; final RR replacement open
```

### S-SP-OMIE-96-CONSULT-2026（confirmed consultation context; fallback detail not normative）

```yaml
source_id: S-SP-OMIE-96-CONSULT-2026
institution: OMIE
title: Informe justificativo del resultado de la consulta pública sobre la propuesta de modificación de las reglas para 96 rondas
document_type: OMIE public-consultation result report
publication_date: 2026-03-09
effective_from: consultation outcome only; not an effective market rule
effective_to: unknown
url: https://www.omie.es/sites/default/files/2026-03/informe-justificativo-resultado-de-la-consulta-publica-96r.pdf
accessed_at: 2026-09-03
language: Spanish
relevant_pages: PDF pp.1-7 and consultation responses on the 96-round implementation and XBID-flow functionality
relevant_sections: proposal sent to MIBEL regulators; temporary normal/emergency procedure if central XBID flow functionality was not operational before go-live
notes: Process and fallback context only. The later BOE/OMIE notice chain controls application; this report does not define RR replacement eligibility or settlement.
historical_2025: no; not backfilled to 2025
version_relation: consultation context for S-SP-BOE-2026-17570 and S-SP-OMIE-INST4-2026
evidence_status: confirmed consultation report; operational implementation status at 2026-09-03 partly open
```

### SUP-03 source-status summary

| Source ID | Use | Historical/baseline boundary | Status |
|---|---|---|---|
| S-ENTSOE-TERRE-2026 | TERRE/LIBRA last MTU, 10:00 stop and former-member status | 2025-12-30 / 2026-01-01; no backfill | confirmed |
| S-SP-BOE-2026-17285 | System procedures, P.O.3.3 repeal, PHF/PHFC plan chain | Published 2026-08-07; applied only at agreed date | confirmed; completed operation post-baseline |
| S-SP-BOE-2026-17570 | Market-rule layer, 96/92/100 rounds, IDA schedule and orders | Published 2026-08-11; not a 2025 rule | confirmed; completed operation post-baseline |
| S-SP-OMIE-INST4-2026 | Concrete 2026-09-22/23 planned go-live and transition maintenance | Notice dated 2026-08-11; future at 2026-09-03 | confirmed plan; actual completion open |
| S-SP-REE-BALANCE-2026 | Current aFRR/mFRR service-entry boundary; no named RR replacement located | Current page; not used to rewrite 2025 | confirmed operational page; normative status limited |
| S-SP-REE-RR-96-PROP-2026 | REE consultation/proposal workstream | 2026 post-2025 process | confirmed proposal; not final rule |
| S-SP-OMIE-96-CONSULT-2026 | 96-round implementation and temporary flow-fallback context | 2026 process only | confirmed consultation; implementation detail partly open |

## SUP-04 项目级账户和代码映射来源（访问日 2026-09-03）

### S-SP-OMIE-PUBFILES-2025（confirmed format version; project-level crosswalk open）

```yaml
source_id: S-SP-OMIE-PUBFILES-2025
institution: OMIE
title: Modelo de Ficheros para la distribución pública de Información del mercado de electricidad, Versión 1.37
document_type: OMIE public-file format specification
publication_date: 2025-09-30
effective_from: 2025-09-30 for the v1.37 format document; each file category may have its own implementation date
effective_to: later OMIE format versions may supersede
url: https://www.omie.es/sites/default/files/2025-09/formato_ficheros_inf_pub_137.pdf
accessed_at: 2026-09-03
language: Spanish
relevant_pages: PDF pp.1-2 (title/date and revision history); pp.6-10 (header, issue date/data date and records); sections describing public market files, programs and offers, including PHFC and bid-unit fields
relevant_sections: Version 1.36 effective 2025-03-18; v1.37 effective 2025-09-30; semicolon-delimited files; `Fecha Emisión`, data date, file fields and records; offer/program file identifiers such as `IdRemitente`, `IdOferta`, `IdUnidad` and `tipo=UO` where present
notes: First-party format dictionary used only to trace the OMIE-side identifiers and file lineage. It does not publish the private participant crosswalk from OMIE UO to REE UP/UF, CUPS, SIMEL or BRP settlement records. Public confidentiality and category-specific field availability remain open.
historical_2025: v1.36/v1.37 provide 2025 version boundaries; individual 2025 file completeness and production mapping remain open
version_relation: supersedes S-SP-OMIE-FORMATS-2024 for the v1.37 public-file format layer; no retroactive assumption is made for dates before each effective format
evidence_status: confirmed format document; project-level crosswalk open
```

### S-REE-ADMISSION-GUIDE-2024（confirmed general code workflow; generation-focused limitations）

```yaml
source_id: S-REE-ADMISSION-GUIDE-2024
institution: Red Eléctrica de España (REE)
title: Guía práctica para la admisión de un nuevo sujeto de liquidación de instalaciones RCR (Agosto 2024)
document_type: REE participant/admission guide (non-normative explanatory guide)
publication_date: 2024-08
effective_from: explanatory guide at issue; P.O.14.x and current REE procedures control
effective_to: later REE guide versions may supersede
url: https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/normativa_guias/GEN_ParticipacionMercadoP_solicitudalta.pdf
accessed_at: 2026-09-03
language: Spanish
relevant_pages: PDF pp.8-10 (participant, installation and UP long/short codes; UP/UF/EIC workflow); pp.11-16 (Portal de Servicios, GDE, guarantees and admission sequence)
relevant_sections: registration from PRETOR/RAIPRE and CIL-RAIPRE data; participant, physical facility and UP identifiers; EIC through the Spanish local office; GDE and Portal de Servicios workflow
notes: The guide is centred on RCR generation installations. It is used to confirm the general admission/code workflow and as a boundary source, not to infer that every pure independent BESS has a CIL or the same generation code list. The project-specific independent-storage path remains U/open-critical.
historical_2025: 2024 guide available before the 2025 historical period; exact project application version must be obtained
version_relation: operational guide related to P.O.14.2/P.O.3.1/P.O.14.1/P.O.14.3/P.O.14.4; not a replacement for BOE rules
evidence_status: confirmed general workflow; storage-specific applicability open
```

## SUP-06 晚间日前电价与 price-setting 数据来源（访问日 2026-09-04）

### S-SP-OMIE-ANNUAL-2024（confirmed annual price-setting summary）

```yaml
source_id: S-SP-OMIE-ANNUAL-2024
institution: OMIE
title: Annual Report 2024
document_type: OMIE annual electricity-market report
publication_date: 2025-02-19
effective_from: report covers 2024 market results
effective_to: 2024-12-31 for reported statistics
url: https://www.omie.es/sites/default/files/2025-02/informe-anual-en.pdf
accessed_at: 2026-09-04
language: English PDF
relevant_pages: PDF pp.17-18 (figures 1.11-1.14)
relevant_sections: Figure 1.11/1.12 energy classified at 95% of marginal price; Figure 1.13/1.14 percentage of hours in which each technology sets a price
notes: The annual report states that hydro, wind, solar photovoltaics and biomass/cogeneration/waste are the technologies with the most marginal hours in Spain. The 95% energy graph and the setter graph are separate measures; percentages are not generation shares.
historical_2025: no; used as an official 2024 methodological and context reference
version_relation: annual context for S-SP-OMIE-MONTHLY-2025; not backfilled into 2025
evidence_status: confirmed report and figure locations; unit-level setter reconstruction remains out of scope
```

### S-SP-OMIE-MONTHLY-2025（confirmed January-March report boundary and 95% caveat）

```yaml
source_id: S-SP-OMIE-MONTHLY-2025
institution: OMIE
title: Informe mensual enero, febrero y marzo de 2025
document_type: OMIE monthly market reports
publication_date: 2025-02-18 (January); 2025-03-27 (February); 2025-04-29 (March)
effective_from: each report covers its named delivery month
effective_to: 2025-03-31 for the March report; the 95% technology series in March stops at 2025-03-18
url: https://www.omie.es/sites/default/files/2025-02/informe-mensual-enero-2025_es.pdf; https://www.omie.es/sites/default/files/2025-03/informe-mensual-febrero-2025_es.pdf; https://www.omie.es/sites/default/files/2025-04/informe-mensual-marzo-2025_es.pdf
accessed_at: 2026-09-04
language: Spanish PDFs
relevant_pages: March PDF pp.2-3 (new bid typology and 2025-03-19 first delivery); p.14 (95% technology graph and explicit stop at 2025-03-18); p.15 (price-setting technology graph). January and February PDFs contain the corresponding daily-market figures 1.5 and 1.8 on pp.10-11.
relevant_sections: “Energía por tecnología al 95% del precio marginal” and “Tecnologías que marcan precio en el mercado diario”
notes: OMIE defines the 95% series as matched energy with offered price at or above 95% of the marginal price, including complex bids, and explicitly says the graph does not show the technology setting the marginal price. The March report says the technology-at-95% data are only available through 2025-03-18 because the new bid typology prevents obtaining that technology breakdown afterward. The 1.8 charts were downloaded and decoded from the vector-color grid; the extracted 2025-01-01—2025-03-18 file and page-level render checks are recorded in review_ES_SP_SETTER_20250101_20250318_2026-09-04.md.
historical_2025: yes; official setter calibration window is 2025-01-01—2025-03-18
version_relation: pre/post 2025-03-18 boundary source for ES-SP-PRICE-01
evidence_status: confirmed monthly reports, boundary and vector-grid hour-label extraction; report technology labels are confirmed, while UO-level technology crosswalk remains open
```

### S-SP-OMIE-CAM-2025（confirmed peak/off-peak aggregation and multi-label note）

```yaml
source_id: S-SP-OMIE-CAM-2025
institution: OMIE
title: Tecnologías que marcan precio en el mercado diario — Comité de Agentes del Mercado, 14 May 2025
document_type: OMIE CAM presentation
publication_date: 2025-05-14
effective_from: presentation reports 2025 data through 2025-03-18
effective_to: 2025-03-18 for the reported 95%/setter figures
url: https://www.omie.es/sites/default/files/2025-05/presentacion_cam_omie_2025_05_14_v2.pdf
accessed_at: 2026-09-04
language: Spanish PDF
relevant_pages: PDF p.24 (hours punta 08:00-22:00 and horas valle 22:00-08:00, percentage of hours by technology and explanatory note)
relevant_sections: “Horas en las que marca precio cada tecnología”; “Energía casada por encima del 95% del precio marginal”
notes: OMIE warns that technology percentages can sum above 100% because more than one technology may set price in the same hour; in coupled hours units from the other zone may set the local price. The 08:00-22:00 bucket is not a substitute for the 19:00-22:00 evening sample.
historical_2025: yes for the reported slice; not a unit-level setter file
version_relation: contextual cross-check for S-SP-OMIE-MONTHLY-2025 and ES-SP-PRICE-01
evidence_status: confirmed presentation and aggregation note; exact evening-hour values require raw-file reconstruction
```

### S-SP-OMIE-INST1-2025（confirmed 2025-03-18 implementation boundary）

```yaml
source_id: S-SP-OMIE-INST1-2025
institution: OMIE
title: INSTRUCCIÓN 1/2025 — Inicio de la negociación cuarto-horaria en los mercados intradiarios y de la nueva tipología de ofertas en el mercado diario
document_type: OMIE market-operation instruction
publication_date: 2025-03-07
effective_from: session operated on 2025-03-18 for delivery date 2025-03-19
effective_to: replaced/superseded by later implementation instructions where applicable
url: https://www.omie.es/sites/default/files/2025-03/instruccion_1_2025_es.pdf
accessed_at: 2026-09-04
language: Spanish PDF
relevant_pages: PDF pp.1-4 (application date; daily market remains 24 hourly periods for 2025-03-19; intraday markets move to quarter-hourly; accepted new bid types)
relevant_sections: §§1-3, especially the session operated 18 March for delivery 19 March and the PDBC/PDBF resolution description
notes: This is the source for the calibration cut at 2025-03-18 and for separating the new bid typology from the later 2025-10-01 day-ahead MTU15 change.
historical_2025: yes
version_relation: implementation boundary for S-SP-OMIE-MONTHLY-2025 and S-SP-OMIE-MTU15-DA-2025
evidence_status: confirmed official instruction; data availability by file category still requires checking
```

### S-SP-OMIE-UOF-ARCHIVE-2026（confirmed monthly UOF curve archive listing）

```yaml
source_id: S-SP-OMIE-UOF-ARCHIVE-2026
institution: OMIE
title: Ficheros mensuales con curvas agregadas de oferta y demanda del mercado diario incluyendo unidades de oferta
document_type: OMIE public file access listing
publication_date: continuously maintained; listed files show archive change timestamps
effective_from: current listing at access
effective_to: unknown; rolling catalogue may change
url: https://www.omie.es/en/file-access-list?dir=Ficheros+mensuales+con+curvas+agregadas+de+oferta+y+demanda+del+mercado+diario+incluyendo+unidades+de+oferta&parents=/Mercado+Diario/3.+Curvas&realdir=curva_pbc_uof
accessed_at: 2026-09-04
language: English web page
relevant_pages: web §§49-71 (monthly `curva_pbc_uof_YYYYMM.zip` entries, including 2025-01, 2025-02 and 2025-03)
relevant_sections: Mercado Diario → Curvas → monthly curves including offer units
notes: The listing demonstrates a public archive entry for the monthly UOF curve packages. It does not by itself guarantee immutable versions, all revisions, or a published UO-to-technology crosswalk.
historical_2025: yes for the listed 2025-01—03 packages; file contents and revision lineage must be recorded after download
version_relation: raw curve layer for ES-SP-PRICE-01
evidence_status: confirmed listing; package-level schema and crosswalk remain open
```

### S-SP-OMIE-FORMATS-2025（confirmed CURVA_PBC and MARGINALPDBC fields）

```yaml
source_id: S-SP-OMIE-FORMATS-2025
institution: OMIE
title: SIOM Descripción de los formatos de intercambio entre OM y AM. Vol. I — Mercado, versión 3.1
document_type: OMIE exchange-file format specification
publication_date: 2025-04-07 (edition date in document)
effective_from: format version at issue; historical category implementation must be checked file by file
effective_to: later format versions may supersede
url: https://www.omie.es/sites/default/files/2024-03/Formatos_Intercambio_OM_Vol_I-Mercado.pdf
accessed_at: 2026-09-04
language: Spanish PDF
relevant_pages: PDF pp.107-113 (CURVA_PBC fields and offer-type codes; MARGINALPDBC fields)
relevant_sections: §3.3.12 CURVA_PBC; §3.3.14 MARGINALPDBC
notes: CURVA_PBC documents `Periodo`, `Fecha`, `Pais`, buy/sell, power, price, offered/cashed flag and offer typology. MARGINALPDBC documents `MarginalPT` and `MarginalES`. The specification also explains how complex orders, imports/exports and market splitting affect displayed curve prices.
historical_2025: format evidence yes; category-level historical schema/revision still open
version_relation: field-definition layer for S-SP-OMIE-UOF-ARCHIVE-2026 and S-SP-OMIE-MONTHLY-2025
evidence_status: confirmed field descriptions; UOF package-specific columns and technology mapping remain open
```

### S-REE-PARTICIPANT-2026（confirmed current participant entry; normative status limited）

```yaml
source_id: S-REE-PARTICIPANT-2026
institution: Red Eléctrica de España (REE)
title: Solicita el alta como participante — Participación en el mercado de producción peninsular
document_type: REE operational participant-admission page
publication_date: continuously maintained page; no single publication date shown
effective_from: current operational page at access; P.O.14.2/P.O.3.1/P.O.14.x control legal effect
effective_to: unknown
url: https://www.ree.es/es/clientes/generador/participacion-mercado-peninsular/solicita-el-alta-como-participante
accessed_at: 2026-09-03
language: Spanish
relevant_pages: web §§17-42 (participation through UP; EIC application; GDE and Portal de Servicios; coordination with OMIE)
relevant_sections: UP is the participation unit; each UP and, where applicable, UF requires EIC; participant admission and UP/UF structural changes are submitted through REE services and coordinated with OMIE
notes: Current operational entry used to identify the actual REE portal path. It does not reveal a project's private codes, account identifiers or storage-specific CUPS/CIL mapping.
historical_2025: current page only; no unverified historical backfill
version_relation: operational entry supporting S-REE-ADMISSION-GUIDE-2024 and P.O.3.1/P.O.14.2
evidence_status: confirmed operational entry; normative status limited
```

### S-REE-SIMEL-FAQ-STORAGE-2026（confirmed meter-access/material boundary; CUPS/CIL applicability open）

```yaml
source_id: S-REE-SIMEL-FAQ-STORAGE-2026
institution: Red Eléctrica de España (REE)
title: Preguntas frecuentes — Titular de almacenamiento / Gestión de medidas eléctricas
document_type: REE storage measurement FAQ and operational page
publication_date: continuously maintained page; no single publication date shown
effective_from: current page at access; P.O.10.x/SIMEL procedures control legal effect
effective_to: unknown
url: https://www.ree.es/es/clientes/titular-de-almacenamiento/gestion-medidas-electricas/preguntas-frecuentes
accessed_at: 2026-09-03
language: Spanish
relevant_pages: web §§100-105 (SIMEL secure access); §§146-159 (frontier-point admission documents); §§169-184 (provisional certificate and CUPS/CIL steps for specified generation cases)
relevant_sections: SIMEL access is restricted to each measurement participant/delegate; single-line/three-line diagrams, equipment, authorisations, tests and technical contracts for frontier-point admission; CUPS/CIL conditions are stated in a specific generation/commissioning context
notes: Confirms the measurement-system access and material boundary. It does not establish a universal CUPS or CIL requirement for a pure independent electrochemical BESS, nor provide the project's point-meter-to-UP/UF field dictionary.
historical_2025: current operational page; no historical project mapping inferred
version_relation: current SIMEL/storage operational layer; read with MITECO P.O.10.x and P.O.14.x
evidence_status: confirmed access/material boundary; pure-independent-storage mapping open-critical
```

### S-REE-PF-CIL-2015（confirmed historical CUPS/CIL boundary; not a current independent-BESS rule）

```yaml
source_id: S-REE-PF-CIL-2015
institution: Red Eléctrica de España (REE)
title: Alta, modificación y baja de puntos frontera de generación, consumo y servicios auxiliares — Versión 16 (mayo 2015)
document_type: REE SIMEL frontier-point guide
publication_date: 2015-05
effective_from: guide version at issue; later SIMEL/measurement rules may supersede
effective_to: superseded/operationally dated; not used as a 2025 current rule without version confirmation
url: https://www.ree.es/sites/default/files/01_ACTIVIDADES/Documentos/Documentacion-Simel/alta_fronteras_unificado_v16.pdf
accessed_at: 2026-09-03
language: Spanish
relevant_pages: PDF pp.15-17 (CUPS/CIL composition and association in the generation context)
relevant_sections: CIL construction from CUPS and phase suffix for renewable/cogeneration/waste generation; relationship of CIL and CUPS
notes: Boundary source only. It demonstrates that CIL/CUPS are established concepts in certain generation measurement flows, but is old and generation-focused; it cannot prove the current code path for a pure independent BESS.
historical_2025: historical background only; exact 2025 application not assumed
version_relation: predecessor context for later SIMEL/storage procedures
evidence_status: confirmed historical guide; current independent-storage applicability open-critical
```

### S-REE-EIC-2026（confirmed EIC office entry）

```yaml
source_id: S-REE-EIC-2026
institution: Red Eléctrica de España (REE)
title: Mercado interior de la energía — Oficina EIC
document_type: REE operational EIC information page
publication_date: continuously maintained page; no single publication date shown
effective_from: current page at access; EIC scheme documents and applicable system rules control
effective_to: unknown
url: https://www.ree.es/es/operacion/mercado-interior-energia
accessed_at: 2026-09-03
language: Spanish
relevant_pages: web §§111-115 (EIC office and purpose)
relevant_sections: Spanish EIC office and ENTSO-E EIC scheme for unique identification in internal electricity-market data exchange
notes: Confirms where the Spanish EIC function is located and why EICs are used. It does not expose a project code or equate EIC with OMIE UO, CUPS or mRID.
historical_2025: current page; historical code values and validity dates remain project-specific
version_relation: Spanish operational entry for S-ENTSOE-EIC-2026
evidence_status: confirmed operational entry; project values open
```

### S-ENTSOE-EIC-2026（confirmed EIC scheme and code authorities）

```yaml
source_id: S-ENTSOE-EIC-2026
institution: ENTSO-E
title: Energy Identification Codes (EICs)
document_type: ENTSO-E EIC scheme page and code-list entry point
publication_date: continuously maintained page; no single publication date shown
effective_from: current EIC scheme at access; individual code validity is code-list dependent
effective_to: unknown
url: https://www.entsoe.eu/data/energy-identification-codes-eic/
accessed_at: 2026-09-03
language: English
relevant_pages: web §§127-153 (EIC scheme, CIO/LIO, code lists and supporting documents)
relevant_sections: harmonised Energy Identification Coding scheme for electronic data interchange; Central Issuing Office and Local Issuing Offices
notes: Used for the hierarchy and authority of EIC codes only. It does not provide a Spain-specific cross-table from EIC to OMIE UO, SIMEL point or BRP settlement account.
historical_2025: EIC framework applicable; individual 2025 code validity and project values open
version_relation: EU/ENTSO-E coding layer supporting Spanish REE EIC operations
evidence_status: confirmed scheme; cross-institution mapping open
```

### S-ENTSOE-MRID-2024（confirmed CIM resource/mRID semantics; Spanish crosswalk open）

```yaml
source_id: S-ENTSOE-MRID-2024
institution: ENTSO-E
title: Configuration document — UML model and schema, Version 1.1
document_type: ENTSO-E CIM/EDI schema document
publication_date: 2024 (version 1.1; exact signature date not stated on the PDF landing page)
effective_from: schema-version dependent
effective_to: later schema versions may supersede
url: https://www.entsoe.eu/Documents/EDI/Library/cim_based/schema/Configuration_document_UML_model_and_schema_v1.1.pdf
accessed_at: 2026-09-03
language: English
relevant_pages: PDF pp.152-160 (Provider_MarketParticipant and RegisteredResource attributes)
relevant_sections: `Provider_MarketParticipant.mRID` identifies a party; `RegisteredResource.mRID` is the unique identification of a registered resource; resource names are human-readable and need not be unique
notes: Defines mRID at the ENTSO-E/CIM model layer. It does not state that a Spanish mRID is the same value as a REE UP/UF EIC, OMIE UO, CUPS or project account. The field-level crosswalk and message context remain open-critical.
historical_2025: schema semantics only; no assertion that a particular 2025 Spanish dataset exposed the same fields
version_relation: detailed mRID semantics supporting S-ENTSOE-EDI-2024; newer process schemas may add context
evidence_status: confirmed model semantics; Spain project mapping open-critical
```

### SUP-04 source-status summary

| Source ID | 用途 | 版本/时间边界 | 状态 |
|---|---|---|---|
| S-SP-PO31-2024-STORAGE | 独立储能送出/吸收UP、UP/UF/EIC、PM/代表结构 | 2025 historical/baseline rule structure | confirmed rule; project values open |
| S-SP-BOE-2025-RULES | OMIE UO、代表、BRP/结算主体、市场计划和结算标识 | 2025-03-18起的修订规则；更早日期按旧版切片 | confirmed rule; version-by-date crosswalk open |
| S-SP-OMIE-PUBFILES-2025 | OMIE报价/文件字段与文件发行/数据日期 | v1.36 2025-03-18; v1.37 2025-09-30 | confirmed format; historical/public-file completeness open |
| S-REE-ADMISSION-GUIDE-2024 | 一般参与者/UP/UF/EIC/GDE代码申请流程 | 2024 guide; generation-focused | confirmed guide; pure-BESS applicability open |
| S-REE-PARTICIPANT-2026 | 当前REE参与者、UP/UF/EIC入口 | current operational page | confirmed operational entry; normative status limited |
| S-REE-SIMEL-FAQ-STORAGE-2026 | SIMEL权限、边界点材料、CUPS/CIL限定流程 | current page; no historical backfill | confirmed boundary; independent-BESS mapping open-critical |
| S-REE-EIC-2026 / S-ENTSOE-EIC-2026 | 西班牙EIC办公室和ENTSO-E编码体系 | current coding framework | confirmed; project crosswalk open |
| S-ENTSOE-MRID-2024 / S-ENTSOE-EDI-2024 | mRID/CIM/EDI消息层语义 | schema-version dependent | confirmed semantics; Spain mapping open-critical |
| S-REE-LIQ-ACCESS-2026 / S-REE-LIQ-GUIDE-2024 | 私有结算访问与文件字段边界 | current access; 2024 guide | confirmed access boundary; project settlement files open |

## SUP-05 数据接口、版本与权限来源（访问日 2026-09-03）

### S-REE-ESIOS-ARCHIVE-API-2026（confirmed route; dataset coverage open）

```yaml
source_id: S-REE-ESIOS-ARCHIVE-API-2026
institution: Red Eléctrica de España / e·sios
title: Archive API — list archives by start_date, end_date and date_type
document_type: public API documentation
publication_date: continuously maintained documentation; no single publication date shown
effective_from: current documentation at access
effective_to: unknown; later API documentation may supersede
url: https://api.esios.ree.es/doc/archive/getting_a_list_of_archives_by_start_date%2C_end_date_and_date_type_datos.html
accessed_at: 2026-09-03
language: English API documentation
relevant_pages: web §§2-15 (archive query); §§33-63 (request/response example)
relevant_sections: GET `/archives`; `start_date`, `end_date` and `date_type` parameters; `date_type` accepts `datos` or `publicacion`; response exposes archive id, archive type, data-date interval, `date_times`, `publication_date`, taxonomy and download URL
notes: Establishes the interface distinction between the date of the data and the date of publication. It does not verify that every balancing archive or every 2025 date has a complete, unrevised file.
historical_2025: date filtering can target 2025, but archive-by-archive coverage and republication history remain open
version_relation: archive metadata layer supporting S-REE-ESIOS-API-2026 and S-REE-DOWNLOAD-2026
evidence_status: confirmed route and metadata fields; historical coverage/revision open
```

### S-REE-DST-2025（confirmed 2025 operational calendar; measurement estimation boundary）

```yaml
source_id: S-REE-DST-2025
institution: Red Eléctrica de España / e·sios
title: Publicación de información referente al servicio de respuesta activa de la demanda 2025
document_type: REE operational publication and 2025 calendar notice
publication_date: October 2024 (document title and issue context)
effective_from: calendar applies to 2025 operational planning; not a substitute for P.O.10.x
effective_to: 2025 calendar only
url: https://api.esios.ree.es/documents/2496/download?locale=en
accessed_at: 2026-09-03
language: Spanish/English PDF
relevant_pages: PDF p.3 (2025 holidays and daylight-saving Sundays)
relevant_sections: 30 March 2025 identified as 23-hour day; 26 October 2025 identified as 25-hour day, with H21-H23/H23-H25 period labels
notes: This is an operational annual calendar notice, not a general market-rule amendment. P.O.10.5's missing-measurement treatment for 23/25-hour days is separately supported by S-MITECO-2025-ISP.
historical_2025: yes for the listed calendar dates; exact period numbering of each dataset must still be verified
version_relation: calendar evidence supporting S-MITECO-2025-ISP and the local-time conversion rules
evidence_status: confirmed calendar boundary; dataset-specific period mapping open
```

### S-SP-OMIE-PDBC-ARCHIVE-2026（confirmed listing sample; full category coverage open）

```yaml
source_id: S-SP-OMIE-PDBC-ARCHIVE-2026
institution: OMIE
title: Programa diario base de casación español — public file access list
document_type: OMIE public file catalogue and rolling archive listing
publication_date: continuously maintained page; individual archive change timestamps shown
effective_from: current catalogue at access
effective_to: unknown; catalogue and archive availability can change
url: https://www.omie.es/en/file-access-list?dir=Programa+diario+base+de+casaci%C3%B3n+espa%C3%B1ol&parents%5B0%5D=%2F&parents%5B1%5D=Mercado+Diario&parents%5B2%5D=Programas&realdir=pdbc
accessed_at: 2026-09-03
language: English web page
relevant_pages: web §§49-70 (monthly PDBC archive listing, archive names, sizes and changed timestamps)
relevant_sections: monthly `pdbc_202501.zip` through `pdbc_202512.zip` entries are listed; each entry has a changed timestamp, demonstrating a public archive listing and not a guaranteed immutable snapshot
notes: The listing is direct evidence for the sampled PDBC programme category only. It does not prove that every OMIE category, balancing file, private offer or project-level record is publicly available or complete for 2025.
historical_2025: PDBC monthly archive entries visible at access; category-wide completeness and historical replacement/version lineage remain open
version_relation: operational archive listing supporting S-SP-OMIE-PUBFILES-2025 and S-SP-OMIE-FILES-2026
evidence_status: confirmed listing sample; full coverage/revision open
```

### S-ENTSOE-TP-MOP-2025（confirmed platform retention/access/version boundary; item-level applicability open）

```yaml
source_id: S-ENTSOE-TP-MOP-2025
institution: ENTSO-E
title: Central Information Transparency Platform — Manual of Procedures (URL package V2r1; body pages labelled V2r0)
document_type: ENTSO-E Transparency Platform manual
publication_date: URL/package is V2r1, while the body pages retrieved show V2r0 labels; no single publication date shown
effective_from: version-dependent; the current MoP page states later v3.x revisions and requires the most recent applicable version
effective_to: superseded for applicable items by later MoP revisions
url: https://www.entsoe.eu/Documents/MC%20documents/Transparency%20Platform/MOP/00_ENTSO-E%20Manual%20of%20Procedures_V2R1.pdf
accessed_at: 2026-09-03
language: English PDF
relevant_pages: PDF pp.5 (at-least-five-year historical availability); pp.17-19 (consumer registration, API/data-repository access, versions and downloads); pp.14-16 (provider replacement version and retained versions)
relevant_sections: §1.4 historical data; §§7.1-7.6 data-consumer access, XML/XLSX/CSV download, REST API and data repository; §6.8 replacement XML with incremented version and retained submitted versions
notes: The five-year and retained-version statements are platform-level statements in the consulted PDF. Its cover/contents and body carry mixed V2r1/V2r0 labels, so the exact package version is itself a version-control caveat; latest MoP v3.x and item-level implementation must be checked before treating the statements as a guarantee for a Spanish balancing dataset.
historical_2025: platform policy indicates at least five years in the consulted version; Spain-specific item coverage and 2025 balancing history remain open
version_relation: version/access layer; current MoP roadmap is separately described by S-ENTSOE-MOP-ROADMAP-2026
evidence_status: confirmed text in consulted PDF; package-version and dataset-specific applicability open
```

### S-ENTSOE-TP-QUERY-2025（confirmed API response/time/error behavior; data-item mapping open）

```yaml
source_id: S-ENTSOE-TP-QUERY-2025
institution: ENTSO-E Transparency Platform
title: Query Response
document_type: official Transparency Platform API help article
publication_date: 2025-12-09 (updated)
effective_from: article current at access; API behavior can change with platform revisions
effective_to: unknown
url: https://transparencyplatform.zendesk.com/hc/en-us/articles/15727773247124-Query-Response
accessed_at: 2026-09-03
language: English
relevant_pages: web §§23-50 (response time, partial/exact matching, daily response behavior, HTTP codes)
relevant_sections: response timestamps always UTC; some daily/price articles return complete local publication days; responses may be partial or exact; 429 for more than 400 requests/minute per IP, 401 for missing/invalid token and 200/999 for no matching data
notes: This is a first-party operational/API explanation. It does not map a Spanish project to an EIC, UP/UF, OMIE UO or private settlement account, and does not prove a historical dataset is complete.
historical_2025: response behavior documented before/within the 2025 historical period; item-level historical retention and Spanish balancing data availability remain open
version_relation: query behavior supports S-ENTSOE-TP-MOP-2025 and S-ENTSOE-EDI-2024
evidence_status: confirmed operational behavior; Spanish item mapping/coverage open
```

### S-ENTSOE-EDI-LIB-2026（confirmed schema/code-list update boundary; historical message mapping open）

```yaml
source_id: S-ENTSOE-EDI-LIB-2026
institution: ENTSO-E
title: Electronic Data Interchange (EDI) Library
document_type: official EDI library and implementation-guide catalogue
publication_date: continuously maintained; page records code-list updates through 2026-06-10
effective_from: each guide/schema/code-list version has its own applicability
effective_to: later versions may supersede; older versions remain process-dependent
url: https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/
accessed_at: 2026-09-03
language: English
relevant_pages: web EDI library page; last-updates entries for code list versions 93 (2025-12-02), 94 (2026-03-02) and 95 (2026-06-10); Electricity Balancing Processes catalogue
relevant_sections: balancing implementation-guide catalogue for TERRE/PICASSO/MARI/resource planning; code-list version notices; schema/XSD entry points
notes: Confirms that platform code lists and schemas are versioned. It does not prove that the same version was used by every Spanish file in 2025 or provide a Spanish project-level mRID/EIC/UO/UP/UF crosswalk.
historical_2025: version 93 is a post-2025-12-02 code-list boundary; exact 2025 message/schema version by dataset remains open
version_relation: current EDI catalogue supporting S-ENTSOE-EDI-2024; no post-baseline version is backfilled into 2025
evidence_status: confirmed version catalogue; historical message mapping open
```

### S-ENTSOE-MOP-ROADMAP-2026（confirmed current roadmap boundary; no 2025 backfill）

```yaml
source_id: S-ENTSOE-MOP-ROADMAP-2026
institution: ENTSO-E
title: Manual of Procedures (MoP) and implementation roadmap
document_type: official ENTSO-E MoP revision and roadmap page
publication_date: continuously maintained; page accessed after 2026-08-11
effective_from: applicable MoP version is item/area dependent; page states most recent version governs where no dedicated tab exists
effective_to: future revisions may supersede
url: https://www.entsoe.eu/data/transparency-platform/mop/
accessed_at: 2026-09-03
language: English
relevant_pages: web §§118-143 (MoP purpose and revision history, including v3.1-v3.5 and implementation roadmap)
relevant_sections: MoP is technical guidance for data providers/consumers; v3.4 adds Energy Storage production type; v3.5 adds further publication changes; roadmap identifies implementation progress by data publication and area
notes: Current roadmap is used only to identify post-baseline interface/version risk. It cannot retroactively establish a 2025 field, storage category or Spanish data availability without the item-level applicable version.
historical_2025: no backfill; 2025 field applicability remains version-by-date open
version_relation: current roadmap for S-ENTSOE-TP-MOP-2025 and S-ENTSOE-EDI-LIB-2026
evidence_status: confirmed current roadmap; historical applicability open
```

### S-SP-OMIE-PUBLIC-FORMAT-2024（confirmed public CURVA_PBC country codes）

```yaml
source_id: S-SP-OMIE-PUBLIC-FORMAT-2024
institution: OMIE
title: Modelo de ficheros para la distribución pública de información del mercado de electricidad, versión 1.35
document_type: OMIE public-information file format specification
publication_date: 2024-06 (version shown in document)
effective_from: format-version dependent; sampled file schema must be checked against issue date
effective_to: later format versions may supersede
url: https://www.omie.es/sites/default/files/2024-06/Formato_ficheros_inf_pub_135.pdf
accessed_at: 2026-09-04
language: Spanish PDF
relevant_pages: PDF pp.23-25 (§6.4, daily market aggregated offer/demand curves)
relevant_sections: §6.4 CURVA_PBC; country-code and offer-status field definitions
notes: Defines País codes `MI` (Mibel), `ES` (España) and `PT` (Portugal), plus Hora, Fecha, Tipo Oferta, energy, price and offered/cashed flags. In market separation, local ES/PT curves may appear; the sampled UOF file therefore requires a market-state-aware filter rather than a silent `Pais=ES` filter.
historical_2025: format evidence supports the 2025 sample; the monthly UOF package remains the operative file-level evidence
version_relation: schema evidence supporting S-SP-OMIE-FORMATS-2025 and S-SP-OMIE-UOF-ARCHIVE-2026
evidence_status: confirmed field and country-code definitions; technology mapping remains open
```

### S-SP-OMIE-UNIT-LIST-2026（confirmed current UO technology field; historical applicability open）

```yaml
source_id: S-SP-OMIE-UNIT-LIST-2026
institution: OMIE
title: LISTADO DE UNIDADES OFERTANTES VIGENTES
document_type: OMIE current offering-unit list
publication_date: 2026-09-04 (Fecha Emisión shown in PDF)
effective_from: current list at access; no historical 2025 validity asserted
effective_to: unknown; later current lists may supersede
url: https://www.omie.es/sites/default/files/dados/listados/LISTA_UNIDADES.PDF
accessed_at: 2026-09-04
language: Spanish PDF
relevant_pages: PDF pp.1-78; columns CODIGO, TIPO UNIDAD, ZONA/FRONTERA and TECNOLOGÍA
relevant_sections: LISTADO DE UNIDADES OFERTANTES VIGENTES
notes: The current list supplies explicit technology text for many UO codes and was used only to create a candidate crosswalk for the 2025 sample. Its current-date status does not prove a historical 2025 unit mapping, retirement status, rename or bid-type relationship.
historical_2025: historical applicability open
version_relation: candidate crosswalk layer for ES-SP-PRICE-01; must not override historical evidence
evidence_status: confirmed current field and candidate extraction; historical mapping open
```

### S-SP-OMIE-UNIT-LIST-ARCHIVE-2025-09（auxiliary archived snapshot; not final historical ground truth）

```yaml
source_id: S-SP-OMIE-UNIT-LIST-ARCHIVE-2025-09
institution: OMIE (original publisher); Internet Archive (archival host)
title: LISTADO DE UNIDADES OFERTANTES VIGENTES (archived OMIE PDF)
document_type: Internet Archive capture of OMIE official unit list
publication_date: 2025-09-10 (Fecha Emisión in PDF); captured 2025-09-11
effective_from: unknown; snapshot is not a date-effective historical register
effective_to: unknown
url: https://web.archive.org/web/20250911035831id_/https://www.omie.es/sites/default/files/dados/listados/LISTA_UNIDADES.PDF
original_url: https://www.omie.es/sites/default/files/dados/listados/LISTA_UNIDADES.PDF
accessed_at: 2026-09-05
language: Spanish PDF
relevant_pages: PDF pp.1-69; columns CODIGO, TIPO UNIDAD, ZONA/FRONTERA and TECNOLOGÍA
relevant_sections: LISTADO DE UNIDADES OFERTANTES VIGENTES
notes: Auxiliary evidence only. The snapshot is closer to the 2025-01—03 sample than the current list and was used for cross-snapshot comparison. It does not establish that each label applied on every 2025 delivery date; OMIE direct historical export remains required.
historical_2025: auxiliary only; historical applicability open
version_relation: comparison layer for ES-SP-PRICE-01; must not override direct historical evidence
evidence_status: confirmed archived PDF and hash; historical mapping remains open
```
