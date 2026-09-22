# 西班牙回测输入输出规范草案

> 2026-09-20用户后续变更：保留v0.3审核历史，但不得直接作为新运行接口。最新业务基线见 [完美信息两版基线](spain_perfect_information_baseline_20260920.md)。首版不再使用随机场景权重/预测校准窗；费用为“不纳入毛收益”而不是已验证为零；整段版允许全期完美信息、滚动版仅限窗口。新接口及其审核另行登记，完整实施仍未批准。

版本v0.3；2026-09-17；主线程编写，独立review设计层面PASS（P0=0、P1=0、P2=0），待用户参数确认及数据验收。配套[模式与四项设计](spain_backtest_mode_design_draft_2026-09-17.md)、[三轮审核记录](review_ES_BACKTEST_IO_DESIGN_2026-09-17.md)。本文件定义逻辑表，不创建生产配置、数据文件或Excel成品。涉及的公式以该草案B01—B06和原数学v1.2为准。

## 1. 使用规则

必填缺失、未知单位、规则版本未适用、信息权限不符均报错，不静默补0。所有输入分为官方数据F、用户声明U、建模假设H、加工数据D，保留source_id/assumption_id及原始记录引用。价格金额币种EUR。时间运算UTC；本地展示Europe/Madrid，保留偏移和DST fold，不强制每天96个时段。

每个运行有唯一run_id、版本、输入文件hash、规则版本映射、配置hash、场景生成版本和种子封存记录。人工激活样本与真实数据绝不能同列无标记混用。

## 2. 配置和设备表

| 字段 | 类型/单位 | 值/要求 |
|---|---|---|
| run_id / design_version | string | 唯一标识/草案版本 |
| approval_state | enum | draft/user_confirmed/review_pass；草案不能冒充生产许可 |
| start_local / end_exclusive_local | ISO datetime | 请求2025-01-01 00:00至2026-09-01 00:00 |
| timezone | string | Europe/Madrid |
| information_mode | enum | price_known_activation_unknown / price_and_activation_known |
| markets | list | DA、有效IDA场次、aFRR_up/down；IDC必须false |
| activation_source | enum | synthetic_benchmark / calibrated_proxy；不能写site_actual |
| activation_intensity_id | enum | low/mid/high，分别运行 |
| activation_config_version | string | 幅度、转移/分支、模板、全期锚点、权重及批准引用 |
| evaluation_path_id / seed_ref | string | 仅评估/结算侧保存；两者均不可送入模式A优化接口。B只能取得获准窗口路径，不因此取得窗外数据 |
| weight_kind | enum | H01为design_weight；empirical_probability仅校准及审核后可用 |
| lookahead_local_days / execution_local_days | integer | 建议7/1，按当地日边界 |
| annual_cap / year_basis | float / enum | 600 EFC / Madrid_calendar_year |
| partial_year_policy | enum | full_calendar_cap / prorata_covered_days；必须显式 |
| cycle_method / cycle_energy_basis | enum / MWh_DC | dc_total_throughput_div_twice_window / Emax−Emin，本配置180，不硬编码 |
| days_in_year / covered_calendar_days | integer by year | 自然年365或366；当地完整覆盖日数，pro-rata分母不得固定365 |
| terminal_method / terminal_multiplier | enum / float | visible_da_tail_mean / 建议1；最终窗口自动hard10 |
| stress_feedback_to_optimizer | bool | false |
| stress_duration_minutes | list[int] | 候选15/30/60 |
| stress_terminal_lo/hi | MWh_DC | 候选10/190，须批准 |
| power_charge/discharge/grid_import/grid_export | MW_AC | 均100 |
| energy_nameplate/min/max/start/final | MWh_DC | 200/10/190/10/10 |
| eta_charge / eta_discharge | ratio | 0.92/0.92 |
| capacity_limit_up/down / support_limit_up/down | MW | 各100；scope=per_delivery_period，按每q、每方向合计 |
| participation_mode / share | enum / ratio | direct_bsp / 1 |
| new_order_acceptance | ratio | 1，用户研究假设 |
| fees / degradation_cost | 带单位float | 用户确认0，必须记录explicit_zero |
| qualification_claim / verified_by_team | enum / bool | user_confirmed / false（未收到证据） |

