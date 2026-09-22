# ES-03 西班牙平衡能量、激活与欧洲平台

> 对象：独立电化学储能；历史期 2025-01-01—2025-12-31；规则基准日 2026-08-11。范围为平衡能量报价、激活、欧洲平台、本地 fallback、未交付接口和必要计量接口。容量费沿用 ES-02；完整不平衡价格公式、单/双价、更正结算留 ES-05。访问日期均为 2026-08-11。

规则事实来自 BOE/CNMC、REE、ENTSO-E、ACER 一方资料；解释和待确认项不作为模型参数。每项 claim 的 source ID、机构、日期、生效期、URL 和定位均列在证据列，完整来源登记见 [sources.md](sources.md)。

## 1. aFRR / regulación secundaria 与 PICASSO

| Claim ID | 规则事实 | 证据（source ID；机构/文件；日期/生效；URL；定位） | 解释/储能边界 | 状态 |
|---|---|---|---|---|
| ES03-aFRR-001 | P.O.7.2同时覆盖本地aFRR能量市场、PICASSO欧洲激活、IGCC/IN以及PICASSO/通信故障的本地后备。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06发布，按SRS/PICASSO连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §1，PDF pp.99-100。 | aFRR容量市场和能量激活分层；PICASSO价不是容量费。 | `confirmed`/高 |
| ES03-aFRR-002 | aFRR容量中标者须在对应QH/方向提交至少等量能量支持；**D-1 12:00起开放能量报价接收**，D-1 20:00前形成首版`oferta de respaldo`，之后持续更新，交付前25 min为当前更新接口。12:00开放时间与20:00首版备用报价截止时间是两个不同节点。 | S-CNMC-2024-MP；CNMC，2024-06-06发布、2024-07-06生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.10(2)(c)；S-CNMC-2024-11535-PO；P.O.7.2 Annex I §2.2，PDF pp.113-115；S-CNMC-2025-QH；CNMC/BOE，2025-03-17发布；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.1 §13.3，HTML §§1362-1395。 | 对储能是能量可用性义务；SOC、恢复和未交付系数未确认。 | `confirmed`义务/高；公式ES-05 |
| ES03-aFRR-003 | aFRR能量产品自动、程序化激活，FAT 5 min；最小/粒度1 MW、最大9999 MW；交付15 min；连续激活间隔至少4 s；价格分辨率0.01 €/MWh；每方向最多25块；价格仅受技术字段限制。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06发布/连接条款生效；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 Annex I §2.1，PDF pp.113-115。 | €/MWh是能量价，不是aFRR容量€/MW；储能产品测试另留ES-04。 | `confirmed`/高 |
| ES03-aFRR-004 | 报价块含MW、€/MWh、上/下方向、可分/不可分；接收时验证资格、时域、价格、量、粒度、块数和PM–OS格式，失败可拒绝全部或部分。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 Annex I §§2.1-2.2，PDF pp.113-115。 | PM–OS保密字段不由公开文本外推。 | `confirmed`字段/高；保密字段待确认 |
| ES03-aFRR-005 | 本地算法按LMOL从最具竞争力到最不具竞争力逐周期分配：上调方向先按负价绝对值由高到低、再按正价从低到高，下调方向先按正价从高到低、再按负价绝对值由低到高；同价块按规模同时按比例激活，末块拆分至Ptarget，最后块为本地边际价。PICASSO连接后分配仍用本地算法但边际价由PICASSO确定；价外接受块可按其报价价，最近激活后5 min取对供应商更有利价格。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §9.2，PDF pp.105-107；Annex III §7，PDF pp.122-124。 | 这是激活顺序/价格形成事实；完整能量结算公式留ES-05。 | `confirmed`原则/高 |
| ES03-aFRR-006 | PICASSO连接前本地激活，连接后PICASSO主路径；相关平台或本地SRS路径不可用时按P.O.7.2使用本地算法/SRS后备；RCP是针对SRS一般技术/安全故障的单独后备，并须由OS通知切换。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §§1、8.2-8.4、Annex IV；S-ACER-aFRR-IF；ACER Decisions 02/2020、15/2022、08/2024，https://www.acer.europa.eu/electricity/implementation-monitoring/eb，web §§118-133；S-REE-PLATFORMS-2026；REE现行页面，https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance，web §§44-47（PICASSO Jun-2025）。 | RCP不是对所有平台或通信异常的概括性fallback；fallback不豁免储能预认证，逐日切换和通信冗余待确认。 | `confirmed`路径/高 |
| ES03-aFRR-007 | IGCC/IN、PICASSO和OS在每个控制周期协调；IN可对相反方向的aFRR需求进行TSO–TSO净额，随后由平台优化并形成激活结果。公开材料不支持把该过程简化为固定的“IN先于aFRR激活”顺序；OS实时提交西班牙需求和法葡ATC。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §§8.1、8.3.1-8.3.4，PDF pp.107-109；S-ACER-IN-IF；ACER Decisions 13/2020、16/2022，https://www.acer.europa.eu/electricity/implementation-monitoring/eb，web §§135-147。 | IN是TSO–TSO netting，不是储能投标产品；不在模型中设定固定的跨平台先后顺序。 | `confirmed`接口/高 |
| ES03-aFRR-008 | REE页面记录IGCC于2020-10、MARI于2024-12、PICASSO于2025-06接入；仅给月份，未给逐日切换。 | S-REE-PLATFORMS-2026；REE现行页面（访问2026-08-11）；https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance；web §§44-47。 | 2025序列只能按月份版本边界并保留逐日切点待确认。 | `confirmed`月份/中高 |
| ES03-aFRR-009 | OS用实时信号、PTR/PTRb'和能量接受量监测交付；Art.14、P.O.7.2/P.O.14.4承接未交付、资格暂停和支付。 | S-CNMC-2024-MP；CNMC/BOE，2024-06-06/2024-07-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Arts.9、14；S-CNMC-2024-11535-PO，P.O.7.2 Annex II-III，https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf，PDF pp.103-111。 | 只记录接口，不写系数/宽限期/罚则公式。 | `confirmed`接口/高 |

