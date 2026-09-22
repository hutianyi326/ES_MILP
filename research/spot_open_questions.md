# 西班牙现货市场未决问题（ES-SP）

> 研究基线：历史期 2025-01-01—2025-12-31；规则基准日 2026-08-11；对象为西班牙大陆竞价区的独立电化学储能。  
> 本清单与 `spot_market_structure.md` 配套。未决内容不得作为规则事实、模型参数或收益结论使用。

## 1. ES-SP-01 制度、主体与架构

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SP-01-Q01 | BOE-A-2026-17285 与 BOE-A-2026-17570 配套批准的 96 轮连续日内交易何时实际启用？对应的 OMIE 公告、市场规则版本和首个交付日是什么？ | 截至 2026-08-11 基准日，两份 BOE 文件仍只规定由 OMIE、REE、REN 约定并公开应用日；补充核验发现 OMIE Instruction 4/2026（2026-08-11）计划于 2026-09-22 维护后启动、首个交付日 2026-09-23。2026-09-03 时点尚未到达，实际完成上线和首个成功交付仍未确认（S-SP-BOE-2026-17285；S-SP-BOE-2026-17570；S-SP-OMIE-INST4-2026） | ES-SP-03/07 | partially-closed/open-critical |
| ES-SP-01-Q02 | 2025 年 OMIE 市场规则、P.O.3.1、P.O.9.1、P.O.14.4 的逐日版本边界如何建立？ | 已确认 2025-03-18 日内四分之一小时、2025-10-01 日前四分之一小时；程序文件日级切片未闭合（S-SP-OMIE-QH-ID-2025；S-SP-OMIE-MTU15-DA-2025；S-SP-BOE-2025-RULES） | ES-SP-03/04/07 | open-critical |
| ES-SP-01-Q03 | 西班牙—法国、 西班牙—葡萄牙在 SDAC/SIDC 解耦、部分解耦或 shadow auction 时的具体触发条件、平台和输出是什么？ | 已确认正常耦合架构；fallback 条件与数据输出未提取（S-EU-CACM-2015；S-SP-ENTSOE-MCSC-2026；S-SP-REE-INTERCONNECTIONS-2026） | ES-SP-03/07 | open |
| ES-SP-01-Q04 | JAO FTR option、SDAC/SIDC 隐式容量、商业计划交换和物理潮流的字段交叉映射如何建立？ | JAO/HAR 和 REE 页面分别确认长期权利与物理互联，但 EIC/corridor crosswalk 未闭合（S-SP-JAO-HAR-2024；S-SP-REE-INTERCONNECTIONS-2026） | ES-SP-07 | open |
| ES-SP-01-Q05 | 摩洛哥、安道尔边界是否有受监管的现货显式/双边交易通道，是否有可用于 2025 回溯的公开字段？ | REE 确认物理连接；未确认 SDAC/SIDC 接入和现货产品（S-SP-REE-INTERCONNECTIONS-2026） | ES-SP-02/03/07 | open |

## 2. ES-SP-04 独立储能主体与系统接口

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SP-04-Q01 | “储能设施持有人”成为 OMIE 市场主体时，实际需要哪一类行政注册、系统主体证明和并网文件？ | 已确认：市场规则要求储能设施持有人有效登记、取得系统主体资格、签署市场规则加入合同、提交 NIF/ACER/银行账户；REE 负责 UP 建立。具体项目注册表单、并网文件清单和 RAIPEE 登记路径仍需项目级核验（S-SP-BOE-2025-RULES；S-SP-PO31-2024-STORAGE；S-SP-OMIE-AGENT-2026） | ES-SP-04/07 | partially-closed/open |
| ES-SP-04-Q02 | 独立储能的市场主体、UP、UO、BRP、代表之间是一对一、可拆分还是可组合？ | 已确认：OMIE 注册关联层的 UO/UP 双射与 REE 计划申报层的多 UP 聚合并不矛盾；非水储能的送出与取电分别设置 UP，每个方向按 BRP+市场参与者各一 UP，UP 可含多个按安装划分的 UF。代表直接/间接对 UP 使用方式不同；具体项目账户仍需确认（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES） | ES-SP-04 | closed-for-general-rule; project-mapping-open |
| ES-SP-04-Q03 | 储能充电和放电是否必须使用不同 UO/UP、不同报价方向、不同计量点或不同 BRP？ | 已确认：非水独立储能送出与取电必须使用不同 UP；相应现货 UO 分别为销售/购买方向并与 UP 协调关联；储能点位的双向有功计量分别记录 Activa Saliente/Entrante。是否必须配置不同物理表计、不同 BRP 或不同代表，规则未要求一概拆分，需按项目配置确认（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES；S-MITECO-2025-ISP） | ES-SP-04 | closed-for-direction; metering/BRP-project-open |
| ES-SP-04-Q04 | OMIE 成交结果经 REE 技术可行性校核后，储能最终执行计划、偏差和结算使用哪些字段及哪个计划版本？ | 已确认计划链条和责任：OMIE 结果→PM 按 UP/UF 进行必要申报/分解→REE 发布 PDBF、PDVP、确认后的 PDVD、PHF/PHFC；独立储能测量按其 UP 汇总并进入 BRP 结算。具体消息字段、版本号、修订标志和 OMIE/REE 数据 crosswalk 留 ES-SP-07（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES Rules 35–36、58.4） | ES-SP-04/07 | partially-closed |
| ES-SP-04-Q05 | 独立储能是否需要分别办理 OMIE 市场保证金、REE 系统保证金、网络费用、税费和代表服务费用？ | 已确认：OMIE 市场交易保证金与 REE/OS 结算环节的付款保证金属于不同规则入口；代表间接模式由代表承担相应市场付款/保证金责任，直接模式由被代表主体承担。具体金额、网络费、税费和代表合同费用不由本阶段规则统一确定（S-SP-BOE-2025-RULES；S-SP-PO31-2024-STORAGE） | ES-SP-04/07 | partially-closed/open |
| ES-SP-04-Q06 | 储能与辅助服务同时参与时，现货成交计划、备用预留、激活、补能和偏差之间的正式接口是什么？ | 已有辅助服务研究确认部分接口；现货—调频耦合留 ES-SP-06（S-CNMC-2024-11535-PO；S-CNMC-2025-QH；S-MITECO-2025-ISP） | ES-SP-06 | open-critical |

