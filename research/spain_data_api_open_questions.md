# 西班牙数据接口待确认问题（ES-DATA-01）

访问核验日：**2026-09-05（Europe/Madrid）**。本文件专门记录仍不能由当前一方资料完全闭合的事项；问题未关闭前不得把单位、最终性或项目级含义写入采集口径。REE/eSIOS key 已从 `data/API_Key.md` 读取并验证，ENTSO-E token 仍未申请/读取。

## 1. 高优先级问题

| q_id | 数据项/问题 | 当前证据和状态 | 影响 | 关闭条件/最小验证 |
|---|---|---|---|---|
| `ES-DATA-Q01` | aFRR 容量需求上调/下调的正式 eSIOS indicator ID 是否为 630/631？ | 官方 indicator search/metadata 已确认 630/631 名称分别为上调/下调需求；2025-07—2026-07 按月请求全部 HTTP 200。单位文本为 `Potencia`，最终性仍未闭合。 | 仍需确认 SI 单位、修订和发布时间才能进入严格结算回测。 | 核对逐指标单位/发布延迟/最终标志，并与规则的 14:45 时限分开记录。 |
| `ES-DATA-Q02` | aFRR 激活能量量的正式 indicator ID、方向和单位是否为候选 680/681？ | 官方 indicator search/metadata 已确认 680/681 名称分别为上调/下调激活能量；历史请求可返回 QH values。单位文本为 `Energía`，底层结算映射仍未闭合。 | 将 682/683误作激活量会导致容量/能量收益重复或漏计。 | 核对能量单位、方向和缺失规则，并与 QH 总量/结算文件对照。 |
| `ES-DATA-Q03` | 682/683 的官方 API `magnitud`、返回值是否是 aFRR 能量价格而非结算金额？ | 元数据分别返回 `Precio de energía de regulación secundaria a subir/bajar`，`magnitud=Precio €/MWh`；2025-07—2026-07 历史请求可返回 QH values。 | 价格类型与最终结算/CBMP映射仍需区分。 | 核对 release/finality 和与激活量的结算连接。 |
| `ES-DATA-Q04` | 不平衡价格的正式 indicator ID（候选 763/764）及单价/双价、上/下方向是什么？ | 官方 indicator search/metadata 已确认 763/764 为上调/下调测量偏差价格，`magnitud=Precio €/MWh`；历史请求可返回 QH values。P.O.14.4 单/双价和 BRP 结算映射仍未闭合。 | 不能把公开系统指标直接当作 BRP 最终结算价。 | 继续核对 Archive taxonomy、ISP、revision/final 标记及 `PDESV` 文件含义。 |
| `ES-DATA-Q05` | eSIOS 指标是否整月可请求，是否存在空值、重发或版本？ | 2025-07—2026-07 共 481 个按月请求全部 HTTP 200；处理结果和原始响应已保存。P48 有 76 个空值月份请求，`values_updated_at`/最终性仍未统一。 | 可进行系统级历史分析，但不能宣称所有技术序列连续或最终化。 | 建立逐指标缺口、发布时间和 revision/finality 审计；空值不插值。 |
| `ES-DATA-Q06` | eSIOS 指标的公开层级是系统汇总、BSP/UP还是私有结算？ | SRS/公开下载说明系统/市场级结果存在；BRP项目结算和 participant 细节可能私有；逐指标权限未确认。 | 公开价格不等于独立储能项目的中标、激活或结算收入。 | 通过指标 `geos`/taxonomy 和 eSIOS download权限实测；把 public aggregate 与 private participant data 分开登记。 |
| `ES-DATA-Q07` | eSIOS 14:45/约30分钟规则发布时间是否等于 API 实际发布延迟？ | SRS guide为规则发布时间；CNMC披露材料给容量/RR约30分钟要求；API没有统一 SLA。 | 预测/决策回测可能错误使用事后修订值。 | 为每次请求保存 publication_date、`values_updated_at`、HTTP时间和实际首次出现时间；按数据日期建立 release-lag 分布，不能用规则时限代替实测。 |
| `ES-DATA-Q08` | eSIOS provisional/final/revision 语义是否有统一字段？ | API示例有 `values_updated_at`；Archive有 `publication_date`；未找到统一 final/revision schema。 | 无法区分决策输入、临时值和最终结算值。 | 找到逐指标字典/版本字段；若无统一字段，按各 archive 文件版本和更新时间维护 provisional/final 状态，并在数据字典显式注明。 |
| `ES-DATA-Q24` | ENTSO-E A75 的 REST/FMS 是否能实际返回/下载 2026-08-01—31 西班牙技术聚合数据，记录是否完整？ | 官方 A75 数据项、R3 抽取和 Spain 区域已确认；REST/FMS 需要 token，本轮未申请或读取 token，未保存 2026-08 文件。 | 目前只能证明“有官方数据项和接口”，不能声称 2026-08 已可下载或无缺失。 | 按官方流程取得个人 REST/FMS 权限后，按月或逐日请求 A75；保存 HTTP 状态、文件名、首尾 UTC、记录数、缺失计数和 SHA-256，不保存 token。 |
| `ES-DATA-Q25` | ENTSO-E 对 Spain A75 的值是 public grid aggregated real-time set points 且不更新；能否作为 measured/settlement actual 的代理？ | 官方 A75 页面明示 Spain-specific 语义；A75仍被定义为按市场时段和技术的 actual net generation。 | 该序列可能适合系统级曲线和交叉核对，但不能未经验证称项目计量、结算或不平衡实际值。 | 与 REE/eSIOS 的公开测量/结算序列（在有权限时）按技术、区域和 QH 对比；在结果前保留 `setpoint_proxy` 标签。 |
| `ES-DATA-Q26` | REST 请求的 `resolution=PT15M` 是否被服务端接受，返回是否确实是 PT15M？ | R3规范列出 PT15M/PT30M/PT60M；旧 generation dependency table也列这些分辨率；无 token未执行 API请求。 | 若服务端忽略参数或按默认分辨率返回，15分钟回测会出现时间聚合错误。 | 用 A75 请求检查 XML/CSV 的 `ResolutionCode`、每 UTC 日记录数和 DST日；以服务端返回为准，不仅依据请求参数。 |
| `ES-DATA-Q27` | A75 的 `B25 Energy storage` 是否在西班牙 2026-08 返回，储能充电/放电符号及与发电聚合的关系是什么？ | ENTSO-E PsrType代码表确认 B25 名称；本轮无 Spain A75 response。 | 将储能计入发电或忽略抽水/充电可能造成系统出力和储能收益双计。 | 分别查询/读取 B25 和所有相关 PSR 类型，核对 `ActualGenerationOutput[MW]` 符号、ProductionType、AreaType和元数据；未证实前不填入国家采集字段。 |
| `ES-DATA-Q28` | Spain EIC `10YES-REE------0` 在 A75 请求中应使用 BZN、CTA还是 CTY；各区域是否重复覆盖？ | 官方 Area/EIC 列表将该 EIC映射到 `BZN\|ES`、`CTA\|ES`、`LFA/LFB/MBA/SCA`；AreaType是不同层级。 | 选错 area type 会把国家、控制区和市场平衡区混合或重复计量。 | 有 token后分别以官方允许的 area parameter 查询，记录 AreaTypeCode、AreaDisplayName、时间记录数；选定一种层级并把选择写入 manifest。 |
| `ES-DATA-Q29` | A75 R3 monthly CSV 的 2026-08 文件名、FMS保留范围和可追溯版本字段是什么？ | File Library帮助页确认 monthly CSV、抽取名和 FMS下载机制；本轮未登录 FMS、未看到具体 2026-08文件。 | 无法判断整月文件是否已经生成、重发或可回溯历史版本。 | 通过 FMS 列出目标抽取，记录文件名、`lastUpdateTimestamp`（如提供）、大小和哈希；重发另存 retrieval batch，不覆盖旧文件。 |