## 2. mFRR / regulación terciaria 与 MARI

| Claim ID | 规则事实 | 证据（source ID；机构/文件；日期/生效；URL；定位） | 解释/储能边界 | 状态 |
|---|---|---|---|---|
| ES03-mFRR-001 | P.O.7.3先本地算法激活；OS网页通知MARI连接日后由MARI交换；平台故障或本地激活时用本地算法后备并通知参与者。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06/MARI连接条款；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§1、4，PDF pp.155-156；S-ACER-mFRR-IF；ACER Decisions 03/2020、14/2022，https://www.acer.europa.eu/electricity/implementation-monitoring/eb，web §§105-116。 | 可用备用不是容量费。 | `confirmed`/高 |
| ES03-mFRR-002 | PM每日23:00前提交次日全时域可用上/下tertiary reserve；计划/可用性变化时持续更新，至QH开始前25 min；可用备用报价强制。 | S-CNMC-2025-QH；CNMC/BOE，2025-03-17；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.1 §13.2，HTML §§1362-1395/PDF pp.35882-35884；S-CNMC-2024-11535-PO P.O.7.3 §§8.1-8.2，https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf，PDF pp.157-158。 | reserve MW是可激活功率，不是容量中标量。 | `confirmed`/高 |
| ES03-mFRR-003 | mFRR手动激活，可程序化或直接；FAT 12.5 min；最小/粒度1 MW、最大9999 MW；价格分辨率0.01 €/MWh。对同时参与aFRR/secondary的供应商，标准交付范围为5–30 min，程序化激活5 min、直接激活最长20 min；对mFRR-only供应商，程序化交付为15 min、直接激活最长约29 min，具体以P.O.7.3产品表为准。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06/MARI连接条款；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §7、Annex I §§1-2，PDF pp.156-159。 | 5–30 min及程序化5 min/直接20 min不能外推为所有mFRR资源的统一参数；储能持续时间应按参与配置和激活类型分别建档。 | `confirmed`/高 |
| ES03-mFRR-004 | mFRR块含MW、€/MWh、方向、直接/程序化、可分/不可分及跨期条件；MARI结果对同时参加aFRR的供应商最晚峰值点前12.5 min、其他供应商供能前7.5 min通知。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §8.2、§9.4、Annex I，PDF pp.157-160。 | 通知时点不是设备成功保证；储能遥测/SOC另留ES-04。 | `confirmed`/高 |
| ES03-mFRR-005 | MARI匹配后跨境程序firm；平台无结果时由其他机制覆盖；紧急、无报价或不可控时OS可异常调度。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 §§9.4-9.5、10，PDF pp.159-160。 | 异常调度不是可预先报价储能产品。 | `confirmed`接口/高 |
| ES03-mFRR-006 | mFRR能量价单位€/MWh；P.O.14.4承接权利/支付和未履约结算。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 Annex I、P.O.14.4，PDF pp.157-160、195-196；S-EBGL-2017；欧盟委员会，2017-11-23生效2017-12-18；https://eur-lex.europa.eu/eli/reg/2017/2195；Arts.20、29-30。 | 不提前写平台边际价、单/双价或不平衡公式。 | `confirmed`单位/接口；公式ES-05 |
| ES03-mFRR-007 | 本地mFRR算法建立上调/下调分开的有效报价阶梯：上调按价格从低到高、下调按价格从高到低；同价先完全可分块，再按最小功率/块类型和文件到达顺序排序。程序化激活可用程序化及直接报价；直接激活排除程序化报价，并在同向连续激活时从上次切点继续。程序化边际价为上调已分配最高价、下调已分配最低价；直接激活价格先临时、待该QH所有分配完成后确定。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.3 Annex II §§1-4，PDF pp.164-166。 | 该顺序是本地fallback/本地激活规则；MARI跨境共同排序由mFRR-IF及平台结果控制，不在此处外推。 | `confirmed`本地/高；MARI共同排序待平台字段 |