## 3. ES-SP-02/03 日前和日内规则

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SP-02-Q01 | 2025 年日前市场订单类型、价格上下限、最小申报量、关门时间和出清参数按哪个版本逐日适用？ | 市场规则文件已登记，参数提取明确留 ES-SP-02（S-SP-BOE-2025-RULES；S-SP-OMIE-MTU15-DA-2025） | ES-SP-02 | open |
| ES-SP-02-Q02 | 日前市场的 2025-03-18 新报价类型与 2025-10-01 MTU15 切换对储能报价单位有何具体影响？ | 版本时间线确认；储能订单参数未研究（S-SP-OMIE-QH-ID-2025；S-SP-OMIE-MTU15-DA-2025） | ES-SP-02/04 | open |
| ES-SP-03-Q01 | 2025 年三场 IDA 的具体开启/关闭、交付范围、跨区容量和与连续交易的衔接如何逐场还原？ | 规则层具体日程留 ES-SP-03；逐日运行记录和版本字段由 ES-SP-07 回溯（S-SP-BOE-2024-IDAS；S-SP-ENTSOE-MCSC-2026；S-SP-OMIE-NEMO-2026） | ES-SP-03/07 | open |
| ES-SP-03-Q02 | 2025 年连续日内交易的产品、关闭时间、合同状态、交易价格和计划更新如何与 15 分钟边界对应？ | 规则层参数留 ES-SP-03；逐笔交易和计划字段由 ES-SP-07 核验（S-SP-BOE-2024-IDAS；S-SP-ENTSOE-MCSC-2026；S-SP-OMIE-NEMO-2026；S-SP-BOE-2025-RULES） | ES-SP-03/07 | open |
| ES-SP-03-Q03 | 日内成交后的计划是否在所有情形自动覆盖日前计划，还是受 UO/UP、PDVD、PHF/PHFC 和系统校核限制？ | 市场/系统计划接口确认；具体替代关系未闭合（S-SP-BOE-2025-RULES；S-SP-OMIE-NEMO-2026；S-SP-REE-ROLE-2026） | ES-SP-03/04 | open-critical |

## 4. ES-SP-05/06 后续机制研究

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SP-05-Q01 | 日前—日内价差、同日跨时段搬移、负价和连续市场流动性如何在机制层定义，且不引入未经核验的收益假设？ | 机制定义、买卖方向、IDA/连续市场差异和计划桥接已完成；2025 逐笔价格、成交量、订单状态和修订字段尚未逐项核验（S-SP-BOE-2025-RULES；S-SP-OMIE-NEMO-2026；S-SP-OMIE-QH-ID-2025；S-SP-OMIE-MTU15-DA-2025） | ES-SP-05/07 | open-critical（数据层） |
| ES-SP-05-Q02 | 现货交易中储能效率、SOC、循环寿命、费用和偏差成本应如何作为机制解释与建模假设分开记录？ | 机制层已明确这些不是统一现货规则参数；储能方向、双向计量、BRP 偏差责任和 15 分钟接口已确认，但数值和项目合同未确认（S-SP-PO31-2024-STORAGE；S-CNMC-2025-QH；S-MITECO-2025-ISP；S-SP-BOE-2025-RULES） | ES-SP-05/06/项目尽调 | open-critical（项目/模型层） |
| ES-SP-05-Q03 | 日内成交计划如何按具体储能 UO/UP/UF、BRP/代表和双向计量字段落地？ | 通用规则确认送出/取电方向、UO/UP、BRP 和 PHF/PHFC 计划链；项目级账户和数据 crosswalk 未闭合（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES；S-MITECO-2025-ISP） | ES-SP-04/07 | open-critical |
| ES-SP-05-Q04 | 2025 年 IDA 收单前暂停窗口、连续市场订单状态和异常解耦如何逐日还原？ | 2025 规则确认正常机制和订单状态；逐日暂停、fallback/decoupling 事件及其输出数据未验证（S-SP-BOE-2025-RULES；S-SP-OMIE-NEMO-2026；S-SP-OMIE-MARKET-2026） | ES-SP-03/07 | open |
| ES-SP-05-Q05 | 2026-08-11 时 96 轮连续交易修改的实际应用日和新时序是什么？ | 基准日结论仍是“应用日未锁定”；补充核验的 OMIE Instruction 4/2026 将计划切换日设为 2026-09-22、首个交付日设为 2026-09-23，并规定维护窗口、默认组合分解和 IDA3 过渡。由于 2026-09-03 尚未发生，实际 go-live/首日结果仍待确认；不得回填 2025（S-SP-BOE-2026-17285；S-SP-BOE-2026-17570；S-SP-OMIE-INST4-2026） | ES-SP-03/07 | partially-closed/open-critical |
| ES-SP-06-Q01 | aFRR/mFRR/RR 激活如何改变现货计划、BRP 偏差和储能计量方向？ | 辅助服务研究已确认部分规则；联合接口待交叉复核（S-CNMC-2024-11535-PO；S-CNMC-2025-QH；S-MITECO-2025-ISP；S-REE-GUIDE-2024） | ES-SP-06 | open-critical |
| ES-SP-06-Q02 | 现货成交功率、aFRR 预留功率和 mFRR/RR 可用功率之间是否存在正式的同一 UP/不同 UP 约束？ | 尚无完整储能专用规则证据（S-CNMC-2024-11535-PO；S-CNMC-2025-QH；S-MITECO-2025-ISP） | ES-SP-06 | open-critical |
| ES-SP-06-Q03 | 2026 年 RR/TERRE 退出后的替代机制如何影响现货—平衡耦合？ | TERRE/LIBRA 在 2025-12-30 10:00 CET 停止，REE/REN 自 2026-01-01 为 former members；BOE-17285 使 P.O.3.3 失效，但已核验官方资料尚未命名新的西班牙 RR 产品或替代结算/激活路径。96 轮是连续日内市场修订，不是已确认的 RR 替代（S-ENTSOE-TERRE-2026；S-SP-BOE-2026-17285；S-SP-BOE-2026-17570；S-SP-REE-BALANCE-2026） | ES-SP-06/07 | open-critical |

