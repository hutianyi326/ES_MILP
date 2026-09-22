# 西班牙独立储能数据接口、版本与权限核验（SUP-05）

> 研究对象：西班牙大陆竞价区（peninsular bidding zone）的独立、非水电化学储能。  
> 历史期：2025-01-01—2025-12-31。  
> 规则基准日：2026-08-11。  
> 补充核验访问日：2026-09-03。  
> 本文件只核验官方公开接口、文件格式、时间/版本和权限边界；不下载项目时序，不进行策略、收益、MILP、代码、回测或预测。

## 0. 先给结论

1. **公开接口适合做规则和市场层核验，不足以自动形成项目级审计链。** REE/eSIOS、OMIE 和 ENTSO-E 可以提供公开的市场结果、计划、价格、系统指标、文件元数据或平台层消息入口；独立储能项目的 UO—UP/UF—EIC、BSP 激活、SIMEL 双向计量和 BRP 结算，仍需要 REE、OMIE、代表、BSP/BRP 或计量责任方的项目文件。[S-REE-REData-API-2026][S-REE-ESIOS-ARCHIVE-API-2026][S-SP-OMIE-PUBFILES-2025][S-REE-SIMEL-FAQ-STORAGE-2026][S-REE-LIQ-ACCESS-2026]
2. **数据日期、交付日期和发布日期/发行时间必须分开保存。** eSIOS 的归档接口允许按 `date_type=datos` 或 `date_type=publicacion` 查询，并返回 `date_times` 与 `publication_date`；OMIE 公共文件头也区分文件发行日期和市场/交付日期。[S-REE-ESIOS-ARCHIVE-API-2026][S-SP-OMIE-PUBFILES-2025]
3. **西班牙本地数据和欧洲数据的时区表达不同。** eSIOS 示例同时返回带本地偏移的 `datetime` 和 UTC 的 `datetime_utc`；ENTSO-E Transparency Platform 的响应时间统一用 UTC，但日级响应可能按照数据发布区域的本地日返回完整的一天。因此，欧洲平台数据不能直接把 `00:00Z` 当作西班牙本地日界。[S-REE-ESIOS-API-2026][S-ENTSOE-TP-QUERY-2025]
4. **2025 年存在 23 小时日和 25 小时日。** REE 的 2025 日历资料列出 3 月 30 日为 23 小时日、10 月 26 日为 25 小时日；P.O.10.5 对缺失计量的估算还规定了这两类日期的特殊处理。该估算规则不是把原始数据强行补成 24 小时，也不代表每个公开接口的原始序列都会使用相同的时段编号。[S-REE-DST-2025][S-MITECO-2025-ISP]
5. **2025 全年数据“可查询”不等于“逐项完整、不可修订”。** OMIE 公开列表在访问日显示了 `pdbc_202501.zip` 至 `pdbc_202512.zip` 的月度文件，但这只能确认 PDBC 类别的公开列表样本；eSIOS 的归档接口能按日期检索，但目标平衡指标、文件完整性和重发布历史没有在本任务逐项核验。[S-SP-OMIE-PDBC-ARCHIVE-2026][S-REE-ESIOS-ARCHIVE-API-2026]
6. **2026-08-11 之后的接口或规则不得回填 2025。** 2026-09-01 生效的 REE 实时信息修订，以及计划于 2026-09-22/23 切换的 96 轮连续日内交易，均只能作为未来/当前边界记录；不能改变 2025 历史数据的时段、字段或结算口径。[S-CNMC-2026-RT][S-SP-OMIE-INST4-2026][S-SP-BOE-2026-17285][S-SP-BOE-2026-17570]

## 1. 内容分层和研究边界

### 1.1 F/I/A/U 的含义

- **F｜规则或接口事实**：官方规则、官方 API 文档、官方文件格式或官方平台页面直接写明的内容。
- **I｜研究解释**：把接口字段、日期或权限翻译成数据整理和审计含义；不是新增市场规则。
- **A｜建模假设登记**：未来建模时必须显式登记的处理原则。本 SUP-05 不新增可执行模型参数。
- **U｜待确认**：官方证据尚未闭合，不能当作规则事实、项目数据或收益模型输入。`open-critical` 表示关闭前不得写入国家模型配置、收益公式、代码或回测。