## 3. RR / TERRE与2026替代边界

| Claim ID | 规则事实 | 证据（source ID；机构/文件；日期/生效；URL；定位） | 解释/储能边界 | 状态 |
|---|---|---|---|---|
| ES03-RR-001 | 2025 P.O.3.3为RR平衡能量激活/交换；TERRE使用至连续日内市场96 closures；24 RR horizons/gates与96 closures不同。 | S-CNMC-2025-QH；CNMC/BOE，2025-03-17；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.1 §13.1、P.O.3.3，PDF pp.26-27、123-127；S-ACER-RR-IF；ACER/RRIF 2023修订；https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/MARKET-CODES/ELECTRICITY-BALANCING/02%20RR%20IF/Action-3a-RR-IF-Amended-proposal-approved.pdf；PDF pp.1-2、12-13。 | 96不是容量采购量；2025只能记录RR能量层。 | `confirmed`/高 |
| ES03-RR-002 | RR标准产品程序化、手动激活；准备/爬坡0–30 min、FAT30 min；最小1 MW；交付15–60 min；报价MW、€/MWh、上/下方向、类型和复杂条件；价格分辨率0.01 €/MWh。 | S-CNMC-2025-QH；CNMC/BOE，2025-03-17；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.3 §6、Annex I §1-2，PDF pp.124-127。 | RR非容量市场；储能专门资格/SOC未确认。 | `confirmed`产品/高 |
| ES03-RR-003 | RR报价自D-1 12:00接收；H-55′为eSIOS截止；每UP、每方向每小时最多40块；报价须在开放时域且不得重复同价块；送TERRE前至少5 min按PHFC/不可用信息校验。 | S-CNMC-2025-QH；CNMC/BOE，2025-03-17；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.3 Annex I §§2.1-2.2，PDF pp.126-127。 | PM–OS仍控制价格边界和更细验证。 | `confirmed`/高 |
| ES03-RR-004 | TERRE/RRIF执行跨境激活；上/下方向按RR价格规则结算，控制流、平台舍入和保障价格有P.O.3.3/P.O.14.4接口。 | S-CNMC-2025-QH；CNMC/BOE，2025-03-17；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.3 §10、Annex I；S-ACER-RR-IF；ACER 2023 RRIF；https://www.acer.europa.eu/sites/default/files/documents/en/Electricity/MARKET-CODES/ELECTRICITY-BALANCING/02%20RR%20IF/Action-3a-RR-IF-Amended-proposal-approved.pdf；PDF pp.12-13。 | 只保留接口，具体边际/报价价和未交付金额留ES-05。 | `confirmed`接口/高 |
| ES03-RR-005 | ENTSO-E记录REE/REN在2025-12-30约09:00–10:00 MTU停止TERRE/LIBRA，2026-01-01起为former member，平台计划2026-03关闭。 | S-ENTSOE-TERRE-2026；ENTSO-E，页面更新至2026；https://www.entsoe.eu/network_codes/eb/terre/；web §§127-151、208-229。 | 2025序列须截断于该MTU。 | `confirmed`切点/高 |
| ES03-RR-006 | 截至2026-08-11未找到REE/BOE对TERRE停止后RR替代平台、本地产品或fallback的有效P.O.闭环；2026交易/激活/价格/储能资格不得外推。 | S-ENTSOE-TERRE-2026；ENTSO-E，https://www.entsoe.eu/network_codes/eb/terre/；S-REE-PLATFORMS-2026；REE现行页，https://www.ree.es/es/clientes/comercializador/participacion-en-servicios-de-balance；S-CNMC-2025-QH P.O.3.3 §13.1，https://www.boe.es/eli/es/res/2025/03/06/(12)。 | 这是证据范围结论，列ES-01-Q02/Q03 `open-critical`。 | `unresolved`/高风险 |