## 5. 数据与证据问题

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SP-07-Q01 | OMIE 的日前价格、成交量、订单曲线、IDA片段和连续交易记录的历史 API/文件是否完整覆盖 2025？ | 官方入口存在，历史覆盖和修订策略未逐项验证（S-SP-OMIE-NEMO-2026；S-SP-OMIE-AGENT-2026） | ES-SP-07 | open-critical |
| ES-SP-07-Q02 | OMIE、REE、eSIOS 和 ENTSO-E 的时区、DST、MTU、单位、币种和发布时间字段如何逐项统一？ | 入口已登记，字段字典未完成（S-SP-OMIE-NEMO-2026；S-SP-OMIE-AGENT-2026；S-SP-REE-ROLE-2026；S-REE-REData-API-2026；S-eSIOS-API-IND-2026；S-ENTSOE-EDI-2024） | ES-SP-07 | open |
| ES-SP-07-Q03 | OMIE 成交结果、REE 计划、商业交换、物理潮流、平衡激活和不平衡价格能否通过 mRID/EIC/单位代码关联？ | 各方数据入口分散；crosswalk 未完成（S-SP-OMIE-NEMO-2026；S-SP-REE-ROLE-2026；S-REE-REData-API-2026；S-ENTSOE-EDI-2024） | ES-SP-07 | open-critical |
| ES-SP-07-Q04 | 2025 年规则变化和回溯数据的修订/重发布是否有版本号、revisionNumber、created/published 时间和更正标志？ | 市场规则规定发布和更正机制；数据层字段待验证（S-SP-OMIE-NEMO-2026；S-SP-OMIE-AGENT-2026；S-ENTSOE-EDI-2024） | ES-SP-07 | open |
| ES-SP-07-Q05 | 决策时可获得的日前/日内数据与事后结算数据如何隔离保存，避免回测使用未来信息？ | 研究原则已确定；具体文件清单待 ES-SP-07（S-REE-REData-API-2026；S-eSIOS-API-IND-2026；S-SP-OMIE-NEMO-2026） | ES-SP-07 | open |
| ES-SP-07-Q06 | OMIE 日前、IDA、连续日内公开文件是否对每个 2025 交付日完整留存？文件缺失、停牌、解耦、撤单和后续更正如何编码？ | 入口和最近六年滚动声明已确认；逐文件抽样和历史下载尚未执行（S-SP-OMIE-FILES-2026；S-SP-OMIE-FORMATS-2024） | ES-SP-07 | open-critical |
| ES-SP-07-Q07 | OMIE 的 issued_at、data_date、版本/更正字段能否区分实时可知值和后来重发布值？ | 文件头有发行时间/数据日期；revisionNumber/更正标志未在格式说明中确认（S-SP-OMIE-FORMATS-2024） | ES-SP-07 | open-critical |
| ES-SP-07-Q08 | REE/eSIOS 各个平衡/不平衡 indicator ID、单位、15分钟/小时分辨率、时区、刷新时滞、API key/配额和 2025 覆盖是什么？ | API 路由、日期过滤和 token 入口已确认；逐指标元数据未闭合（S-REE-ESIOS-API-2026；S-REE-REData-API-2026） | ES-SP-07 | open-critical |
| ES-SP-07-Q09 | REE 公开计划/激活/计量文件与 BRP 私有结算 ZIP 的字段、版本号、修订标志如何一一映射？ | 规则链和私有边界已确认；公开文件与项目账户 crosswalk 未确认（S-REE-LIQ-ACCESS-2026；S-REE-LIQ-GUIDE-2024；S-SP-BOE-2025-RULES） | ES-SP-07 | open-critical |
| ES-SP-07-Q10 | ENTSO-E Spain bidding-zone/EIC、OMIE zone、REE UP/UF 和 platform mRID 是否有官方交叉表？ | ENTSO-E 数据项/API 入口已确认；跨机构代码映射未闭合（S-ENTSOE-TP-API-2026；S-SP-BOE-2025-RULES；S-SP-PO31-2024-STORAGE） | ES-SP-07 | open-critical |
| ES-SP-07-Q11 | CET/CEST 的 DST 重复/缺失时段、UTC offset 与 OMIE H/period、REE QH/eSIOS datetime 如何统一？ | 官方入口分别支持 CET/CEST、UTC 或本地 datetime；指标级行为未逐项验证（S-SP-OMIE-FORMATS-2024；S-ENTSOE-TP-API-2026；S-REE-REData-API-2026） | ES-SP-07 | open |
| ES-SP-07-Q12 | 2025 MARI/PICASSO 的具体接入日、首个有效 MTU、fallback/重发布文件如何识别？ | REE 只确认 2024-12/2025-06 月份边界；精确日和数据文件 ID 未确认（S-REE-PLATFORMS-2026） | ES-SP-07 | open-critical |
| ES-SP-07-Q13 | 2025-12-30 TERRE 最后 MTU 的 REE/eSIOS 归档标识、保留期和 2026 替代数据入口是什么？ | ENTSO-E 停止时段已确认；归档和替代机制未闭合（S-ENTSOE-TERRE-2026；S-REE-PLATFORMS-2026） | ES-SP-07 | open-critical |
| ES-SP-07-Q14 | OMIE 90天报价保密期是否同样适用于 IDA/连续逐笔订单，历史文件的撤单/修订如何表示？ | 日前报价文件90天规则已确认；IDAs/连续市场适用范围 open（S-SP-OMIE-FORMATS-2024；S-SP-OMIE-FILES-2026） | ES-SP-07 | open |
| ES-SP-07-Q15 | M+1计量/BRP结算等事后数据是否被错误地用于决策时点回测？ | 项目原则要求分层；具体文件级时间戳和访问权限仍需核验（S-MITECO-2025-ISP；S-REE-LIQ-ACCESS-2026；S-SP-OMIE-FORMATS-2024） | ES-SP-07 | open-critical |