### 1.2 不在本任务内完成的工作

本文件不下载或保存原始时序、不查询项目私有账户、不执行任何 API 批量采集、不生成价格/激活/偏差收益、不编写策略或 MILP。文件中出现的字段名称只表示官方接口或指南中的候选字段，不代表某个独立储能项目一定能取得这些字段。

## 2. 官方接口和文件层次

### 2.1 接口总表

| 数据层 | 官方入口和可确认内容 | 适合核验的内容 | 仍需项目/逐文件确认的内容 |
|---|---|---|---|
| REE REData API | GET `/lang/datos/{category}/{widget}`；可按 ISO 8601 起止日期和小时/日/月/年聚合；JSONAPI 响应含 indicator、`last-update` 和缓存元数据 | 系统级需求、发电、市场/运行公开指标的入口、时间过滤、响应更新时间 | 平衡容量/能量的具体 widget、indicator ID、单位、刷新/最终修订规则、完整 2025 覆盖；不能从入口自动推出独立 BESS 项目字段。[S-REE-REData-API-2026] |
| eSIOS Indicator API | `/indicators/{id}`；官方文档列出 `start_date`、`end_date`、`time_trunc` 的日期范围、小时和 15 分钟聚合示例，返回 `value`、`datetime`、`datetime_utc`、`values_updated_at`、`magnitud` 和地理标识 | 指标名称搜索/取得 ID、指标元数据、时间序列查询方式、本地/UTC 时间对照、公开指标的粗粒度复核 | 目标平衡指标 ID、单位、地理层级、发布时间延迟、限流、缺失和修订标志，以及 2025 全年是否连续。[S-REE-ESIOS-API-2026][S-eSIOS-API-IND-2026] |
| eSIOS Archive API / 下载 | `/archives` 可按数据日期或发布日期过滤；响应示例含 archive ID、类型、数据日期范围、`date_times`、`publication_date` 和下载 URL | 区分“数据属于哪一天”和“文件何时发布”，定位公开归档类别 | 每个平衡、偏差、计量文件是否存在、是否被替换、是否保留全部历史版本；本任务不进行归档下载。[S-REE-ESIOS-ARCHIVE-API-2026][S-REE-DOWNLOAD-2026] |
| OMIE 公共文件 | 公共文件目录覆盖价格、曲线、计划、容量、交易和程序；文件格式使用分号字段，文件头含 `Fecha Emisión`、市场/交付日期和报告标题，文件名通常带日期和版本后缀 | 日前/日内公开结果、计划、价格、容量，文件发行时间和版本线索；PDBC 月度目录可见 2025 文件样本 | 公开报价是否仍处于保密期、每个类别的修订/替换规则、UO—REE UP/UF 交叉表、项目级文件和私有报价。[S-SP-OMIE-FILES-2026][S-SP-OMIE-PUBFILES-2025][S-SP-OMIE-FORMATS-2024] |
| REE 结算和 SIMEL | 结算指南提到 `reganeu`/`reganecuQH`、`p48cierre`、`rp48preccierre` 和 `prdv*` 文件；SIMEL 处理边界点计量，储能需分别记录送出/吸收方向 | 结算文件类型、字段族和计量方向的规则核验；判断公开数据与项目结算数据的差距 | 逐项目计量点、质量标志、双向表计、激活/计量对应、BRP 结算 ZIP、发布批次和修订注释；详细 BRP 文件为受限访问。[S-REE-LIQ-GUIDE-2024][S-REE-LIQ-ACCESS-2026][S-REE-SIMEL-FAQ-STORAGE-2026] |
| ENTSO-E Transparency Platform | 平台集中发布发电、负荷、输电和平衡等规定数据；REST API 可按数据项和时间区间查询，平台有下载、订阅和数据仓库层次 | 欧洲层平衡/价格/容量/计划数据、数据项代码、平台版本和发布时间；跨区域数据可作西班牙公开数据的交叉核验 | 西班牙具体 EIC/domain、BSP/资源/激活消息与 UP/UF/UO 的项目级对应，具体 2025 数据项完整性和每个消息 schema 的历史版本。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-TP-QUERY-2025][S-ENTSOE-EDI-LIB-2026] |

### 2.2 接口字段与含义：不要把“候选字段”当成项目实测值

#### F｜REE/eSIOS

