# 西班牙晚间日前电价分析基线（ES-SP-PRICE-01）

> 状态：`conditional_price_setter_identification_pending_historical_crosswalk_and_calibration`（已完成技术层面的 official-setter ground truth、UOF 样本解析、条件性 NM 诊断和样本合并；但 UO→technology 历史适用性仍为 CONDITIONAL，故尚未完成“定价机组”确认，也未通过代理指标正式校准门禁）。
>
> 确认记录：2026-09-04，用户确认本基线的时间窗口、校准边界、95% near-marginal 首版口径和先样本后完整期的阶段门禁。
>
> 2026-09-05 独立 review agent 验收：第 1 步（UOF 月包下载与晚间校准窗口清洗）`PASS（限定校准窗口）`；第 2 步（UO→technology crosswalk）`CONDITIONAL`。候选表和历史活动审计已完成，但当前 `LISTA_UNIDADES.PDF` 为 2026-09-04 现行版本，未证明 2025 历史适用性；不得进入正式 NM 校准。详见 `project/review_ES_SP_CROSSWALK_HISTORICAL_AUDIT_2026-09-05.md`。
>
> 2026-09-05 补充路径：取得 Internet Archive 对 OMIE 官方 `LISTA_UNIDADES.PDF` 的 2025-09-11 快照（文件内部发行时间 2025-09-10），并与当前清单比较；1,023 个样本 UO 在两个快照中技术大类一致。该副本仅作辅助历史证据，不能替代 OMIE 直接历史导出，故第 2 步仍为 `CONDITIONAL`。详见 `project/review_ES_SP_CROSSWALK_ARCHIVE_2026-09-05.md`。

> 2026-09-05 用户确认在历史 crosswalk 暂无更好渠道的情况下继续执行 NM 校准。已完成 308 个晚间小时的条件性 `NM_MW`、`NMShare`、precision、recall、F1 和窗口/阈值敏感性计算；结果状态为 `CONDITIONAL_DIAGNOSTIC_COMPLETE`，详见 `project/review_ES_SP_NM_CALIBRATION_2026-09-05.md`。

> 2026-09-05 已执行第四步条件性数据合并：将 NM 小时表与 `Spain_Combined_Data.xlsx` 的负荷、技术出力、跨区交易，以及 REE eSIOS 负荷和 763/764 不平衡价格对齐；308/308 小时一对一合并通过。Combined 日前价格与 OMIE 官方价格有 5 个小时不一致，已保留两列并以 OMIE 官方价格作为 NM 基准。详见 `project/review_ES_SP_DATA_MERGE_2026-09-05.md`。
>
> 2026-09-05 独立 review agent 对第四步复核结论为 `CONDITIONAL`（不是 `BLOCKED`）：308/308 键唯一，15 分钟覆盖和派生公式均通过。当时记录的电池空字段、跨区符号和 1293 分辨率均已在 2026-09-06 复核更新中处理；历史 crosswalk 仍为 CONDITIONAL。
>
> 2026-09-06 复核更新：用户确认样本期储能尚未装机，新增 `battery_consumption_research_mw=0` 研究字段，原始空值列保留。跨区字段根据 2025-01-02 中午负值/晚间正值，并结合 REE P48 10237 进口正值、10238 出口负值，采用“正值=净进口、负值=净出口”，即 `net_export_mw=-cross_border_trading_mw`。1293 的“五分钟”已确认是原生分辨率，API 15 分钟请求返回的是 5 分钟值的平均聚合；详见第四步 review 报告。
>
> 2026-09-06 更新后的 review agent 复核仍为 `CONDITIONAL`；10237/10238 的核对样本已保存至 `data/raw/ES/esios/2025-01/20260906T_crossborder_sign_audit/`，以便独立复现。
>
> 2026-09-06 用户补充：`Combined` 日前价格来自 Energy Chart 导出的清洗后 15 分钟数据，可能由此前 5 分钟值直接平均得到。该信息作为来源说明和待验证聚合假设记录；在取得原始导出元数据前，仍不替代 OMIE 官方价格。
>
> 二次确认原因：将西班牙原始数据根目录明确固定为 `data/raw/ES`，并重新确认目的、方法、阶段步骤和完整期范围；不改变已通过的样本结果。
>
> 二次确认结果：已确认，允许进入 official setter ground truth 与 UOF 月包解析阶段；尚未授权将未校准结果用于交易策略或收益结论。
>
> 2026-09-05 凭据核验：用户指定的 `Counry\_Investigation` 路径不存在；实际目录中的 `data/raw/ES/REE_Token.txt` 仍为 0 字节。已从 `data/API_Key.md` 的 `## REE APIKey` 段落读取有效 key，官方 eSIOS indicator 1293 返回 HTTP 200，并完成 2025-07—2026-07 的 481 个按月请求；详见 `project/review_ES_ESIOS_TOKEN_2026-09-05.md` 与 `project/review_ES_ESIOS_20250701_20260731_2026-09-05.md`。
>
> 本基线承接“西班牙晚间电价分析”对话，限定为研究、数据校验和代理指标校准；不等同于报价建议、收益承诺、MILP 约束或生产代码授权。