## 5A. ES-SUP-01 FCR/SRAD 独立储能资格与预认证

本节承接 `supplemental_fcr_srad_eligibility.md`。以下问题均保持 `open-critical`；在官方规则、REE服务文件或项目接口文件闭合前，不得将独立储能可直接参与 FCR/SRAD 写入模型或收益结论。

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SUP-01-Q01 | 独立非水储能能否以自身 UP/UF 直接申请 FCR/一次调频 BSP 资格和 OS habilitación？ | S-CNMC-2024-MP 将储能持有人列为潜在 BSP，但未在已核验的 P.O.1.5/P.O.3.8 中确认独立储能的完整申请路径；ENTSO-E 当前 FCR Cooperation 页面不列西班牙。不得据此推断允许或禁止。 | ES-SUP-01/ES-SP-06 | open-critical |
| ES-SUP-01-Q02 | 西班牙本地 FCR 采购、容量/能量报价和补偿机制是否存在，以及与欧洲 FCR Cooperation 的关系是什么？ | S-ENTSOE-FCR-COOP-2026 当前成员清单不含西班牙；S-CNMC-2024-MP 明确二次调频备用市场，但未闭合 FCR 本地采购与支付。 | ES-SUP-01/ES-SP-06 | open-critical |
| ES-SUP-01-Q03 | 独立储能如申请 FCR，适用 P.O.3.8 哪一套测试、P.O.1.5 哪些参数及聚合比例例外？ | S-CNMC-2024-6215-PO38 核验到二次/三次/RR 测试框架，未找到 FCR/储能专用测试通道；S-CNMC-2024-MP 的资格条件为原则性要求。 | ES-SUP-01 | open-critical |
| ES-SUP-01-Q04 | FCR 的下垂、死区、响应时间、持续时间、SOC恢复和双向对称要求如何落实到储能控制器？ | S-CNMC-2024-MP/P.O.1.5 给出系统/发电机侧一次响应参数；独立储能适用参数与测试判据未确认。 | ES-SUP-01/ES-SP-06 | open-critical |
| ES-SUP-01-Q05 | FCR 储能的实时遥测、计量、UP/UF/UO、PM/BSP/BRP 接口和双向能量结算字段是什么？ | S-CNMC-2024-MP 规定 BSP、BRP、控制中心、实时数据和储能双向计量的原则；项目级字段、方向和消息交叉表未闭合。 | ES-SUP-01/ES-SP-04/07 | open-critical |
| ES-SUP-01-Q06 | 2025 年 SRAD 是否允许独立储能作为需求侧 UP/UF（或独立储能 UP）直接注册、预认证和竞价？ | S-CNMC-2023-SRAD-22497/P.O.7.5 将产品定义为需求 UP 的上调产品；已核验文本未确认独立储能直接资格，不能由“储能关联需求设施”条款反推。 | ES-SUP-01 | open-critical |
| ES-SUP-01-Q07 | SRAD 中储能充电负荷的基线、CUPS/UF归属和上调激活是否会被认定为需求减少、储能放电或两者之一？ | S-CNMC-2023-SRAD-22497 只要求识别关联储能并防止激活造成储能发电减少或耗电增加；基线算法和方向映射未确认。 | ES-SUP-01/ES-SP-06 | open-critical |
| ES-SUP-01-Q08 | 2025 SRAD 年度拍卖是否有独立储能实际中标/注册案例，及其服务期、容量、价格和失败记录？ | S-CNMC-2023-SRAD-22497 与 S-CNMC-2024-SRAD-CAP-24096 确认规则和 2025 价格上限框架；公开结果中的技术类型和独立储能身份尚未审计。 | ES-SUP-01/ES-SP-07 | open-critical |
| ES-SUP-01-Q09 | SRAD 的双向计量、实时功率遥测、质量位、命令/确认信号如何映射储能充放电和 UF 汇总？ | S-CNMC-2023-SRAD-22497 确认实时有功遥测、质量位、命令和确认；储能双向计量与 UF 字段映射未确认。 | ES-SUP-01/ES-SP-04/07 | open-critical |
| ES-SUP-01-Q10 | SRAD 的 CCGD/CECRE 控制中心、PM/BSP/BRP、UP/UF/UO 责任链如何在独立储能项目中配置？ | P.O.7.5 和 P.O.14.4 定义角色与控制中心接口，但未提供独立储能项目级 crosswalk。 | ES-SUP-01/ES-SP-04/06 | open-critical |
| ES-SUP-01-Q11 | SRAD 与 aFRR/mFRR/RR、现货计划、备用和补能是否可并行，哪些情形触发不可叠加或取消资格？ | S-CNMC-2023-SRAD-22497 有不改变计划、激活后重调度等要求；与其他服务/现货的储能耦合限制未闭合。 | ES-SUP-01/ES-SP-06 | open-critical |
| ES-SUP-01-Q12 | 2025 服务期实际适用的 SRAD 版本、REE 运行公告、拍卖结果及任何临时修订是什么？ | S-CNMC-2023-SRAD-22497 是 2025 基线，S-CNMC-2024-SRAD-CAP-24096 设定 2025 价格上限；逐项核验 2025 REE 公告和运行版本仍缺。 | ES-SUP-01/ES-SP-07 | open-critical |
| ES-SUP-01-Q13 | 2026-01-01 起 S-SRAD-2025（及后续 S-SRAD-2026）对独立储能资格、最小规模和产品参数的实际影响是什么？ | S-SRAD-2025 明确适用于 2026 服务期，S-SRAD-2026 后续调整分配/披露；均不得回填 2025，独立储能资格仍待确认。 | ES-SUP-01 | open-critical |