## 2. 负荷和实际发电问题

| q_id | 数据项/问题 | 当前证据和状态 | 影响 | 关闭条件/最小验证 |
|---|---|---|---|---|
| `ES-DATA-Q09` | eSIOS `1293 Demanda real` 的正式元数据、默认区域和历史是否可用？ | 元数据确认 1293 为 `Demanda real`、`magnitud=Potencia`、geo 为 Península；2025-07—2026-07 返回 38,016 个 QH 点，保留本地/UTC时间。SI单位和最终性仍未闭合。 | 负荷基准仍需明确 Península 与 national 的边界。 | 继续核对单位、修订和与 REE 5-minute 实时页面的日合计。 |
| `ES-DATA-Q10` | REData `estructura-generacion` 的 `time_trunc=hour` 是否返回真实逐小时数据？返回值单位是 GWh、MWh还是平均 MW？ | 本轮公开小窗口实测：2026-08 `time_trunc=hour` HTTP 400；`time_trunc=day` HTTP成功但 `magnitude=null`。因此当前没有可解释的逐小时值；页面仍显示 GWh 和 provisional/definitive 提示。 | “出力曲线”与“发电量”可能被混为一谈；当前失败响应不能支撑小时回测。 | 待 REE修复或提供替代 widget 后重试，读取 `magnitude`、单位、values和technology labels，并验证小时记录与页面日合计；在此之前使用 ENTSO-E A75 作为候选替代。 |
| `ES-DATA-Q11` | REData页面的 provisional/definitive 标记如何在 JSON/API 中表达？ | 页面说明无下划线日期为 definitive；API文档示例只有 `last-update`和cache。 | 历史回测不能知道使用的是临时还是最终数据。 | 请求含不同状态日期的 JSON/CSV/XLSX，核对 response字段或页面标志；若 JSON没有标志，保存页面状态元数据并标注解释。 |
| `ES-DATA-Q12` | REData national 与 peninsular `geo_limit` 的正式 geo_id、技术分类和外岛覆盖是什么？ | API文档给允许值及需要 `geo_ids`，但动态表没有在本研究复制完整 geo_id。 | 可能重复统计 national/peninsular，或漏掉 Canarias/Baleares。 | 从 API geo表/响应读取 geo_id；分别请求 national、peninsular、Canarias、Baleares，记录技术集合和单位。 |
| `ES-DATA-Q13` | P48 71–105、10008–10257 的每个 indicator 当前单位、区域、符号和历史可用范围是否稳定？ | 本轮已读取 71–94 元数据并下载 2025-07—2026-07；名称均为 `Generación programada`，`magnitud=Energía`、QH，但部分技术月份为空。10008+汇总指标尚未逐项下载。 | 发电、抽水、互联净额和总计划可能被相加两次，且单位/符号仍可能错。 | 继续核对 95–105、10008+汇总与技术分项关系，保留版本和制度断点。 |
| `ES-DATA-Q14` | eSIOS P48计划的 public archive/download 文件名、修订和最终状态是什么？ | eSIOS archive路由已确认，P48 ID已确认；目标 archive taxonomy未盘点。 | API序列可能无法重建当时可见的计划版本。 | `date_type=datos`和`publicacion`各查 2026-08，按 taxonomy列出 archive，下载一个小样本并比对 indicator response。 |
| `ES-DATA-Q30` | REData失败后，REE/eSIOS 是否另有公开且历史可取的按技术实际发电 15分钟/小时指标？ | REData widget 当前 hour=400、day=`magnitude=null`；REE实时页面仅明确 5分钟可视化；本轮未找到可替代的已闭合 eSIOS actual-generation indicator。 | 若 ENTSO-E A75 的 setpoint语义不满足项目需要，仍需官方 measured actual 来源。 | 向 REE/eSIOS support 请求官方指标名/ID和历史权限；在闭合前，目录中的可下载替代限定为 ENTSO-E A75，REData只作失败记录。 |