数值域：功率非负，0<效率≤1，10≤E≤190，份额1，费用显式零，市场方向支持量整MW；存在未批准H配置时仅允许文档/输入检查，正式收益运行禁用。资产年内投运具体日若无证据，1月1日起可用登记为模拟假设。

## 3. 市场时间、合同与价格

### 3.1 contracts与events

主键contract_id和event_id。每合同：market、session_id、delivery_start_utc、delivery_end_utc、duration_hours、original_resolution、rule_version、source_id。每事件：event_type（offer_open/gate/result/support_initial/support_update）、decision_time_utc、publication_time_utc、contract_id、allowed、reason。

offer_gate≤result_release≤delivery_start；容量结果先于支持决策。不能猜缺失时间；同刻顺序采用模式草案§2规则，官方精度冲突时拒绝。合同到物理网格映射表主键(contract_id,q_id)，weight无量纲，必须满足Σduration_q×weight=contract_duration。小时合同不拆成四个自由日前变量。

交易上限按event、contract、direction给MW，用户上限100；已提交订单不在新决策集合。credit_model=not_modeled，不能声称保证金已验证。首日关门合同禁止新增交易。

### 3.2 prices（实际历史归档）

主键(price_id,version_id)；字段market、session_id、direction、contract_id或delivery_interval、value、original_unit、normalized_unit、conversion_factor、publication_time_utc、retrieved_at、source_id、raw_ref/hash、quality_flag。price_id必须能唯一连接到对应产品。

现货/激活单位EUR/MWh，容量单位EUR/MW/对应容量时段；若原为EUR/MW/hour仅乘该容量时段小时数一次。direction不可省略。负数允许；下调激活原始收付款符号必须映射为M16约定并记录sign_transform，不由价格正负猜。

决策视图decision_prices另加window_id、available_to_model_at、information_override_reason。历史发布时间不因上帝模式被改写；只有明确可见窗口内价格允许override=perfect_price。窗口外价格对两模式均不可见。settlement_prices保留实现版本并按冻结成交/激活复算；不能将窗口估值当结算项。

## 4. 激活情景和信息节点

### 4.1 activation_nodes与activation_steps

nodes主键(tree_version,node_id)，包含parent_node_id、branch_time_utc、conditional_design_weight、weight_kind、observed_at、state、intensity_id、template_id、anchor_utc。H01根权重1，各父节点子设计权重和1，叶scenario_weight为路径设计权重乘积；这定义人工抽样过程，不表示市场经验概率。empirical_probability只能通过另行校准审核的映射输入。观测时刻按实际信号前缀确定，不把隐藏状态生成时刻当作观察时刻。

steps主键(tree_version,leaf_id,step_start_utc)，字段step_end_utc、duration_hours、alpha_up/down、source_kind、assumption_id、source_window。0≤alpha≤1，同子步至多一方向非零；步长候选5分钟。不同叶可共享前缀；叶ID是存储键，不是可观察状态。

H01中signal_publication_at=step_start_utc；发布本步恒定参考系数（包括0），不依赖本站中标。activation_nodes.observed_at必须等于从已发布系数首次可辨认状态的子步开始：块+5分钟隐藏分支对应+15分钟，24/72小时分支对应其开始。不得用branch_time替代尚不可见的observed_at；info_node仅在发布后可分开。当前物理响应可用当前指令，实测电量/现金记账在执行后。此为人工观测协议，不等于真实市场遥测发布规则。

全期评估路径表主键(path_id,step_start_utc)，由独立评估器保存realized_alpha；滚动每日用相同path_id，不重抽过去。模式A只取已经观察的前缀，B可取获准窗口内后缀。所有模式/市场组合共用价格、path_id和强度，初末状态与循环口径一致。

### 4.2 decision_information

主键(window_id,decision_event_id,leaf_id)，字段info_node_id、allowed_price_ids、observed_activation_until、known_activation_until（A只能到已观察时刻）、fixed_state_hash、mode、visible_window_end。节点ID由允许的观测内容生成，不使用未揭示state、leaf_id、未来路径hash或seed。

逐节点检查：同info_node_id的报价/状态变量一致；固定订单相同；时刻尚未到达的实际激活字段不能出现在A决策输入。人工模板一旦被观测推断的可预测性在报告标注，不称为真实信号预测。