REE REData 的接口说明允许使用 `start_date`、`end_date` 和 `time_trunc`，并以 JSONAPI 返回指标。示例响应含 `last-update`、缓存的 `expireAt`、指标 `magnitude`、指标更新时间和带时区的值时间戳；这些字段可以帮助判断“接口何时刷新”，但没有承诺每一个平衡指标都具有相同的刷新或终结时间。[S-REE-REData-API-2026]

eSIOS 的指标名称搜索接口用于发现/取得 indicator ID，并记录文档中的 token/API key 入口；指标值查询接口则提供 `start_date`、`end_date`、`time_trunc`、`value`、`datetime`、`datetime_utc`、`values_updated_at`、`magnitud` 和地理标识字段。`time_trunc=fifteen_minutes` 代表接口提供该聚合选项，不等于每个指标在 2025 年都以 15 分钟原始分辨率发布；需要逐个指标查看其元数据。[S-eSIOS-API-IND-2026][S-REE-ESIOS-API-2026]

eSIOS Archive API 将 `date_type=datos` 和 `date_type=publicacion` 分开。响应中的 `date` 区间表示数据日期，`publication_date` 表示发布日期，`download` 只是归档下载入口。这个接口设计可以支持“按交付日找数据”和“按发布日期找文件”两种检查，但不能据此确认归档内容已覆盖某项平衡产品的全年所有时段。[S-REE-ESIOS-ARCHIVE-API-2026]

#### F｜OMIE

OMIE 公共文件格式说明了文件头、文件发行时间、市场/交付日期、分号分隔字段和文件版本后缀。公开格式中可见的字段族包括市场日、时段、价格、程序、报价或单位标识；具体文件的字段必须按当日适用的版本读取。v1.36/v1.37 是 2025 年出现的格式边界，不能用 2025 年 9 月以后的字段定义回填年初文件。[S-SP-OMIE-PUBFILES-2025]

OMIE 公开列表在 2026-09-03 访问时显示了 PDBC 目录中 `pdbc_202501.zip` 至 `pdbc_202512.zip` 的月度条目，并列出文件大小和 changed 时间。该观察只证明该类别在当前目录中有 2025 月度归档条目；它不证明所有文件没有重发，也不证明平衡、计量和结算数据同样公开。[S-SP-OMIE-PDBC-ARCHIVE-2026]

#### F｜REE 结算、计量和储能方向

REE 结算指南列出了小时和四分之一小时结算文件、预闭算/闭算阶段以及用于核对不平衡价格的 `prdv*` 文件名；详细 BRP 结算 ZIP 的访问入口由 REE 页面限制给 BRP。储能计量规则区分 `Activa saliente`（送出/注入）和 `Activa entrante`（吸收/取电），但项目的具体 SIMEL 字段、质量码、主/备用表和公开下载权限没有在本任务闭合。[S-REE-LIQ-GUIDE-2024][S-REE-LIQ-ACCESS-2026][S-MITECO-2025-ISP][S-REE-SIMEL-FAQ-STORAGE-2026]

#### F｜ENTSO-E

ENTSO-E 平台的官方手册将公开用户、数据提供者和数据消费者区分开：网页可浏览，下载或 REST API/数据仓库访问需要注册；REST API 面向有限数据量，数据仓库提供更大数据量的异步查询。数据提供者重新提交文件时应递增版本号，平台会保留提交版本。所查阅的官方 MOP PDF 的 URL/package 标注为 V2r1，但正文页仍显示 V2r0，因此这里只把“至少五年保存”和“保留提交版本”记为所查阅手册中的平台级政策，并把精确版本及最新 MoP v3.x 适用性保留为版本控制问题。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-MOP-ROADMAP-2026]

官方 Query Response 说明：响应时间统一为 UTC；部分日级数据项会返回完整本地日；结果可能是部分匹配或精确匹配；接口会返回 429（请求过多）、401（令牌缺失/无效）或 200/999（无匹配数据）等状态。因而“API 返回成功”不等于“该时间区间已经完整覆盖”。[S-ENTSOE-TP-QUERY-2025]

## 3. 时间、时区、夏令时与轮次

### 3.1 保存规则

### F｜官方可确认的时间表达