## 0. 西班牙数据目录固定口径

- 项目根目录：`C:\Users\Tianyi\OneDrive\融和元储工作\模型等其他参考资料\Python\Counry_Investigation`。
- 西班牙电价及其原始官方文件统一保存于：`C:\Users\Tianyi\OneDrive\融和元储工作\模型等其他参考资料\Python\Counry_Investigation\data\raw\ES`。
- OMIE 原始文件使用 `data/raw/ES/omie/`；REE REData 原始响应使用 `data/raw/ES/redata/`，REE eSIOS 原始响应使用 `data/raw/ES/esios/`。
- 清洗结果使用 `data/processed/ES/`，质量报告和研究交付物使用 `outputs/ES/` 与 `project/`；原始文件不可覆盖。
- 你消息中的 `Counry\_Investigation` 按当前工作区实际目录解释为 `Counry_Investigation`；不存在另一个 `Counry\_Investigation` 目录。

## 1. 研究目标

回答三个问题：

1. 2025-01-01—2025-03-18，OMIE 公布的日前价格设定技术（official setter）在 19:00—22:00 晚间交付小时如何分布；
2. 出清价附近的已成交卖方报价由哪些技术构成，能否用 `near-marginal` 代理指标解释晚间价格；
3. 2025-03-19 以后，在 OMIE 不再提供可直接按技术识别 95% 边际能量的情况下，是否可以用经校准的报价堆栈代理指标延伸分析。

## 2. 口径冻结（已确认）

### 2.1 时间与区域

- 交付时区：西班牙本地时间（CET/CEST），数据处理保留 `Europe/Madrid` 和原始时段号。
- 晚间窗口：交付小时 `19:00、20:00、21:00、22:00`，即每日电价样本 4 小时。
- OMIE 图表有时按结束小时/报告小时展示。正式提取前必须用一个日期核对“交付小时”与报告 `Hora/Periodo` 的映射；不得把 `19–22` 与 `20–23` 的标签差异静默合并。
- 价格区：西班牙竞价区；保留葡萄牙/法国等跨区标识，用于判断市场耦合和价格分裂。

### 2.2 事实、解释与假设

| 层级 | 本基线口径 |
|---|---|
| F｜规则事实 | OMIE 月报将“价格设定技术”与“以不少于边际价 95% 报价且已成交的能量”分开；后者不表示 setter。OMIE 说明 2025-03-18 启用日前新报价类型，首个受影响交付日为 2025-03-19；日前仍为 24 个小时，日内改为 15 分钟。 |
| I｜研究解释 | 晚间太阳能下降、负荷/残余负荷上升通常与价格上行同向；CCGT 更适合作为边际成本锚的候选，而不是未经校准就称为唯一 setter。水电机会成本、抽蓄和跨区耦合可能使直接 setter 不同于成本锚。 |
| A｜建模假设 | `95%` 是首版 near-marginal 阈值；正价格时优先用 `[0.95P_t, P_t]` 的已成交西班牙相关（`MI/ES`）卖方报价，另做无上界和其他阈值敏感性。零价/负价单独标记，不强行套用乘法窗口。 |
| U｜待确认 | 报价曲线中复杂块、SCO、跨区进出口行的价格含义与“已成交”容量如何映射到技术；UO→technology crosswalk；OMIE 报告小时标签映射；2025-01—03 原始文件的版本/修订完整性。 |

## 3. 阶段任务

### Task 0 — 样本和时间映射验收