场景规模预检记录分支数、叶数、物理步数和估计二元变量数；7当地天跨块/DST可能超729叶，应以实际边界数计算3^n。不允许为提速默默删除非预知或剪掉不利叶；缩减方法需独立批准。内存/求解资源超限则报告design_not_computationally_validated。

## 5. 订单与滚动状态

### 5.1 orders

主键order_id；字段market、contract_id、direction、submitted_at、decision_event_id、status（new/submitted_pending/awarded/delivered/cancelled_with_evidence）、submitted_mw、awarded_mw、price_ref、provider_block_id、capacity_id、support_version、immutable_after。

订单状态迁移仅按事件记录；G仅控制new。pending提交量冻结，beta=1情况下数学预计成交量已确定，但仍按结果事件迁移；不得重复将其计入P_fixed。capacity不同状态按草案B06合成，方向合计上限100。support版本只取适用时刻最新有效版本，历史版本保留审计但不相加。

### 5.2 state_snapshot

主键(run_id,path_id,snapshot_utc)，字段energy_dc_mwh、cycle_used_by_calendar_year、fixed_order_ids、pending_order_ids、capacity_commitments、support_versions、last_observed_activation_time、ledger_checkpoint。每次起点值必须等于前次执行结束值。

cycles明细主键(run_id,path_id,step_start_utc)，字段charge_ac_mwh、discharge_ac_mwh、charge_dc_mwh、discharge_dc_mwh、efc_increment、Madrid_year、cumulative_efc、annual_limit。跨当地年界拆分；不含未执行优化方案，不按窗口重置。缺年初累计量且从年中开始时，需显式批准新模拟假设。

## 6. 输出和账本

| 输出表 | 主键/核心字段 | 说明 |
|---|---|---|
| trades | run/path/order/交付区间 | 申报、成交MW/MWh、价格、方向、提交及结果时间、状态 |
| reserve | run/path/q/direction | 申报/中标/支持MW、可用功率余量，非重复支持版本 |
| operation | run/path/step | B、激活、实际c/p、E前后、SOC、循环增量、限值和误差 |
| cash_ledger | run/path/cash_type/order_or_step/direction | spot/capacity/activation/fee/degradation；有符号EUR、原价格单位、能量/容量基数、唯一键 |
| window_objective | run/path/window | 预计窗口利润、终端系数和非现金估值、目标值、状态、gap、时间；不能跨窗相加称收益 |
| realized_summary | run/path/期间 | 来自唯一现金账本的日月年毛收益，分市场/方向，费用零标记、覆盖率 |
| diagnostic | run/path/snapshot/test_id | 冻结订单hash、扰动时长/方向、首违约、能量/功率/循环缺口、覆盖不足、恢复需求 |
| comparison | mode/组合/path/期间 | 同口径差额、weight_kind、人工过程加权值/样本平均及适用说明；不得标市场概率期望 |
| audit | run/check_id | PASS/FAIL/NOT_RUN及证据 |

账本按完整回测期间只入账一次；预先已成交交易现金按合同交付区间归属展示，但trade_id原成交价格不变，不按日内最新价重估。终端估值不是任何cash_type。期末已冻结而未交付承诺不允许留在评估期外；否则终止完整期结果发布。

Excel为后续交付格式，逐步明细超过单表容量时分工作簿/表，原始审计明细不截断；此处不创建Excel。中文Markdown首页列模式、窗口长度、合成激活、理想成交、费用未扣、数据覆盖、待确认假设和压力失败。

## 7. 现有数据初步盘点（不是全期数据验收）

| 本地证据 | 已知情况 | 尚不能推断 |
|---|---|---|
| `data/processed/ES/omie_quality_20250701_20260731.md` | 记录160608行；DA下载失败2，IDA1失败1且空33，IDA2空3，IDA3空2 | 不代表每产品每合同无缺口；空文件不自动判市场不开市 |
| `data/processed/ES/omie_quality_20260801_20260831.md` | 2026-08记录12336行，字段缺失/重复检查为0 | 不代表业务全覆盖或全部价格单位已验证 |
| `data/processed/ES/esios_quality_20250701_20260731_20260904T231550Z.json`及对应验收 | 有2025-07—2026-07公共aFRR资料 | 不代表本站激活、2025上半年或2026-08aFRR覆盖完整 |
| 2025年初OMIE局部文件/合并工作簿 | 已找到文件线索 | 本轮未打开工作簿或逐行检查，不推断完整性 |