## 5B. ES-SUP-02 SOC、持续时长、补能与恢复

本节承接 `supplemental_storage_energy_requirements.md`。以下问题集中于独立储能的能量状态与履约责任；在项目级 REE/OS 文件、有效 P.O. 版本或最终欧盟决定闭合前，不得写入模型参数或收益结论。

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SUP-02-Q01 | aFRR 独立储能是否有最低/最高 SOC、可用 MWh 或 SOC 保持带？ | P.O.7.2/P.O.3.8 给出响应、实时可用备用和测试要求；P.O.9.2 只确认 SOC 遥测字段，未找到 SOC 门槛（`S-CNMC-2024-11535-PO`；`S-CNMC-2023-8113-PO92`）。 | ES-SUP-02/ES-SP-06 | open-critical |
| ES-SUP-02-Q02 | aFRR 激活期间和激活后是否有统一持续时长、补能窗口、恢复目标或相邻激活限制？ | 已确认 FAT5、15 分钟产品窗口和 4 秒再激活间隔；不能从这些参数推导电池能量容量或恢复规则（`S-CNMC-2024-11535-PO`）。 | ES-SUP-02/ES-SP-06 | open-critical |
| ES-SUP-02-Q03 | mFRR 不同交付 profile（同时参加 aFRR、mFRR-only、程序化/直接）对应的储能持续供能和恢复要求是什么？ | P.O.7.3 给出 FAT12.5 和约 5–30 分钟产品 profile，但未找到独立储能 SOC/补能数值（`S-CNMC-2024-11535-PO`）。 | ES-SUP-02/ES-SP-06 | open-critical |
| ES-SUP-02-Q04 | RR/TERRE 2025 产品是否对独立储能设有最低可用能量、激活保持、补能或恢复要求？ | P.O.3.3 确认 FAT30、15–60 分钟交付；未发现独立储能能量参数，2026 替代机制也未闭合（`S-CNMC-2025-QH`；`S-ENTSOE-TERRE-2026`）。 | ES-SUP-02/ES-SP-06/07 | open-critical |
| ES-SUP-02-Q05 | TERRE 停止后 2026 RR 替代平台、产品资格和储能恢复要求是什么？ | ENTSO-E 确认 2025-12-30 停止；截至 2026-08-11 未找到完整西班牙替代规则（`S-ENTSOE-TERRE-2026`；`S-SP-BOE-2026-17285`；`S-SP-BOE-2026-17570`）。 | ES-SP-06/07 | open-critical |
| ES-SUP-02-Q06 | 西班牙独立储能能否申请 FCR/一次调频资格，适用哪套专项测试、持续时长、SOC 和补能条款？ | SOGL 有 FCR 有限能量上位框架；P.O.3.8 已审目录未列独立储能 FCR 测试路径，西班牙采购/补偿仍未闭合（`S-EU-SOGL-2017`；`S-ENTSOE-FCR-COOP-2026`；`S-CNMC-2024-6215-PO38`）。 | ES-SUP-01/ES-SUP-02 | open-critical |
| ES-SUP-02-Q07 | CE FCR 有限能量储备最低激活期的最终决定何时生效，是否改变西班牙项目的 15–30 分钟和约 2 小时恢复框架？ | ACER 2026-07-21 通知确认 2026-07-07 请求仍在处理；截至基准日没有最终决定（`S-ACER-2026-FCR-MIN-ACT`；`S-EU-SOGL-2017`）。 | ES-SUP-02 | open-critical |
| ES-SUP-02-Q08 | 同一独立储能并行参与 aFRR/mFRR/RR/FCR 时，SOC、备用预留、激活冲突和补能如何协调？ | 已有各产品单独规则，缺少同一资源的跨产品优先级、互斥和恢复 crosswalk（`S-CNMC-2024-11535-PO`；`S-CNMC-2025-QH`；`S-ENTSOE-FCR-COOP-2026`；`S-CNMC-2023-SRAD-22497`）。 | ES-SP-06/ES-SUP-02 | open-critical |
| ES-SUP-02-Q09 | 2025 SRAD 是否允许独立储能直接以需求 UP/UF 注册，充电功率是否可作为需求基线？ | P.O.7.5 明确需求 UP、CUPS 和关联储能保护性检查；未确认独立储能直接资格、双向基线及 SOC 规则（`S-CNMC-2023-SRAD-22497`；`S-CNMC-2024-6215-PO38`）。 | ES-SUP-01/ES-SUP-02 | open-critical |
| ES-SUP-02-Q10 | SRAD 的最多 3 小时保持是否仅适用于需求响应，还是在独立储能获准后也适用？ | 3 小时是 2025 需求产品服务特征；不能在独立储能资格未闭合前当作电池能量时长（`S-CNMC-2023-SRAD-22497`）。 | ES-SUP-02 | open-critical |
| ES-SUP-02-Q11 | aFRR/mFRR/RR/SRAD 的 SOC 不足是否有免责、故障分类、可用性通知和恢复/停权程序？ | P.O.14.4 对响应不足/未交付有结算后果；公开文本未找到 SOC 免责和统一恢复规则（`S-CNMC-2024-11535-PO`；`S-CNMC-2025-QH`；`S-CNMC-2023-SRAD-22497`）。 | ES-SUP-02/ES-SP-06 | open-critical |
| ES-SUP-02-Q12 | P.O.9.2 SOC、实际可发功率和预期功率字段的单位、质量位、刷新周期和最大容量定义是什么？ | P.O.9.2 历史文本确认字段存在；项目级数据字典、通信点和双向计量映射未闭合（`S-CNMC-2023-8113-PO92`；`S-CNMC-2026-14009-TELEMETRY`）。 | ES-SP-04/07/ES-SUP-02 | open-critical |
| ES-SUP-02-Q13 | 2026-09-01 生效的 P.O.9.2/P.O.14.4 遥测罚则如何与 2026-08-11 基准及 2025 历史切片隔离？ | BOE-A-2026-14009 的生效日在基准日之后；罚则不能回填 2025 或 2026-08-11（`S-CNMC-2026-14009-TELEMETRY`；`S-CNMC-2025-QH`）。 | ES-SP-07/ES-SUP-02 | open-critical |