- 取 2025-01-02 或其他不含 DST 的日期，核对 `marginalpdbc`、月报图表和 `curva_pbc_uof` 的日期、小时/period、价格和单位。
- 验收 19:00—22:00 是否得到 4 条交付小时记录；检查价格、功率和小数点/分隔符。
- 若样本无法同时还原价格、已成交标志和 UO 标识，暂停完整下载并记录 `U`。
- 2026-09-04 样本验收通过：4 条晚间价格记录已还原，UOF 字段头、`MI/ES/PT` 国家代码、成交标志和西班牙小数格式已核对；详见 `project/review_ES_SP_PRICE_SAMPLE_2026-09-04.md`。

### Task 1 — Official setter ground truth

- 官方来源：OMIE 2025 年 1 月、2 月、3 月月报中的 **“Tecnologías que marcan precio en el mercado diario”**（图 1.8，西班牙区）。
- 期间：`2025-01-01—2025-03-18`，3 月 19 日以后不作为 official setter ground truth。
- 记录方式：multi-label；同一小时出现多技术时各技术均为 1，不强行选 dominant setter。
- 输出：
  `official_setter_20250101_20250318.csv`
  
  字段至少为 `DateTime`、`Hour`、`Hydro_Setter`、`CCGT_Setter`、`PumpedHydro_Setter`、`Wind_Setter`、`SolarPV_Setter`、`RenewCogRes_Setter`、`Nuclear_Setter`、`Other_Setter`、`source_report`。
- 统计：`SetterFrequency_k = SetterHours_k / TotalHours`；multi-label 下各技术频率之和允许超过 100%。
- 2026-09-04 已完成：输出 `data/processed/ES/official_setter_20250101_20250318.csv`，共 1,848 条小时记录；验收见 `project/review_ES_SP_SETTER_20250101_20250318_2026-09-04.md`。

### Task 2 — 下载和解析 OMIE 报价曲线

- 首选官方目录：`curva_pbc_uof_YYYYMM.zip`（2025-01、02、03）。目录当前显示这些月份条目；下载后保留原始压缩包，不覆盖旧版本。
- 解析字段：`Periodo`、`Fecha`、`Pais`、`Unidad`、`Tipo Oferta`、`Potencia Compra/Venta`、`Precio Compra/Venta`、`Ofertada(O)/Casada(C)`、`Tipología de Oferta`。
- 首版筛选：`Tipo Oferta=V`、`Ofertada/Casada=C`；按 OMIE 文件的市场状态保留西班牙相关曲线：市场耦合时 `Pais=MI`（Mibel），市场分裂时使用 `Pais=ES`（西班牙）。`Pais=PT` 和进出口/跨区行保留标记但不直接并入西班牙技术栈。OMIE 文件格式将 `MI` 定义为 Mibel、`ES` 为 España、`PT` 为 Portugal；样本日期 2025-01-02 的 `ES/PT` 行仅在部分分裂时段出现，因此不能静默只保留 `ES`。
- 价格基准：从官方 `marginalpdbc` 取西班牙区 `MarginalES`，而不是从报价曲线反推。
- 2026-09-04 已完成月包下载和晚间子集清洗：输出 `data/processed/ES/omie_uof_sell_matched_20250101_20250318_evening.csv`，共 333,023 行；验收见 `project/review_ES_SP_UOF_20250101_20250318_2026-09-04.md`。

### Task 3 — UO 到 technology crosswalk

- 优先使用 OMIE 官方 UO/生产技术清单或同一数据包中的技术字段。
- 未映射 UO 保留为 `unmapped`/`other`，不得根据单位名称猜测技术。
- 至少区分：`CCGT`、`Hydro`、`PumpedHydro`、`Wind`、`SolarPV`、`Nuclear`、`Coal`、`Cogeneration/Biomass/Waste`、`Interconnection`、`Other`。
- 2026-09-04 已取得 OMIE 当前单位清单并生成候选交叉表（1,495 个样本 UO，1,238 个有明确文本分类）；由于清单为现行版本，历史适用性仍待确认，不作为 2025 ground truth。2026-09-05 新增 `omie_uof_technology_crosswalk_historical_audit_20260905.csv`，记录 1,495 个 UO 在 2025 晚间 UOF 样本中的出现日期、月份和行数；该审计仍将历史技术适用性标记为未确认。

### Task 4 — Near-marginal 代理指标

对正边际价 `P_t > 0`，首版按以下规则计算：

\[
NM_{i,t}=1\{0.95P_t\le p_{i,t}\le P_t\}\,q_{i,t}
\]

其中 `q` 为已成交卖方功率（MW），`p` 为卖方报价（€/MWh）。