## 3. OMIE 文件和时间问题

| q_id | 数据项/问题 | 当前证据和状态 | 影响 | 关闭条件/最小验证 |
|---|---|---|---|---|
| `ES-DATA-Q15` | OMIE `marginalpdbc`/`marginalpibc`/`precios_pibcic` 2026文件的实际 period 数、列分隔、编码和小数格式是否与 v3.1完全一致？ | 官方 v3.1格式给字段和 EUR/MWh；目录证明整月文件存在；本次未保存原始文件。 | 固定宽度解析、15分钟映射和价格小数可能出错。 | 下载 2026-08-01、08-31各一个文件，记录 header、period计数（正常日96、DST日需另测）、列数和 SHA-256；不能用 PDF示例的 1–100替代实测。 |
| `ES-DATA-Q16` | OMIE 文件的正式/临时/重发布版本如何表示？目录“Modified”是否为发行时间？ | 目录有文件大小和 Modified；规范区分发行/交付字段但没有统一 final flag。 | 重发文件可能覆盖历史，回测无法复现原始决策信息。 | 记录文件名、HTTP headers、Modified/Fecha Emisión、抓取时间和哈希；在同名重发时以新 retrieval batch保存，不覆盖旧文件。 |
| `ES-DATA-Q17` | DA、IDA、IDC 的本地 market day、Europe/Madrid DST和 period/QH 的精确映射是什么？ | OMIE制度/格式和 eSIOS API分别定义本地日/offset；跨源 mapping未逐样本核对。 | DST重复小时或跨日交付会错位；不能用固定 24×4。 | 选冬/夏转换日同时下载 OMIE与eSIOS样本，按 UTC、offset、delivery date和原始 period建立 crosswalk。 |
| `ES-DATA-Q18` | IDC `MedioES/PT/MO` 与 round-level weighted price 的关系、零成交空文件和交易量字段怎么处理？ | 官方格式确认 max/min/weighted per period；页面确认按合约统计；round文件另有目录。 | VWAP可能被错误重新平均；空 session会被误判缺失。 | 同一交付日对比 `precios_pibcic`、`precios_pibcic_ronda`和 volume file；记录 zero-trade/18-byte 文件为业务状态。 |
| `ES-DATA-Q19` | OMIE公开仓库六年滚动范围和 2026-08之外的历史补档是否持续？ | File access页面说明最近六个滚动年度；旧文件需 Assistance Portal。 | 2025以前回测不能默认可直接下载。 | 以要回测的起止日逐年检查目录；缺失时保存 Assistance Portal 请求/回复，不把二手镜像当官方原始。 |