1. eSIOS 指标接口示例同时给出 `datetime`（带 `+01:00` 或 `+02:00` 偏移）和 `datetime_utc`（`Z` 结尾）。在西班牙语境中，`Europe/Madrid` 的冬季偏移对应 CET（UTC+1），夏季偏移对应 CEST（UTC+2）；应同时保留原始 offset、UTC 时间和数据集自身的时段标签，不据此推导统一的 DST 编号。[S-REE-ESIOS-API-2026][S-SP-OMIE-FORMATS-2024]
2. ENTSO-E Transparency Platform 的响应统一以 UTC 表达；对于日级数据，响应区间可能以数据发布区域的本地日为边界后转换成 UTC。因此西班牙市场日、交付日和 UTC 日界需要分别保存。[S-ENTSOE-TP-QUERY-2025]
3. OMIE 公共文件头使用文件发行日期和市场/交付日期字段，时段字段和文件版本另行记录；`Fecha Emisión` 不是交付日。[S-SP-OMIE-PUBFILES-2025]

### I｜建议的最小时间键

如果未来取得项目数据，每条记录至少应保留以下时间字段：

```text
data_date / delivery_date
period_start_local_with_offset
period_end_local_with_offset
period_start_utc / period_end_utc
publication_or_issue_datetime
market_session_or_round
file_version_or_revision_status
```

这是一项数据审计建议，不是新增市场规则。任何后续模型必须避免以本地“第 1—24 小时”覆盖 UTC 真实时间，也不能把发布日期当成交付时间。

### 3.2 23 小时日、25 小时日和四分之一小时

### F｜2025 日历和缺失计量处理

REE 发布的 2025 年度运营日历将 **2025-03-30** 标为夏令时变化的 23 小时日，并将 **2025-10-26** 标为冬令时变化的 25 小时日；文件采用 H21-H23、H23-H25 等本地时段标签说明变化。[S-REE-DST-2025]

P.O.10.5 的历史估算附件规定：23 小时日按 24 个周期的估算逻辑处理，但不对换时周期估算；25 小时日按 24 个周期的估算逻辑处理，换时周期的估算值与前一个周期相同。该条款针对**缺失计量的估算**，不能用来修改已有真实记录，也不能把所有接口的 DST 表示方式统一改成“空一段”或“复制一段”。[S-MITECO-2025-ISP]

### I｜15 分钟和 96 轮的转换

- 正常本地日：24 小时，若每小时四个 15 分钟合同，则为 96 个四分之一小时位置。
- 23 小时日：按本地钟表的自然时段可出现 92 个 15 分钟位置；25 小时日可出现 100 个位置。但公开接口的具体 period 编号、重复小时表示和是否以 UTC 连续序列发布，必须按文件类别逐项核验，不能仅凭算术生成缺失记录。
- 2025 年历史数据的“15 分钟”来自市场/计量规则和相应文件版本；2026 年 96 轮连续日内市场是另一项操作切换，不能把“96 轮”倒写成 2025 年的统一接口轮次。[S-SP-BOE-2025-RULES][S-MITECO-2025-ISP][S-SP-BOE-2026-17570]

### F｜2026 96 轮边界

OMIE Instruction 4/2026 计划在 2026-09-22 维护后启动 96 轮连续日内交易，并以 2026-09-23 作为首个交付日；截至本文件访问日，该计划尚不能视为已完成的历史运行事实。相关 2026 规则还区分连续市场轮次与 IDA 场次，不能把 96 轮与 24 个 RR horizon 混为一谈。[S-SP-OMIE-INST4-2026][S-SP-BOE-2026-17570][S-SP-BOE-2026-17285]

## 4. 2025 历史覆盖、缺失、修订和发布时间

### 4.1 覆盖状态矩阵