full_requested_period_ready=false。后续每产品建立预期合同格、实际记录格、业务停用证据、缺口及单位验证。先补取或核验，再提出缩短共同连续期间；不拼接断裂片段还假称电量连续。价格、激活和规则共同覆盖是运行门禁。

数据质量状态枚举：verified / missing / duplicate_unresolved / unit_unverified / rule_unverified / synthetic / not_applicable。未知单位停用相应模块；重复时刻先用UTC/偏移/版本去重，禁止平均；负电价保留。插补只能在用户批准的方法和单独标识下进行，不默认许可。

## 8. 验收案例与本轮执行边界

| ID | 输入/操作 | 应有结果 |
|---|---|---|
| IO01 | DC充180、放180；效率0.92 | AC充195.652174、放165.6；EFC=1 |
| IO02 | 只充180DC | EFC=0.5，不称完整循环 |
| IO03 | 已用599.5、未来任一叶0.6 | 该叶违反年度上限；不能用平均值掩盖 |
| IO04 | 2026覆盖243天，选择pro-rata | 600×243/365=399.452055；full方案仍600 |
| IO05 | 同一订单跨两个滚动窗口 | 固定承诺继承，账本只记一次 |
| IO06 | pending买10MW，G=0 | 旧订单保留，新申报为0，P_fixed不得重复含pending |
| IO07 | A两叶未来激活不同、当前历史相同 | 报价相同；B在获准窗口可以不同 |
| IO08 | 末日前均价50、E末100 | s=46，估值4140EUR，只在目标，不入现金账本 |
| IO09 | 最终窗口 | E末10，估值关闭；不可行则报告，不补免费电 |
| IO10 | 压力起点后才提交的补能单 | 不进入该快照诊断；已提交单必须保留 |
| IO11 | E初10、B=0、上调100MW持续15分钟 | 需求电量下降27.173913MWh，诊断失败，不截为成功 |
| IO12 | 春秋DST、跨年 | 时长由UTC算；年度由Madrid分；不固定96点 |
| IO13 | A输入泄露seed/未来leaf标签 | 信息审计FAIL，不能发布模式A收益 |
| IO14 | 激活路径不在经济树中 | out_of_support并停止该路径，不选最近叶 |
| IO15 | 未审核单位/缺规则版本/未批准H参数 | 数据或授权门禁失败，不正式运行 |
| IO16 | 7天窗口跨全期模板块 | 根据全期固定锚点裁切，已发生状态不重抽；块初5分钟闲置，+5分生成状态但到信号可辨认时才揭示；计算实际叶数 |
| IO17 | 两相邻q均申报100MW同方向 | 分别按q检查，通过容量上限；不能错误要求全期合计≤100 |
| IO18 | 模式A决策请求含evaluation_path_id | 接口拒绝；仅评估器保存实现路径标识 |
| IO19 | 模式B到评估期末E不是10 | 与A同样判不可行，不能出售期末留存而抬高B收益 |
| IO20 | 两个实现路径年度已用不同 | 各自快照输入分别校验，不共用累计；更换SOC窗口须重算EFC分母 |
| IO21 | 块+5分钟生成隐藏方向，+15分钟才发布可辨认脉冲 | 模式A在+5/+10分钟仍合并节点，在+15分钟发布后分开；当前响应可跟踪该指令，不能读取更晚信号 |

本轮可手算IO01—04、08、11，其他为后续自动化测试要求；不得因表内列出就标为已运行。无生产代码、MILP求解或收益回测。

## 9. 来源与审批

用户确认：`spain_questionnaire_confirmation_2026-09-17.md`。数学依据：原M01—M21和配套草案B01—B06。官方资料来源沿用`countries/ES/sources.md`，本轮未更改市场规则或发布新法规结论。

输入输出逻辑与数学扩展经review后仍须确认H01—H05、字段级数据质量、场景规模可解性，再另行放行实现；implementation_approved保持false。