## 5C. ES-SUP-03 TERRE/RR 退出与 96 轮连续日内过渡

本节承接 `supplemental_rr_2026_transition.md`。2025-12-30 TERRE/LIBRA 停止边界已锁定；2026 RR 替代产品本身尚未在已核验的官方资料中锁定，因此相关资格、报价、激活、计量和结算问题继续保持 `open-critical`。96 轮的 OMIE 计划切换日已公告为 2026-09-22、首个交付日为 2026-09-23，但截至 2026-09-03 尚未发生，实际完成情况不能写成事实。

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SUP-03-Q01 | 2025-12-30 最后 TERRE MTU 的 REE/eSIOS 归档标识、激活结果和保留期是什么？ | ENTSO-E 已确认 REE/REN 最后参与 09:00—10:00 CET、10:00 停止；本地归档标识和逐笔结果尚未抽样（S-ENTSOE-TERRE-2026） | ES-SP-07 | open-critical |
| ES-SUP-03-Q02 | P.O.3.3 失效后，西班牙是否发布了新的 RR 产品、采购程序或指定的欧洲替代平台？ | BOE-17285 确认 P.O.3.3 因 TERRE 退出而失效；REE 当前平衡服务页列出 aFRR/mFRR 等，但未命名新的 RR 替代。未确认不等于禁止（S-SP-BOE-2026-17285；S-SP-REE-BALANCE-2026） | ES-SP-06 | open-critical |
| ES-SUP-03-Q03 | 若存在 RR 替代，独立储能的资格、预认证、最小规模、报价、激活、计量、结算和罚则分别是什么？ | 尚未找到替代产品的正式规则或专用数据字典；不得用 mFRR/MARI 参数替代（S-SP-BOE-2026-17285；S-ENTSOE-TERRE-2026） | SUP-01/02；ES-SP-06/07 | open-critical |
| ES-SUP-03-Q04 | 2026-09-22 是公告的计划切换日；实际完成切换和首个成功交付日的运行证据是什么？ | OMIE Instruction 4/2026 仅证明计划；2026-09-03 仍早于计划日（S-SP-OMIE-INST4-2026） | ES-SP-03/07 | open-critical |
| ES-SUP-03-Q05 | 96 轮上线后 OMIE 规则、REE P.O.、LTS/消息版本的精确版本号和发布时间是什么？ | BOE-17285/17570、OMIE Instruction 4/2026 的法律和运营层已登记；实际消息版本和生产切换记录未闭合（`S-SP-BOE-2026-17285`；`S-SP-BOE-2026-17570`；`S-SP-OMIE-INST4-2026`）。 | ES-SP-03/07 | open |
| ES-SUP-03-Q06 | PHFC、PHFCIERRE、P48/P48CIERRE、ProgUP 与 OMIE 成交文件字段如何逐项关联？ | BOE-17285 已确认计划链和“本轮仅修改单元”原则；跨机构字段 crosswalk 尚未完成（`S-SP-BOE-2026-17285`；`S-SP-BOE-2026-17570`；`S-SP-OMIE-INST4-2026`）。 | ES-SP-03/07 | open-critical |
| ES-SUP-03-Q07 | PIBCIC/PT 默认组合分解在独立储能 UO/UP/UF 结构中的具体映射是什么？ | OMIE 切换公告确认默认分解可用于维护后恢复；储能项目级 UO/UP/UF 映射未确认（`S-SP-BOE-2026-17285`；`S-SP-BOE-2026-17570`；`S-SP-OMIE-INST4-2026`）。 | ES-SP-04/07 | open-critical |
| ES-SUP-03-Q08 | XBID 跨区流量信息与西班牙计划、商业交换和物理潮流的 mRID/EIC crosswalk 是什么？ | 2026 计划和平台流功能已被官方文件提及；代码和时序字段映射未闭合（S-SP-OMIE-96-CONSULT-2026；S-SP-BOE-2026-17285） | ES-SP-03/07 | open-critical |
| ES-SUP-03-Q09 | 连续市场或 IDA 在异常、维护、系统不可用时的取消、fallback、重发布和结算顺序是什么？ | IDA/计划的部分异常处理已确认；RR fallback 未确认，2026-09-22 维护安排只适用于上线过渡，不应泛化（S-SP-OMIE-INST4-2026；S-SP-BOE-2026-17285） | ES-SP-03/06/07 | open-critical |
| ES-SUP-03-Q10 | 2026-09-03 之后出现的实际 go-live、修订、数据或结算信息如何隔离，避免倒填 2025 和 2026-08-11 基准？ | 研究原则已确定；需要把公告、实际运行日志和后续重发布文件按发布日期/生效日分层保存（`S-SP-OMIE-INST4-2026`；`S-SP-BOE-2026-17285`；`S-SP-BOE-2026-17570`）。 | ES-SP-07 | open-critical |

## 6. 状态规则

- `open-critical`：未解决前不得写入国家模型配置、收益公式或策略结论；
- `open`：可以作为研究解释的限制，但不得伪装成确定规则；
- 任何来自 OMIE 操作页面、REE 数据门户或新闻稿的内容，如未能在 BOE/CNMC/欧盟法规中找到规范性依据，须标注“操作解释/规范性状态有限”；
- 任何 2026-08-11 之后才实际生效的规则，不得回填到 2025 历史期。

## 5D. ES-SUP-04 项目级账户和代码映射