| 数据集/接口 | 2025 覆盖判断（截至 2026-09-03） | 可以确认的证据 | 不能直接假设的内容 |
|---|---|---|---|
| OMIE PDBC 月度公开归档 | **部分确认**：公开目录显示 `pdbc_202501.zip`—`pdbc_202512.zip` 条目 | 文件名、月度范围、大小和 changed 时间可见。[S-SP-OMIE-PDBC-ARCHIVE-2026] | 其他市场类别、每日日文件、平衡文件、项目报价和所有修订是否完整 |
| OMIE 价格/计划/日内其他类别 | **入口确认，全年完整性 U** | 公共文件目录与 v1.37 格式说明。[S-SP-OMIE-FILES-2026][S-SP-OMIE-PUBFILES-2025] | 每个类别 2025 全年是否连续、某日是否重发、旧版本是否可恢复 |
| REE/eSIOS 指标 | **接口可检索，指标级覆盖 U** | 日期范围、聚合和指标/归档查询入口。[S-REE-REData-API-2026][S-REE-ESIOS-API-2026][S-REE-ESIOS-ARCHIVE-API-2026] | 目标 aFRR/mFRR/RR/不平衡指标 ID、单位、缺失、最终更新时间和全年连续性 |
| REE 结算与 SIMEL | **项目权限决定** | 指南中的文件名称/字段族和受限入口。[S-REE-LIQ-GUIDE-2024][S-REE-LIQ-ACCESS-2026][S-REE-SIMEL-FAQ-STORAGE-2026] | 纯独立储能项目的私有 ZIP、SIMEL 读数、计量质量码和历史保留 |
| ENTSO-E Transparency Platform | **平台级历史政策确认，西班牙平衡项 U** | 至少五年的平台级保存说明、UTC 响应、版本机制。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-TP-QUERY-2025][S-ENTSOE-EDI-LIB-2026] | 2025 每个西班牙平衡数据项是否完整，是否有全部替代版本和正确 EIC/domain |

### 4.2 缺失值与修订标志

### F

- REE/eSIOS 接口提供 `last-update`、`values_updated_at` 或归档 `publication_date` 等时间线索；这不是统一的“最终值”标志，也不是每个指标都有相同的修订语义。[S-REE-REData-API-2026][S-REE-ESIOS-API-2026][S-REE-ESIOS-ARCHIVE-API-2026]
- OMIE 文件名和文件头的版本/发行日期可用于建立文件版本线；更换后的文件可能在目录中表现为 changed 时间变化。公开格式并未为所有文件类别提供统一的项目级“revision reason”字段。[S-SP-OMIE-PUBFILES-2025][S-SP-OMIE-PDBC-ARCHIVE-2026]
- ENTSO-E 平台允许数据提供者以递增版本重新提交，手册说明平台保留提交版本；Query Response 还警示结果可以是部分匹配。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-TP-QUERY-2025]

### I

后续历史数据整理应把以下状态分开：

```text
observed/published value
estimated or missing value
intermediate/preliminary value
final/closed value
replacement or revised file
not found / no matching data
```

如果接口只给出“更新时间”而没有明确状态码，应保留更新时间并把最终性标为 `U`，不能因为数值存在就称其为最终结算值。

### A｜仅作假设登记，不执行

未来若需要把不同来源对齐，必须在模型或数据处理说明中登记：以官方原始时区为准、同时保存 UTC 和 Europe/Madrid、任何缺失估算不替代真实计量、事后重发布数据不得进入当时的决策输入。本 SUP-05 不把上述原则转换为代码、收益公式或模型参数。

## 5. 公开与受限权限边界

| 资源 | 公共可见范围 | 受限范围/限制 | 项目级结论 |
|---|---|---|---|
| REData API | GET 接口、公开 widget、JSONAPI 响应。[S-REE-REData-API-2026] | 具体指标、单位和发布状态要逐项查；认证要求以对应接口说明为准。[S-REE-REData-API-2026] | 可做系统/市场公开指标核验，不能当作项目实测 |
| eSIOS Indicator/Archive API | 指标名称搜索、指标值查询、归档元数据和公共下载入口。[S-eSIOS-API-IND-2026][S-REE-ESIOS-API-2026][S-REE-DOWNLOAD-2026] | 是否需要 token/API key、是否限流、归档类别和数据内容按资源逐项核验；未确认所有平衡文件公开。[S-eSIOS-API-IND-2026][S-REE-ESIOS-API-2026] | “可调用入口”不等于“项目级全部字段” |
| OMIE 公共文件 | 价格、计划、部分曲线、容量、公开结果和文件格式 | 报价详情、私有订单、代表/保证金资料和部分文件受市场规则/保密窗口限制；格式资料提到日前报价文件的 90 日边界，但不能外推到其他类别 | 可核验市场结果和文件血缘，不能据此重建某 BESS 的全部报价与 UO 映射。[S-SP-OMIE-FORMATS-2024][S-SP-OMIE-PUBFILES-2025] |
| REE 结算 | 官方指南描述文件角色；公共汇总的可见范围需逐项确认。[S-REE-LIQ-GUIDE-2024] | REE 页面明确详细 BRP 结算 ZIP 只向 BRP 开放；SIMEL 访问限于计量参与者/其代理。[S-REE-LIQ-ACCESS-2026][S-REE-SIMEL-FAQ-STORAGE-2026] | 项目逐笔偏差、激活、计量和结算审计必须取得 BRP/计量责任方授权文件。[S-REE-LIQ-ACCESS-2026][S-REE-SIMEL-FAQ-STORAGE-2026] |
| ENTSO-E Transparency Platform | 网页浏览无需注册的范围由手册说明 | 下载、REST API/数据仓库需要注册；订阅需要注册接收服务；数据提供者有更高的修订/纠错权限 | 欧洲公共数据可作交叉核验，不能把公开平台的资源标识直接视为西班牙项目代码。[S-ENTSOE-TP-MOP-2025] |