按技术聚合：

\[
NM\_MW_{k,t}=\sum_{i\in k}NM_{i,t},\qquad
NMShare_{k,t}=\frac{NM\_MW_{k,t}}{\sum_jNM\_MW_{j,t}}
\]

同时保存绝对 MW 和相对 share。另行运行：

- 仅使用 `p_i >= 0.95P_t` 的无上界版本；
- 90%、92.5%、95%、97.5% 阈值；
- `P_t-5 €/MWh ≤ p_i ≤ P_t` 的绝对价差窗口。

零价和负价时段进入单独的 `price_regime` 分析；不得把 95% 乘法窗口解释为 OMIE 规则。

- 2026-09-05 已完成条件性诊断：输入 308 个晚间小时，输出 `omie_near_marginal_20250101_20250318_evening.csv`（5,360 行明细）、`omie_near_marginal_hourly_20250101_20250318_evening.csv`（308 行小时表）和 `omie_near_marginal_calibration_20250101_20250318_evening.csv`（502 行指标）。当前 crosswalk 版本为 `current_OMIE_LIST_20260904_CONDITIONAL`，不得将结果称为历史官方技术标签。

### Task 5 — 校准和验证

以 Task 1 的 official setter 为 ground truth，按技术和 multi-label 两种方式评估：

- precision、recall、F1；
- top-1 / top-2 技术命中率；
- `NMShare` 阈值（5%、10%、20%、30%）敏感性；
- 90/92.5/95/97.5% 与绝对价差窗口的稳定性；
- 按月份、19/20/21/22 时段、价格 regime 分层。

只有当校准结果通过主线程复核，才允许把 2025-03-19 以后结果命名为 `Near-Marginal Technology Proxy` 或 `Marginal Stack Composition`；不得命名为 `Official Marginal Technology`。

- 本轮结果已完成计算但尚未通过正式校准门禁：CCGT/Hydro/PumpedHydro 在 95% 窗口、`NMShare_all_selected≥5%` 下的 F1 分别为 0.5440、0.7900、0.3602；top-1/top-2 技术集合命中率分别为 60.71%/79.87%。这些数字仅用于条件性诊断。

### Task 6 — 与 Combined 样本合并

与 `data/raw/ES/Spain_Combined_Data.xlsx` 的 `Combined` 样本合并：

- 日前价、负荷、风电、光伏、国内残余负荷、跨境计划交换、各技术出力；其中 Combined 日前价按用户说明来自 Energy Chart 清洗后 15 分钟导出，可能由 5 分钟值平均得到；
- `RL_dom = Load - Wind - Solar`；
- Combined 的 `Cross border electricity trading` 按样本和 REE P48 符号约定为“正值=净进口、负值=净出口”；因此 `NetExport = -CrossBorder`，`RL_adj = RL_dom + NetExport`。
- 商业计划交换与物理潮流分列，不混成同一变量；
- 事后解释可使用实际交换，预测决策输入不得使用最终已实现交换，避免 look-ahead/data leakage。

对话中的相关统计（例如残余负荷与价格的相关性、18:00—21:00 的燃气/水电爬坡）仅作为待复算的探索性结果，不作为官方规则或因果结论。

- 2026-09-05 已完成条件性合并：输出 `data/processed/ES/es_spot_nm_combined_20250101_20250318_evening.csv`（308 行）和质量文件 `data/processed/ES/es_spot_nm_combined_quality_20250101_20250318_evening.json`。Combined 15 分钟输入与 eSIOS 1293 的原生 5 分钟→API 15 分钟平均输入均按四个季度小时聚合到小时，并保留原始口径列和季度小时计数；审查结论为 `CONDITIONAL_PASS`。

### Task 7 — 延伸期

- 校准通过后，将 near-marginal proxy 延伸至 2025-03-19 以后；2025-03-19—09-30 日前价格仍按小时，2025-10-01 起切换到 15 分钟日前 MTU，按版本分别保存。
- 结果文件必须携带 `market_version`、`source_file`、`issued_at`、`data_date`、`retrieved_at`、`timezone`、`price_regime` 和 `crosswalk_version`。