本节承接 `supplemental_account_code_crosswalk.md`。规则层可以确认 UO/UP/UF、PM/BSP/BRP、EIC、OMIE文件和REE结算概念，但项目级实际代码、私有账户和跨平台字段没有公开总表。以下问题关闭前，不得把跨机构代码映射写入策略、收益、MILP、代码或回测。

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SUP-04-Q01 | 独立非水电BESS的PM、OMIE agent、卖出/买入UO、送出/吸收UP、UF和各EIC的实际代码及生效日期是什么？ | 规则确认独立储能的送出/吸收UP结构、UP/UF的EIC要求以及OMIE UO注册关联；没有项目级公开总表，需REE/OMIE注册回执和结构数据（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES；S-REE-PARTICIPANT-2026） | ES-SP-04/06/07 | open-critical |
| ES-SUP-04-Q02 | PM code、OMIE agent code、REE参与者长/短代码是否一一对应，代表模式下由谁持有和维护？ | OMIE规则确认NIF、agent code和代理资料；REE指南对参与者/设施/UP长短代码给出一般流程，但指南以RCR发电为主，储能项目实际同步规则未确认（S-SP-BOE-2025-RULES；S-REE-ADMISSION-GUIDE-2024） | ES-SP-04/07 | open |
| ES-SUP-04-Q03 | 直接/间接代表、BRP和结算主体的实际合同、保证金、偏差责任和替换流程如何对应到账户？ | P.O.14.1/P.O.14.8及OMIE规则确认法律角色和直接/间接代表效果；项目合同、保证金账户、BRP委托关系未公开（S-SP-PO31-2024-STORAGE；S-SP-BOE-2025-RULES；S-REE-LIQ-ACCESS-2026） | ES-SP-04/06/07 | open |
| ES-SUP-04-Q04 | 纯独立化学储能是否需要CUPS、CIL、RAIPRE或CIL-RAIPRE登记，分别对应哪个计量点、UF或UP？ | REE公开FAQ和旧指南确认CUPS/CIL在特定发电/计量流程中的使用，但未确认其对纯独立BESS的普遍适用；不得从发电案例反推（S-REE-SIMEL-FAQ-STORAGE-2026；S-REE-PF-CIL-2015；S-REE-ADMISSION-GUIDE-2024） | ES-SP-04/07 | open-critical |
| ES-SUP-04-Q05 | 项目边界点、主/备用表、计量责任方、送出/吸收方向、SIMEL字段和UP/UF的逐字段映射是什么？ | REE确认SIMEL受限访问和边界点准入材料；储能双向有功概念存在，但公开资料未提供项目字段字典或主/备用表crosswalk（S-REE-SIMEL-FAQ-STORAGE-2026；S-MITECO-2025-ISP；S-REE-LIQ-GUIDE-2024） | ES-SP-04/06/07 | open-critical |
| ES-SUP-04-Q06 | OMIE `IdRemitente`、`IdOferta`、`IdUnidad(UO)`与成交、PDBF/PHF/PHFC、撤单/替代及结算文件如何逐笔连接？ | v1.37格式确认部分报价、文件头、文件日期和计划字段；公开文件类别、私有订单、版本/修订和跨REE计划连接仍需逐文件抽样（S-SP-OMIE-PUBFILES-2025；S-SP-BOE-2025-RULES） | ES-SP-03/04/07 | open-critical |
| ES-SUP-04-Q07 | 平衡激活的BSP/资源/报价ID或平台mRID如何映射到西班牙UP/UF/EIC、OMIE UO和BRP结算？ | ENTSO-E/CIM确认mRID的资源/参与方语义，REE确认BSP和平台入口；未找到西班牙项目级激活消息样例或官方cross-table（S-ENTSOE-MRID-2024；S-ENTSOE-EDI-2024；S-REE-BAL-PART-2026） | ES-SP-06/07 | open-critical |
| ES-SUP-04-Q08 | 项目控制中心、备用控制中心、调节区、聚合/组合代码及其与BSP/BRP/UP/UF的责任边界是什么？ | P.O.9.2和REE服务页面确认实时控制/调节概念；项目控制中心、调节区和组合代码没有公开项目级映射（S-CNMC-2023-8113-PO92；S-REE-BAL-PART-2026） | ES-SP-04/06 | open |
| ES-SUP-04-Q09 | 2025-01-01—12-31各代码、文件格式和计量/结算字段的生效、停用和修订日期如何逐日切片？ | 2025-03-18市场规则、2025-05-01计量边界和2025-10-01日前MTU边界已登记；项目代码及REE/OMIE生产版本不能由当前页面倒推（S-SP-BOE-2024-RULES；S-SP-BOE-2025-RULES；S-MITECO-2025-ISP；S-SP-OMIE-PUBFILES-2025） | ES-SP-04/07 | open-critical |
| ES-SUP-04-Q10 | REE私有结算ZIP、SIMEL读数和OMIE公开文件的访问权限、保留期、修订标志和结算注释能否支持项目级逐笔审计？ | REE确认详细BRP结算文件受限，结算指南给出若干文件/字段名称；公开历史覆盖、版本号和项目可见权限未闭合（S-REE-LIQ-ACCESS-2026；S-REE-LIQ-GUIDE-2024；S-SP-OMIE-PUBFILES-2025） | ES-SP-07 | open |

## 5E. ES-SUP-04 项目资料闭环清单

为关闭上述问题，项目方/代表/BRP/BSP至少应取得以下原件或带生效日期的导出：

| 资料 | 用途 |
|---|---|
| REE参与者、UP/UF结构和EIC回执 | 确认送出/吸收UP、UF、EIC、节点附加UP和生效日期 |
| OMIE agent/UO注册与代表授权 | 确认agent、买/卖UO、代表模式和UO聚合边界 |
| PM/BSP/BRP/结算主体合同及保证金信息 | 确认市场、平衡和偏差责任 |
| 并网、设施/技术单元、计量点和SIMEL资料 | 确认边界点、计量责任方、主/备用表和双向方向 |
| CUPS/CIL/RAIPRE（如项目类型适用）文件 | 判断CUPS/CIL是否适用于纯独立BESS，避免套用发电案例 |
| OMIE报价、成交、计划、撤单/修订样例 | 连接 `IdRemitente`、`IdOferta`、UO和市场结果 |
| REE平衡激活、计划、计量、偏差和结算样例 | 连接BSP/资源/mRID、UP/UF、SIMEL和BRP结算 |