### I｜权限与“可见性”的实际含义

公开页面显示某个指标、文件名或价格，并不意味着可以看到独立储能的项目名称、UO、UP/UF、BSP 激活报价、SOC、双向电表、BRP 结算金额或代表合同。项目级信息链至少需要向以下主体索取：

1. REE：UP/UF/EIC、BSP 资格、激活/运行消息、SIMEL 边界与计量文件。[S-REE-PARTICIPANT-2026][S-REE-BAL-PART-2026][S-REE-SIMEL-FAQ-STORAGE-2026]
2. OMIE 或市场代表：agent、UO、报价、成交、撤单/替代和保证金记录。[S-SP-OMIE-AGENT-2026][S-SP-OMIE-PUBFILES-2025]
3. BSP/BRP/结算主体：平衡激活、最终位置、偏差和结算 ZIP。[S-REE-LIQ-ACCESS-2026][S-REE-LIQ-GUIDE-2024]
4. 计量责任方：送出/吸收电量、质量位、估算/无效标志和主/备用表记录。[S-REE-SIMEL-FAQ-STORAGE-2026][S-MITECO-2025-ISP]

这些是项目取证清单，不是规则要求项目必须向所有主体分别申请同一套文件。

## 6. 哪些数据可用于规则核验，哪些不能替代项目资料

### F｜可用于规则核验的资料

- CNMC/BOE 的市场规则、P.O.10.x、P.O.14.x 和已生效修订的发布日期/生效日期。[S-CNMC-2026-RT][S-MITECO-2025-ISP]
- OMIE 的市场文件格式、公开文件目录、公开价格/程序/容量结果和发行时间。[S-SP-OMIE-PUBFILES-2025][S-SP-OMIE-FILES-2026]
- REE/eSIOS 的公开指标定义、日期过滤、归档发布日期与数据日期。[S-REE-REData-API-2026][S-REE-ESIOS-API-2026][S-REE-ESIOS-ARCHIVE-API-2026]
- ENTSO-E 的 Regulation 543/2013 数据项、实施指南、EIC/EDI schema、UTC 和版本信息。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-TP-QUERY-2025][S-ENTSOE-EDI-LIB-2026]
- REE/OMIE/ENTSO-E 对平台上线、停用、格式更新或未来切换的官方公告。[S-SP-OMIE-INST4-2026][S-ENTSOE-TERRE-2026][S-ENTSOE-MOP-ROADMAP-2026]

### U/open-critical｜不能仅靠公开接口确认的项目数据

以下内容在公开资料中没有形成独立储能项目级总表：

- 项目实际 PM、OMIE agent、卖出/买入 UO、送出/吸收 UP、UF 和 EIC 及其生效日期；
- BSP 资源/报价/激活消息的 `mRID`、平台 ID 与西班牙 UP/UF/UO 的逐笔 crosswalk；
- SIMEL 点位、CUPS/CIL（如适用）、双向有功、质量位、估算/无效标志和计量责任方文件；
- BRP 的 `MEDBC`、`POSFIN`、`AJUDSV`、`DESV` 逐项结算记录及其私有 ZIP 的发布日期、保留和修订历史；
- 2025 年各平衡指标的公开 indicator ID、单位、历史覆盖、最终修订标志、API 限额和平台切换日；
- 2026-08-11 后的 96 轮连续日内、2026-09-01 遥测字段及其实际运行数据是否已经稳定发布。