**2026-09-06 条件执行记录：**用户明确要求在无结构性阻断时先按 conditional 口径执行本步。小时段 `2025-03-19—2025-09-30` 已覆盖 784/784 个晚间小时；15 分钟段 `2025-10-01—2026-07-31` 经缺口修复后覆盖 4,000/4,864 个季度小时。2025-10-30 和 2025-11-27 已分别通过 OMIE `.3`、`.2` 修订价格文件补齐；剩余缺口为 2026-06-08—06-30 不在当前七日 UOF 月包内，以及 2026-07 UOF 月包尚未可用。用户指出 UOF 可能延后三个月发布；该解释与 2026-06 包在 9 月初出现的时间模式一致，但尚未作为 OMIE 官方时限确认，因此 2026-07 暂标记为 pending release/availability，不视为结构性阻断。该结果状态仍为 `conditional_proxy_extension_partial`，不代表 Task 5 校准门禁已通过，亦不得命名为 official setter。独立 review 结论为：小时段 `PASS（结构完整）`，15 分钟段 `CONDITIONAL（部分完成）`；数据质量审计通过结构、算术和来源路径检查，仅允许按发布时滞继续追补 UOF，不允许作为完整年度输入进入最终回测或生产建模。审核记录见 `project/review_ES_SP_PROXY_EXTENSION_2026-09-06.md`，缺口审计见 `project/audit_ES_STEP7_GAP_REPAIR_2026-09-06.md`。

### 7.1 UOF 延迟发布的月度追补任务

- UOF 发布时滞事项不作为一次性“完成”项，而作为每月底运行的独立追补任务。
- 每次运行检查 OMIE 官方 `curva_pbc_uof` 目录，下载新出现或修订的月份包，保留不可覆盖的原始版本、获取时间和文件哈希。
- 对新增月份重新解析晚间样本、修补价格/报价缺口、刷新覆盖率和质量审计；缺失文件继续标记为 `pending_release/availability`，不得插值或用代理值填补。
- 任务完成后只更新“数据可用性/覆盖率”状态，不自动改变历史 crosswalk、Task 5 校准门禁或“定价机组已确认”结论。

### 7.2 研究目的纠偏与剩余主线（2026-09-06）

本研究的首要交付不是“把数据表补齐”，而是确认西班牙日前市场在目标时段的**定价机组/定价技术**。截至本记录日，目的尚未完全实现，原因如下：

1. Task 1 已得到 2025-01-01—2025-03-18 的技术层面 official setter ground truth，但月报并不等同于每个时段的 UO/机组级身份。
2. Task 2 已解析 UOF 报价曲线，但历史 UO→technology crosswalk 仍为 `CONDITIONAL`，不能据此把某个 UO 宣称为历史定价机组。
3. Task 4–5 的 `NM_MW`、`NMShare`、precision、recall、F1 目前是条件性诊断；它们只能说明报价堆栈与 official setter 的一致程度，不能替代官方定价机组记录。
4. Task 6 的合并和 Task 7 的延伸是支撑/维护工作，不构成“定价机组已确认”；2025-03-19 以后只能使用明确标注的 proxy。

因此，后续主线调整为：

1. 继续寻找并审核可证明 2025 历史适用性的 UO→technology（必要时 UO→机组）官方映射；在此之前维持 `CONDITIONAL`。
2. 用映射后的 UOF 成交报价回到 2025-01-01—2025-03-18，逐时核对技术标签与报价/机组候选，形成“定价机组确认表”或明确记录无法达到机组级确认的证据边界。
3. 在上述证据基础上重新执行 Task 5 的窗口、阈值、月份、时段和价格 regime 校准，并由主线程审核是否可称为 `Near-Marginal Technology Proxy`。
4. 只有校准通过后，才把 2025-03-19 以后延伸结果用于定价机制分析；UOF 月度任务仅负责补齐数据，不会自动跨过这道门禁。
5. 【2026-09-16 用户确认修订，替代原门禁】定价机组/技术识别及其校准不再作为价格接受者 MILP 的必要前置条件。该研究按自身证据门禁独立推进；未经验证的技术代理指标仍不得作为确定事实或预测输入。日前、日内及 aFRR 的研究型策略与数学建模按 `project/spain_modeling_scope_2026-09-16.md` 单独验收；不平衡仅作为交付偏差的结算接口，不作为独立套利产品。

### 7.3 条件性机制分析执行记录（2026-09-06）