## 4. IN / IGCC（TSO–TSO，非储能产品）

| Claim ID | 规则事实 | 证据（source ID；机构/文件；日期/生效；URL；定位） | 解释/储能边界 | 状态 |
|---|---|---|---|---|
| ES03-IN-001 | IGCC执行IN，在每个实时控制周期对西班牙控制块与其他控制块的相反aFRR需求进行TSO–TSO净额；其与PICASSO优化及aFRR激活的具体先后由P.O.7.2和平台流程共同决定，不设固定的跨平台顺序。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §8.1-8.2，PDF pp.107-108；S-ACER-IN-IF；ACER Decisions 13/2020、16/2022；https://www.acer.europa.eu/electricity/implementation-monitoring/eb；web §§135-147。 | 不接受BSP/独立储能直接报价；不在模型中设定固定跨平台顺序。 | `confirmed`接口/高 |
| ES03-IN-002 | OS实时提供法葡ATC和西班牙aFRR需求；IGCC返回校正信号进入主调节器，PICASSO据此优化/激活。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §8.3.1-8.3.4，PDF pp.108-109。 | ATC影响可激活量但不是储能申报字段或独立收入。 | `confirmed`/高 |
| ES03-IN-003 | IN/IGCC跨TSO财务净额和拥塞租金不属于BSP能量结算；本阶段只保留aFRR需求接口。 | S-CNMC-2024-MP；CNMC/BOE，2024-06-06/2024-07-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Art.13(3)、P.O.7.2 §8；S-ACER-IN-IF；https://www.acer.europa.eu/electricity/implementation-monitoring/eb。 | 储能收益模型不把IGCC净额当BSP价格。 | `confirmed`边界/高 |

## 5. fallback、未交付、计量与数据