这些问题与 SUP-04 的项目账户和代码问题相互关联，但不能因为“接口中存在一个字段名”就关闭项目级问题。

## 7. 2026-08-11 后接口和规则的时间隔离

| 事项 | 时间状态 | 本研究处理 |
|---|---|---|
| CNMC/BOE 2026-14009 实时信息修订 | 2026-09-01 生效，晚于 2026-08-11 规则基准日 | 只作为 future-effective 边界；其新遥测字段、质量比例和后续发布不能回填 2025 或基准日。[S-CNMC-2026-RT] |
| TERRE/LIBRA 停止及 RR 替代 | 2025-12-30 停止旧平台；2026 替代机制的具体产品/资格/数据接口仍需按官方生效文件确认 | 2025 数据在停止时点截断；2026 后续不得默认仍有相同 RR 产品或接口。[S-ENTSOE-TERRE-2026][S-SP-BOE-2026-17285] |
| OMIE 96 轮连续日内切换 | OMIE Instruction 4/2026 计划 2026-09-22 维护、2026-09-23 首个交付日；截至 2026-09-03 尚为未来计划 | 不修改 2025 市场轮次；实际 go-live 和后续文件格式需在发生后重新核验。[S-SP-OMIE-INST4-2026] |
| ENTSO-E MoP/EDI 版本 | 2025-12-02、2026-03-02、2026-06-10 等版本更新节点已在官方 EDI 页面列出 | 建立“按文件/数据项版本”的历史边界；不以当前 schema 自动覆盖 2025 消息。[S-ENTSOE-EDI-LIB-2026][S-ENTSOE-MOP-ROADMAP-2026] |

### I｜时间隔离原则

一条在 2026-08-11 之后发布的公告可以说明未来接口状态，但不能说明 2025 当天参与者已经能看到该字段；一条在 2026 年重发布的 2025 文件可以帮助事后审计，但不能作为当时交易决策输入。后续研究应保存 `publication_at`、`effective_from`、`delivery_date` 和 `retrieved_at` 四类日期。

## 8. SUP-05 未决问题

以下问题已经同步至 [spot_open_questions.md](spot_open_questions.md)，在解决前不得写入模型、收益或代码。