## 4. 认证、安全与工程问题

| q_id | 问题 | 当前状态 | 关闭条件 |
|---|---|---|---|
| `ES-DATA-Q20` | eSIOS token 的申请、配额、速率限制和可并发窗口是什么？ | 官方首页仅确认 personal token及申请邮箱；配额/限流未给。 | 通过官方邮箱取得 token 后，向 REE确认配额；将 token放环境密钥管理，不进入 Git、manifest、日志或文档。 |
| `ES-DATA-Q21` | eSIOS是否允许把公开 indicator response缓存到项目的 `data/raw/ES`？ | 本轮已保存 481 个脱敏公开响应及 `.meta.json`；请求头和 token 未保存。是否存在资源级下载/缓存限制仍需以 REE 条款核对。 | 仅保存公开 response、请求参数、时间、状态、哈希；任何 private/BSP数据需另行授权。 |
| `ES-DATA-Q22` | REData/OMIE是否有单次日期窗口、robots/CDN、文件大小或临时 HTTP错误？ | 通用接口/目录已可访问；没有做整月下载或压力测试。 | 采集器需要分日/分小时策略与重试，否则可能遗漏。 | 先以单日、再以整月小窗口测试；保存 HTTP 状态、响应长度、Retry-After（如有）和失败清单。 |
| `ES-DATA-Q23` | 2026-08公开文件/接口是否会在 2026-09-04 后被重发或删除？ | OMIE目录显示文件已发布；REE/eSIOS final/republication未确认。 | 可复现性和数据版本管理风险。 | 建立 immutable retrieval batch；任何修订另存新文件/manifest，禁止覆盖原始文件。 |

## 5. 不应在本阶段做出的假设

1. 虽已通过官方 search/metadata 确认 `630/631`、`680/681`、`763/764`，仍不得跳过单位、区域、修订和最终性核验。
2. 不把 632/633/634（容量分配/容量价）当作激活能量量或能量价；不把 682/683（能量价格）当作激活电量。
3. 不把 eSIOS 通用 `time_trunc=fifteen_minutes` 自动解释成每个指标均有连续、原生且最终化的 15 分钟历史数据；本轮缺口仍需单独登记。
4. 不把 REData `time_trunc=hour` 解释成 MW 出力；本轮该请求 HTTP 400、day响应 `magnitude=null`，不能用失败/空单位响应推导小时值。
5. 不把 `values_updated_at`、`last-update`、文件 Modified 或 `publication_date`自动标成 final。
6. 不把 national、peninsular、Iberian bidding zone、系统汇总和 BSP/UP 项目数据混成一个区域层级。
7. 不把 2025-03-18 前的 IDA/IDC、2025-10-01 前的 DA 插值序列称为原生 15 分钟。
8. 不把 ENTSO-E A75 的 Spain setpoint/no-update 序列称为项目电表、结算 actual 或不平衡结算量；不在无响应证据时假定 B25 storage有值。
9. 不把 A75 数据项页、抽取规范或 Spain EIC 映射单独当作 2026-08 文件已存在的证明；需 REST/FMS 实测。

## 6. 下一步建议（凭据获得后）

1. 对已确认 ID 继续逐项读取单位/区域/状态元数据，并核对 2025 制度切点。
2. 对 2025-07—2026-07 的已下载数据建立缺口、发布时间和 revision/finality 审计；不把 token写入文件。
3. 按 ENTSO-E官方流程申请 REST/FMS权限，查询 A75/A16/A01；记录 `ResolutionCode`、`AreaTypeCode`、`ProductionType`、`ActualGenerationOutput[MW]`、`UpdateTime(UTC)`及响应/文件哈希。
4. 在有权限时对 ENTSO-E BZN/CTA/CTY和 B25 做最小对照，并与 REE/eSIOS measured/settlement序列核对；未核对前保持 setpoint proxy标签。
5. REData 仅保留失败/控制记录；待REE修复 HTTP 400或给出明确替代 widget 后再重试，不用 day响应推导小时出力。
6. 先保存 OMIE 2026-08-01与08-31小样本并验证 period/DST/重发逻辑，再批量下载整月；原始文件不可覆盖。