在这些资料取得前，`ES-SUP-04-Q01/Q04/Q05/Q06/Q07/Q09` 维持 `open-critical`，不能改成“已确认”。

## 5F. ES-SUP-05 数据接口、版本与权限核验

本节承接 `supplemental_data_interface_validation.md`。接口文档、公共文件目录和平台页面只能确认公开入口、文件/字段线索、时间表达及访问边界；未逐指标、逐文件或逐项目取得的内容继续保持 `open`/`open-critical`，不得作为模型输入。研究历史期为 2025-01-01—2025-12-31，规则基准日为 2026-08-11；2026-08-11 后的实际发布和未来接口不得倒填历史。

| ID | 未决问题 | 当前证据边界 | 影响阶段 | 优先级 |
|---|---|---|---|---|
| ES-SUP-05-Q01 | REE/eSIOS 中 aFRR 容量、aFRR/mFRR/RR 能量、平衡价格/激活和不平衡价格的准确 indicator ID、单位、分辨率、地理层级和最终更新时间是什么？ | 指标名称搜索、指标值 API 路由、日期过滤和元数据字段已确认；未逐指标查询并取得 2025 版本/单位/完整覆盖（S-REE-REData-API-2026；S-eSIOS-API-IND-2026；S-REE-ESIOS-API-2026） | ES-SP-06/07 | open-critical |
| ES-SUP-05-Q02 | eSIOS 归档接口列出的 2025 平衡/结算文件是否全年完整，是否存在重发布、替换和原版本保留？ | `date_type=datos/publicacion`、archive ID、数据日期和发布日期字段已确认；目标归档尚未逐项盘点（S-REE-ESIOS-ARCHIVE-API-2026；S-REE-DOWNLOAD-2026） | ES-SP-06/07 | open-critical |
| ES-SUP-05-Q03 | eSIOS/REE 的缺失值、估算值、临时值和最终值是否有统一质量/修订字段，或必须依不同指标规则判断？ | API 有 `last-update`/`values_updated_at` 等时间线索；统一质量/最终状态码未确认（S-REE-REData-API-2026；S-REE-ESIOS-API-2026） | ES-SP-07 | open |
| ES-SUP-05-Q04 | OMIE 2025 各类公开文件的逐日版本、替换文件、撤单/修订标志及公开保留期是什么？ | PDBC 月度文件条目与 v1.37 字段/发行时间已确认；全类别逐文件版本线未建立（S-SP-OMIE-PDBC-ARCHIVE-2026；S-SP-OMIE-PUBFILES-2025；S-SP-OMIE-FILES-2026） | ES-SP-03/04/07 | open-critical |
| ES-SUP-05-Q05 | OMIE 文件中的 `Fecha Emisión`、市场/交付日期、时段/轮次和版本后缀，在 23/25 小时日及 2025 15 分钟规则下如何逐文件对应？ | 文件头/日期/版本字段已确认；DST 日的具体 period 序列未抽样闭合（S-SP-OMIE-PUBFILES-2025；S-REE-DST-2025；S-MITECO-2025-ISP） | ES-SP-03/07 | open-critical |
| ES-SUP-05-Q06 | ENTSO-E 西班牙平衡数据的 EIC/domain、documentType/processType、mRID、版本和 2025 历史覆盖如何与 REE/OMIE 记录对应？ | UTC、API权限、版本机制和 schema 入口已确认；西班牙项目级 crosswalk 未找到（S-ENTSOE-TP-MOP-2025；S-ENTSOE-TP-QUERY-2025；S-ENTSOE-EDI-LIB-2026；S-ENTSOE-MRID-2024） | ES-SP-06/07 | open-critical |
| ES-SUP-05-Q07 | REE SIMEL 对独立 BESS 的送出/吸收计量字段、质量码、估算标志、时间戳、保留期和项目可见权限是什么？ | 双向有功概念和受限访问已确认；逐字段字典和项目授权未公开（S-REE-SIMEL-FAQ-STORAGE-2026；S-MITECO-2025-ISP） | ES-SP-04/06/07 | open-critical |
| ES-SUP-05-Q08 | REE 私有 BRP 结算 ZIP 的 2025 发布批次、预闭算/闭算版本、修订注释和保留期如何取得？ | 文件角色和 BRP 受限入口已确认；项目文件、访问期和完整修订链未确认（S-REE-LIQ-ACCESS-2026；S-REE-LIQ-GUIDE-2024） | ES-SP-07 | open-critical |
| ES-SUP-05-Q09 | 2025-03-30/10-26 的每个公开市场、平衡、计量和结算文件是否使用 92/100 个 15 分钟位置、重复本地小时或其他编号？ | 年度日历和 P.O.10.5 缺失估算逻辑已确认；数据集逐项表示未确认（S-REE-DST-2025；S-MITECO-2025-ISP；S-REE-ESIOS-API-2026） | ES-SP-03/06/07 | open-critical |
| ES-SUP-05-Q10 | 2026-09-01 遥测修订、96 轮连续日内上线和 EDI/MoP 后续版本实际发布后，哪些字段从未来变为当前？ | 官方生效/计划边界已记录；截至 2026-09-03 尚无可用于本基准的完整实际运行证据（S-CNMC-2026-RT；S-SP-OMIE-INST4-2026；S-ENTSOE-MOP-ROADMAP-2026） | ES-SP-07 | open-critical |

在上述问题关闭前，不得把公开接口的 indicator ID、文件名、字段或时间戳当成独立储能的项目实测值，也不得以公开结果替代 BRP/SIMEL 私有记录。