| ID | 未决问题 | 当前证据边界 | 优先级 |
|---|---|---|---|
| ES-SUP-05-Q01 | REE/eSIOS 中 aFRR 容量、aFRR/mFRR/RR 能量、平衡价格/激活和不平衡价格的准确 indicator ID、单位、分辨率、地理层级和最终更新时间是什么？ | 指标名称搜索、指标值 API 路由、日期过滤和元数据字段已确认；未逐指标查询并取得 2025 版本/单位/完整覆盖。[S-eSIOS-API-IND-2026][S-REE-ESIOS-API-2026][S-REE-REData-API-2026] | open-critical |
| ES-SUP-05-Q02 | eSIOS 归档接口列出的 2025 平衡/结算文件是否全年完整，是否存在重发布、替换和原版本保留？ | `datos`/`publicacion` 双日期和 archive metadata 已确认；目标归档尚未逐项盘点。[S-REE-ESIOS-ARCHIVE-API-2026][S-REE-DOWNLOAD-2026] | open-critical |
| ES-SUP-05-Q03 | REE/eSIOS 的缺失值、估算值、临时值和最终值是否有统一质量/修订字段，或须依不同指标规则判断？ | API 有 `last-update`/`values_updated_at` 等时间线索；统一状态码未确认。[S-REE-REData-API-2026][S-REE-ESIOS-API-2026] | open |
| ES-SUP-05-Q04 | OMIE 2025 各类公开文件的逐日版本、替换文件、撤单/修订标志及公开保留期是什么？ | PDBC 月度文件条目与 v1.37 字段/发行时间已确认；全类别逐文件版本线未建立。[S-SP-OMIE-PDBC-ARCHIVE-2026][S-SP-OMIE-PUBFILES-2025][S-SP-OMIE-FILES-2026] | open-critical |
| ES-SUP-05-Q05 | OMIE 文件中的 `Fecha Emisión`、市场/交付日期、时段/轮次和版本后缀，在 23/25 小时日及 2025 15 分钟规则下如何逐文件对应？ | 文件头/日期/版本字段已确认；DST 日的具体 period 序列未抽样闭合。[S-SP-OMIE-PUBFILES-2025][S-REE-DST-2025][S-MITECO-2025-ISP] | open-critical |
| ES-SUP-05-Q06 | ENTSO-E 西班牙平衡数据的 EIC/domain、documentType/processType、mRID、版本和 2025 历史覆盖如何与 REE/OMIE 记录对应？ | UTC、API权限、版本机制和 schema 入口已确认；西班牙项目级 crosswalk 未找到。[S-ENTSOE-TP-MOP-2025][S-ENTSOE-TP-QUERY-2025][S-ENTSOE-EDI-LIB-2026][S-ENTSOE-MRID-2024] | open-critical |
| ES-SUP-05-Q07 | REE SIMEL 对独立 BESS 的送出/吸收计量字段、质量码、估算标志、时间戳、保留期和项目可见权限是什么？ | 双向有功概念和受限访问已确认；逐字段字典和项目授权未公开。[S-REE-SIMEL-FAQ-STORAGE-2026][S-MITECO-2025-ISP] | open-critical |
| ES-SUP-05-Q08 | REE 私有 BRP 结算 ZIP 的 2025 发布批次、预闭算/闭算版本、修订注释和保留期如何取得？ | 文件角色和 BRP 受限入口已确认；项目文件和访问期未确认。[S-REE-LIQ-ACCESS-2026][S-REE-LIQ-GUIDE-2024] | open-critical |
| ES-SUP-05-Q09 | 2025 年 3 月 30 日/10 月 26 日的每个公开市场、平衡、计量和结算文件是否使用 92/100 个 15 分钟位置、重复本地小时或其他编号？ | 年度日历和 P.O.10.5 缺失估算逻辑已确认；数据集逐项表示未确认。[S-REE-DST-2025][S-MITECO-2025-ISP][S-REE-ESIOS-API-2026] | open-critical |
| ES-SUP-05-Q10 | 2026-09-01 遥测修订、96 轮连续日内上线和 EDI/MoP 后续版本实际发布后，哪些字段从未来变为当前？ | 官方生效/计划边界已记录；截至访问日尚无可用于本基准的完整实际运行证据。[S-CNMC-2026-RT][S-SP-OMIE-INST4-2026][S-ENTSOE-MOP-ROADMAP-2026] | open-critical |

## 9. 资料来源与检查记录

### 9.1 本 SUP-05 新增/使用的主要来源

来源机构、标题、日期/生效关系、URL、访问日和 API/条款定位已登记在 [sources.md](sources.md) 的 **SUP-05 数据接口、版本与权限来源**部分。主要来源包括：

- REE/eSIOS：REData API、Indicator API、Archive API、2025 DST 日历、公共下载入口；
- OMIE：公开文件格式 v1.37、PDBC 公共归档目录、市场公共文件目录；
- REE/CNMC/BOE：P.O.10.x 计量/缺失处理、P.O.9.2 未来实时信息修订、结算和 SIMEL 权限页面；
- ENTSO-E：Transparency Platform Manual of Procedures、Query Response、EDI Library 和 MoP roadmap。

### 9.2 交付检查

- [x] 只修改 `countries/ES/` 下 SUP-05 授权文件；未修改 `model/`、`src/`、`tests/`、`outputs/`、`data/raw/` 或项目模型状态。
- [x] 每项核心结论均分为 F/I/A/U，并带有唯一 `S-*` source ID。
- [x] 记录数据日期、交付日期、发布日期/发行日期和访问日期的区别。
- [x] 明确记录 CET/CEST、本地 23/25 小时日、15 分钟/小时/日聚合及 2026 96 轮边界。
- [x] 明确区分公开 API/文件、注册/API key、BRP/SIMEL 私有数据和项目级可见性。
- [x] 保留 indicator ID、单位、历史完整性、修订标志、项目 crosswalk 和 2026 后接口状态的 `open/open-critical` 问题。
- [x] 未下载原始时序，未形成策略、收益、MILP、代码、回测或预测输入。