在 calibration review agent 确认指标链路和阈值敏感性均通过、但总体仍受历史 crosswalk 限制后，已按其授权开展明确标注为 `conditional_proxy_mechanism_analysis` 的描述性分析。首版因 P48 `Energía`/15 分钟 MWh 未转换为平均 MW，被 review agent 判定为 `BLOCKED`；现已按 `MWh ÷ 0.25 小时 = 平均 MW` 修复并重新生成，第三次 review agent 复核结论为 `CONDITIONAL`，P48 单位阻塞已解除。修复后分析覆盖 2025-07—2025-09 小时段 368 条，以及 2025-10-01—2026-06-07 15 分钟段 4,000 条；使用 REE eSIOS 1293 负荷、P48 计划出力和 763/764 不平衡价格。该分析不含连续完整跨区交换序列，不做因果或官方定价机组结论。输出和复核材料见 `data/processed/ES/es_proxy_mechanism_*` 与 `project/review_ES_SP_PROXY_MECHANISM_2026-09-06.md`、`project/review_ES_SP_PROXY_MECHANISM_REVIEW_2026-09-06.md`。

## 4. 预期最终数据表

`DateTime | DA_Price_EUR_MWh | Load_MW | RL_dom_MW | NetExport_MW | CCGT_Output_MW | Hydro_Output_MW | PumpedHydro_Output_MW | CCGT_NM_MW | CCGT_NMShare | Hydro_NMShare | PumpedHydro_NMShare | Official_CCGT_Setter | Official_Hydro_Setter | market_version`

## 5. 本轮确认记录

以下事项已于 2026-09-04 确认，作为进入 Task 0 的门禁记录：

1. 晚间窗口是否固定为西班牙本地交付小时 19:00、20:00、21:00、22:00；
2. 是否同意以 2025-01-01—2025-03-18 做 official setter 校准、2025-03-19 以后只使用标明为 proxy 的 near-marginal 指标；
3. 是否同意首版 95% `[0.95P_t, P_t]`、正价单独处理、并行做阈值/绝对价差敏感性；
4. 是否同意在下载完整历史前先通过一个非 DST 日期的样本验收。

确认后状态为 `approved_for_sample`；Task 0 样本通过后，才启动大规模下载和清洗；模型实现仍需后续阶段单独授权。

## 6. 二次确认清单（2026-09-04）

### 主要目的

建立一套可复现的西班牙晚间日前电价形成分析：先用 OMIE 官方披露的 price-setting technology 做 2025-01-01—2025-03-18 的 ground truth，再校准已成交卖方报价的 near-marginal 技术组成，并将通过校准的结果在 2025-03-19 以后明确命名为 proxy，而不是官方 setter。

### 方法

1. 所有西班牙原始文件写入 `data/raw/ES`；清洗结果写入 `data/processed/ES`；质量报告写入 `outputs/ES`；原始文件不覆盖。
2. 交付时间使用 `Europe/Madrid`；晚间窗口固定为 19:00、20:00、21:00、22:00，并保留原始 Period/Hora。
3. 正边际价使用已成交卖方报价的 `[0.95P_t, P_t]` 作为首版 near-marginal 窗口，并行做 90/92.5/95/97.5% 和绝对价差敏感性；零价/负价单独处理。
4. UOF 文件按市场状态保留 `MI`（Mibel）或分裂时的 `ES`（España）；PT、进出口和复杂订单保留标记，不静默并入西班牙技术栈。
5. 未取得官方 UO→technology crosswalk 前，单位保持 `unmapped/other`，不按单位名称猜测技术。

### 后续步骤与门禁

- Task 1：提取 2025-01-01—2025-03-18 月报中的 multi-label official setter。
- Task 2：下载并解析 2025-01、02、03 UOF 月包，保留原始压缩包、版本、哈希和解析质量报告。
- Task 3：取得并审核 UO→technology crosswalk。
- Task 4–5：计算技术级 `NM_MW`/`NMShare`，对 official setter 做 precision、recall、F1 和分层敏感性校准。
- Task 6：与 Combined、负荷、发电、跨区计划交换和不平衡数据合并；事后实际值不得进入预测决策输入。
- Task 7：校准通过后延伸 proxy；2025-10-01 起日前价格按 15 分钟版本处理。

此前 `2025-07-01—2026-07-31` 的 OMIE DA/IDA/IDC 价格已完成下载和清洗，但存在官方 404/空业务文件，均保留为缺口且不插值。REE eSIOS 已取得有效 key、完成小窗口元数据验证并完成完整期公开指标下载；ENTSO-E A75 仍需个人凭据，P48 计划不等同于实际测量出力。