| Claim ID | 规则事实 | 证据（source ID；机构/文件；日期/生效；URL；定位） | 解释/储能边界 | 状态 |
|---|---|---|---|---|
| ES03-FB-001 | aFRR/mFRR为欧洲平台主路径+本地算法/系统后备；aFRR另有SRS/RCP；mFRR无平台结果时由其他机制覆盖；RR仅确认TERRE至96 closures及2025-12-30停止。 | S-CNMC-2024-11535-PO；CNMC/BOE，2024-06-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §1/Annex III-IV、P.O.7.3 §4/§9.4；S-CNMC-2025-QH；https://www.boe.es/eli/es/res/2025/03/06/(12)；P.O.3.1 §13.1；S-ENTSOE-TERRE-2026；https://www.entsoe.eu/network_codes/eb/terre/。 | fallback不豁免资格/测试；RR 2026保持未决。 | `confirmed`aFRR/mFRR；RR `unresolved` |
| ES03-FB-002 | Art.14、P.O.7.2/7.3和P.O.14.4承接未交付、可用率、资格暂停及支付；具体系数、宽限期、恢复测试和罚则公式未提取。 | S-CNMC-2024-MP；CNMC/BOE，2024-06-06/2024-07-06；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；Arts.9、14；S-CNMC-2024-11535-PO；https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf；P.O.7.2 §9、P.O.7.3 §§10-12、P.O.14.4。 | 不把储能SOC不足简化为单一罚价；公式留ES-04/05。 | `confirmed`接口；公式未决 |
| ES03-FB-003 | MITECO决议使15分钟计量/程序接口自2025-05-01生效，P.O.10.x用于平衡验证和结算输入；时区、缺失值、修订流程待确认。 | S-MITECO-2025-ISP；MITECO，2025-04-02发布、2025-05-01生效；https://www.boe.es/eli/es/res/2025/03/28/(2)；HTML §§60-67、90-110及P.O.10.x附件。 | 计量分辨率不等于FAT；序列需保存单位和版本。 | `confirmed`分辨率/高；时区/修订待确认 |
| ES03-FB-004 | REE/eSIOS公开aFRR、mFRR、RR、IGCC/SEPE能量/价格类别；ENTSO-E EDI提供平台激活、报价和资源计划schema入口。 | S-REE-DATA-BAL-2026；REE/eSIOS持续更新页，访问2026-08-11；https://www.ree.es/es/datos/mercados/energia-gestion-desvios；S-ENTSOE-EDI-2024；ENTSO-E，2024 schema入口；https://www.entsoe.eu/publications/electronic-data-interchange-edi-library/；web §§321-330。 | API字段、CET/CEST、延迟、revisionNumber及TERRE归档留ES-06；不写data/raw。 | `provisional`数据入口 |

## 6. 2025—2026版本矩阵

| 平台 | 2025历史期 | 2026-08-11边界 | 储能建模边界 |
|---|---|---|---|
| aFRR/PICASSO | PICASSO接入月2025-06；此前本地，之后PICASSO主路径并保留fallback。 | 现行平台层仍有效，逐日切点和当前P.O.修订待核。 | 可用产品/FAT/报价字段；SOC、持续时间、未交付公式不定。 |
| mFRR/MARI | MARI接入月2024-12；2025为MARI主路径，本地算法后备。 | P.O.7.3/OS通知控制当前路径。 | 可用FAT12.5、交付和报价字段；不推导容量费。 |
| RR/TERRE | TERRE至2025-12-30约09:00–10:00 MTU；24 horizons、96 closures切点。 | TERRE已停止，替代平台/本地RR/fallback未确认。 | 仅切点前2025能量；2026全未决。 |
| IN/IGCC | IGCC自2020-10运行，2025为aFRR控制周期内的TSO–TSO netting接口。 | 仍是TSO–TSO接口；与PICASSO优化/激活的固定先后不在本阶段设定。 | 不作为储能直接收入。 |

## 7. 内容分层与交接

### 规则事实

aFRR：自动、FAT5、15-min、1 MW、€/MWh、D-1支持报价、PICASSO主路径及本地/SRS/RCP fallback。mFRR：手动、FAT12.5、1 MW、€/MWh；同时参与aFRR的供应商适用5–30 min/程序化5 min/直接20 min配置，mFRR-only供应商适用15 min程序化/约29 min直接配置；MARI主路径及local fallback。RR：手动程序化、FAT30、1 MW、15–60 min、24 horizons、D-1 12:00/H-55′/40块/0.01 €/MWh、TERRE于2025-12-30停止。IN/IGCC是TSO–TSO netting。15-min计量接口自2025-05-01生效。

### 研究解释

“reserve MW/available reserve”是能量激活可用功率字段，不是mFRR/RR容量费；平台主路径、fallback和储能产品资格是三层问题；2025 RR须按TERRE停止MTU截断，不能外推2026。

### 建模假设

本阶段不新增建模假设。SOC、持续时间、恢复、未交付公式、价格保护、时区、数据延迟和2026 RR替代保持 `unresolved`。

### 交接问题

1. PICASSO/MARI逐日连接日、故障通知和local算法切换；2. aFRR/mFRR未交付系数、资格恢复、SOC/持续供能；3. RR 2026替代平台/有效P.O./储能资格；4. RR PM–OS细粒度字段和撤回/修订；5. REE/eSIOS/ENTSO-E字段、CET/CEST、延迟、revisionNumber及2025 TERRE归档。
