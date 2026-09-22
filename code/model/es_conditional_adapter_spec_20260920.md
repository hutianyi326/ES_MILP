# 西班牙条件性历史回测适配规格

**版本**：2026-09-20（设计稿，Astra/medium 独立二审通过）  
**状态**：`design_review_passed__implementation_in_progress`；不代表代码已完成，也不代表已获得正式回测或建模批准。  
**适用对象**：独立储能的事后完美信息毛收益上限研究。  
**本文件的边界**：只规定真实历史数据进入既有 MILP/rolling/C 压力诊断框架前的适配、校验、情景和审计口径；本阶段不写入 `data/raw/`，不运行收益，不改变国家规则。

## 1. 已批准范围与三层内容

### 1.1 范围

纳入：

- 日前市场（DA）；
- 日内竞价市场（IDA1、IDA2、IDA3）；
- aFRR 容量（上调、下调）；
- aFRR 激活电量及其激活价格（上调、下调）。

不纳入：连续日内市场、FCR、mFRR、失衡结算、辅助服务之外的费用、真实 BSP 个体报价、实际激活顺序。连续日内市场即使在原始资料中存在，也不得作为本适配器的交易输入。

### 1.2 规则事实、研究解释、建模假设

| 层级 | 本规格中的处理 |
|---|---|
| 规则事实 | 由 REE/eSIOS、OMIE、BOE 等一方资料直接支持，例如指标单位、官方产品时段和 BOE 的结算公式。 |
| 研究解释 | 将系统层面的已激活电量与已分配容量相除，构造单站点可用的激活比例代理；它不是某个储能站的实际激活记录。 |
| 建模假设 | 680/681 暂按 MWh，632/633 按 MW；激活时间采用 start/end 两种敏感性；容量时间表采用 old/new 两种敏感性；不补缺、不裁剪异常、不猜测激活顺序。 |

已批准的条件假设可以进入研究输入，不要求再次取得官方证明。仅未被证据或本规格明确假设覆盖的字段歧义、缺失、冲突进入`unresolved`并排除；禁止以通用“时间未核实”重新阻断C01–C05研究。

## 2. 内部数据契约

适配器的输出是一个带 provenance 的 `HistoricalConditionalInput`。它可以转换为既有 `QHInput`、`ContractInput` 和滚动订单，但不得伪造 `ES_SYNTHETIC_MARKET_` 前缀绕过合成数据门禁。建议内部结构如下。

### 2.1 `QHRecord`

每个记录代表一个 15 分钟交付区间，至少包含：

| 字段 | 单位/格式 | 要求 |
|---|---|---|
| `qh_id` | 稳定字符串 | 由交付开始 UTC 及分辨率生成，不能随场景改名。 |
| `start_utc`, `end_utc` | ISO-8601 UTC | `end-start=15 min`；不得重叠。 |
| `local_start`, `local_end` | Europe/Madrid | 仅用于本地日、Madrid 年和事件审计；保留 CET/CEST 偏移及 DST fold。 |
| `madrid_date`, `madrid_year` | 日期/整数 | 必须由 Europe/Madrid 转换得到，不能由固定 96 个 QH 推出。 |
| `segment_id` | 字符串 | 连续且无缺口的一段；缺口两侧不可共享 SOC 状态。 |
| `alpha_up`, `alpha_down` | `[0,1]` | 从 680/632 和 681/633 计算，见第 7 节；不裁剪、不填零。 |
| `spot_prices` | EUR/MWh | DA、各适用 IDA 价格按合同保存，不把多会话价格压成一个未知来源的价格。 |
| `capacity_prices` | EUR/MW/QH | 上/下调分开，原字段方向不能交换。 |
| `activation_prices` | EUR/MWh | 上/下调分开，保留负号。 |
| `event_times` | UTC + 原始本地时间 | 区分原始发布时间、名义 gate/result 和场景映射时间。 |
| `quality/status` | 枚举 | 至少包括 `explicit`、`cancelled`、`unknown_missing`、`invalid`、`unresolved`。 |
| `source_ref` | 路径、哈希、批次 | 能追溯到原始文件、指标 ID、原始时间戳和转换版本。 |

### 2.2 `ContractRecord`

DA/IDA 的决策对象不是孤立 QH，而是一个有明确交付边界的原始合同：

```text
contract_id
market = DA | IDA1 | IDA2 | IDA3
source_contract_id / session_id
gate_close_utc
result_release_utc
delivery_start_utc / delivery_end_utc
period_granularity = hourly | qh | other_confirmed
price_eur_per_mwh
side = buy | sell
quantity_mwh and/or quantity_mw
qh_weights (duration-conserving mapping)
status = awarded | not_awarded | cancelled | unknown
raw_timestamp / issued_at / data_date
rule_version / source_ref / record_hash
```

`qh_weights` 只用于结算和功率换算，不能把一个小时合同拆成四个相互独立的交易决策。滚动窗口跨界时可以产生结算用的 QH shard，但所有 shard 必须保留同一个 `source_contract_id` 和原合同义务。

### 2.3 `EventRecord`

事件至少有四类字段：

- `raw_timestamp`：文件中实际出现的原始时间戳，永不覆盖；
- `nominal_event_local/utc`：由规则时间表推导的名义 gate/result；
- `actual_event_utc`：只有来源明确给出时才填；
- `mapping_scenario`：start 或 end。

缺少实际发布时间时只能使用名义事件时间进行场景建模，不能把名义时间写成实际 REE 发布时刻。

## 3. 八个模型输入 eSIOS 指标

本项目此前将“八个 aFRR 指标”定义为 632、633、634、2130、680、681、682、683。630/631 是保留备用需求，列为可选诊断字段，不进入本阶段八输入的共同掩码。原始目录中出现十个相关指标时，必须按此区分，不能把指标数量误写成八个。

| ID | 原字段/含义 | 方向 | 原始单位 | 模型角色 | 当前状态 |
|---:|---|---|---|---|---|
| 632 | aFRR up allocated reserve | 上调 | MW，15 分钟 | 上调容量基数 (R^{up}) | 必需 |
| 633 | aFRR down allocated reserve | 下调 | MW，15 分钟 | 下调容量基数 (R^{down}) | 必需 |
| 634 | aFRR down capacity price | 下调 | EUR/MW，15 分钟 | 下调容量收入价格 | 必需 |
| 2130 | aFRR up capacity price | 上调 | EUR/MW，15 分钟 | 上调容量收入价格 | 必需 |
| 680 | up activated energy | 上调 | 暂按 MWh | 上调激活量代理分子 | 必需、条件性单位 |
| 681 | down activated energy | 下调 | 暂按 MWh | 下调激活量代理分子 | 必需、条件性单位 |
| 682 | up activated energy price | 上调 | EUR/MWh | 上调激活结算价格 | 必需 |
| 683 | down activated energy price | 下调 | EUR/MWh | 下调激活结算价格 | 必需 |

补充字段：

- 630：up reserve requirement，MW；
- 631：down reserve requirement，MW。

630/631 可用于覆盖和合理性诊断，但除非另有批准，不改变 alpha 或优化约束。

重要的字段方向约定：2130 是**上调容量价**，634 是**下调容量价**；682 是**上调激活价**，683 是**下调激活价**。不能按指标编号顺序把 634/2130 或 682/683 的方向对调。

## 4. OMIE 交易字段

### 4.1 公共时间和版本字段

OMIE 文件进入内部结构前至少保存：

`delivery_date`、`period`、`local_time`、`utc_time`、`utc_offset`、`dst_fold`、`period_granularity`、`issued_at`、`data_date`、原始文件哈希和市场版本。

时间转换必须由 Europe/Madrid 时区库完成；不能假设每天固定 96 个 QH。文件标签中的 `period_granularity` 曾出现不一致时，以日期、交付期、官方版本边界和明确的 UTC 映射共同校验，不能盲信标签。

### 4.2 DA

主要字段：

- `MarginalES` 或对应官方价格字段：EUR/MWh，保留负价；
- 成交/计划数量：MWh；如需换算功率，使用实际交付时长；
- 买卖方向：`buy` 与 `sell` 分列，不通过“充电应为负”这类直觉自动反转；
- 交付日期、时段和版本边界：必须随合同保存。

历史版本敏感性：2025-01-01—2025-03-17 为小时产品；2025-03-18—2025-09-30 仍按小时交付；2025-10-01 交付起采用 15 分钟 DA MTU。小时合同不得在本适配器中猜测拆为四个独立决策。

### 4.3 IDA

分别保存 `IDA1`、`IDA2`、`IDA3` 的：

- 会话/合同 ID；
- 成交价 EUR/MWh；
- 成交量/计划量 MWh 及可确认的功率 MW；
- gate close、result release、delivery start/end；
- 买卖方向、取消状态、原始版本和数据发布时间。

IDA1/2/3 是三个独立竞价会话。2025-03-18 生产/2025-03-19 交付起的 QH 产品版本边界必须记录；此前版本按官方字段原样保留。IDA3 的适用交付范围（当前工作只使用其明确的有效范围）不能扩展到文件未覆盖的 QH。

### 4.4 不使用的 OMIE 字段

UOF、near-marginal proxy 和连续 ID 的字段不是本阶段交易输入。`merge_spot_data.py`、`extend_near_marginal_proxy.py` 的结果只能作为诊断或后续专题数据，不能冒充 OMIE 官方成交价或真实 BSP 价格。

## 5. 价格方向与独立结算

### 5.1 原始价格

所有价格以原始符号输入，负价格不取绝对值、不截断为零。容量价单位为 EUR/MW；激活价单位为 EUR/MWh；容量结算不再乘以 0.25，除非输入字段明确是 EUR/MW·h 而非本规格确认的 EUR/MW/15min 产品。

### 5.2 条件性现金代理

根据 BOE-A-2025-13076，P.O.14.4 §§7.1–7.2 的上/下调激活结算方向分别对应：

```text
up_activation_cash  =  + ESECS × PMSECS
down_activation_cash =  - ESECB × PMSECB
```

其中 `ESECS/ESECB` 表示上/下调激活电量，`PMSECS/PMSECB` 表示相应激活价格。下调负号来自BSP付款义务，不等于本站一定充电；负的原始价格仍保留。容量项按“MW × EUR/MW”结算，不重复乘0.25。

这些是系统价格和系统激活量代理。它们不是已确认的独立储能 BSP 均价或逐站结算单。若运行标签没有明确写出该代理，结果不得称为真实站点收益。

## 6. 时间、名义事件与四类数据情景

### 6.1 标准时间轴

所有模型时间使用 UTC；Madrid 年、年度 EFC 和本地交易事件使用 `Europe/Madrid` 转换。每个 QH 必须满足：

```text
end_utc - start_utc = 15 minutes
start_utc < end_utc
```

不跨越 DST 重复/缺失时段造成重叠；23/24/25 小时本地日按实际时区日处理。

### 6.2 激活时间场景

由于 680/681 的历史时间戳与交付区间关联仍未完全证实，定义两个明确场景：

1. `ts_start`：原始激活时间戳解释为 QH 起点，交付区间为 `[t, t+15min)`；
2. `ts_end`：原始激活时间戳解释为 QH 终点，交付区间为 `[t-15min, t)`。

两者都保存原始 `raw_timestamp`，只产生派生映射。不能把 end 场景改写原始文件，也不能把一套时间解释混用于 numerator、denominator 和事件掩码。

逐字段映射固定为以下条件假设，并写入manifest（不代表已核官方时义）：632、633、634、2130在两种情景均按原UTC标签为交付起点；680、681在ts_start原标签不动，在ts_end减15分钟；682、683与相应激活能量采用相同映射，以保持同一原记录周期的能量和价格关联。这不是把所有指标一起平移，分母必须按新交付起点重新匹配，alpha重新计算。该敏感性测试的是能量及能量价相对容量/现货的区间关联，不穷尽所有潜在时间语义。

OMIE按原交付日期、小时/QH序号及已审解析器映射，不随激活情景平移。DA交付2025-10-01前为小时、其后QH；IDA交付2025-03-19前为小时、其后QH。IDA3交付为当地12:00至24:00（旧小时13–24），其他时段不要求IDA3数据。模型交易量是变量，不要求公开价格文件包含本站实际成交量。

名义现货事件条件假设（非actual）：DA为交付D日前一日12:00 gate、12:45 result；IDA1为D-1日15:00/15:20；IDA2为D-1日22:00/22:20；IDA3为D日10:00/10:20。均按Europe/Madrid该事件日转换UTC。使用正常时表，不模拟未取得日志的延迟；manifest登记`event_mode=nominal_no_delay`及`actual_event_utc=null`，不能宣称实际市场均按时完成。各时刻作为本研究明确的事件假设接受审核，不等待官方逐日事件日志。

### 6.3 容量时间表场景

定义两个名义时间表：

| 场景 | gate（Madrid 本地时间） | result release（Madrid 本地时间） | 含义 |
|---|---:|---:|---|
| `cap_old` | 16:00 | 16:30 | BOE/P.O. 的旧时刻假设 |
| `cap_new` | 17:00 | 17:30 | 新附件的时刻假设，条件性适用 |

转换到 UTC 时必须使用当日 CET/CEST 偏移。实际历史切换日（2025-06-27 至 2026-08-31 区间）仍未证实，因此 `cap_old/cap_new` 是敏感性场景，不得写成实际切换记录。每条事件保留 `capacity_timetable_effective_date`（未知时为 null）、`source` 和 `implementation_boundary_status=blocked`。

这两个时间表只改变容量 gate/result 的名义可见性和冻结边界，不改变原始成交价、交付时间或激活量。

容量事件均为交付D日前一日。旧版另有PDVP发布后75分钟的相对报价时间条件，新版另有区域无功容量分配后30分钟条件，容量结果还关联报价关闭后30分钟。当前没有对应逐日延迟日志，两个情景均明确采用正常名义时刻（`nominal_no_delay`），不模拟这些相对延迟分支、不生成actual时间。这是简化假设，不是删除规则中的分支。

### 6.4 四类数据情景

数据情景是时间解释的笛卡尔积：

```text
D01 = ts_start + cap_old
D02 = ts_start + cap_new
D03 = ts_end   + cap_old
D04 = ts_end   + cap_new
```

每个场景必须重新计算合同边界、alpha、完整掩码、连续段、EFC 预算和 manifest hash，不能只改一个标签。

## 7. 激活比例与共同有效掩码

### 7.1 激活比例

在 C01/C02 条件性假设下，若 `Δ=0.25 h`：

```text
alpha_up   = E680_MWh / (R632_MW × Δ)
alpha_down = E681_MWh / (R633_MW × Δ)
```

这表示系统激活电量相对于系统已分配容量的比例，再作为单站点激活代理。它不是实测站点控制轨迹，也不证明站点属于同一激活池。

### 7.2 严格校验

以下任一情况都必须拒绝该 QH：

- 8 个 eSIOS 模型输入、所需 OMIE 合同或事件字段缺失；
- 数值非有限、单位未确认或方向未确认；
- 632/633 分母为零；
- `alpha_up < 0`、`alpha_down < 0`、任一 alpha 大于 1；
- `alpha_up + alpha_down > 1`；
- 激活场景与 UTC QH 映射不唯一；
- 价格或合同交付边界不完整；
- 取消、未知缺失或版本冲突无法区分。

不允许 clip、normalize、zero-fill 或用后续 QH 补前一 QH。极小但正的 alpha 必须保留；只有精确零才可记录为零。未提交的零量记录不延长有效承诺尾部。

### 7.3 `valid_qh_mask_s`

对每个数据情景 `s`，共同有效掩码定义为：

```text
valid_qh_mask_s(q) =
    all_8_esios_explicit(q)
  ∧ all_required_omie_contracts_complete(q)
  ∧ contract_boundary_complete(q)
  ∧ finite_and_unit_checked(q)
  ∧ alpha_conditions(q)
  ∧ event_mapping_consistent_s(q)
  ∧ no_unknown_or_conflicting_required_input(q)
```

`cancelled`会话仅移除该会话交易合同，不因已审取消切断其他市场可用QH，也不补零价。`all_required_omie_contracts_complete`允许明确取消或交付范围外的会话不提供合同；未知缺失仍切段。存在价格却又登记取消必须报冲突，不自动选择其一。

比较四个场景时先取`AND_s(valid_qh_mask_s)`，再迭代移除不完整合同残片至闭包、重切连续段、重算共同覆盖年度预算，并在共同口径上分别重优化。不能从各自覆盖的旧收益中裁取共同QH并相减。分别保留自身覆盖和共同覆盖结果，不以交集掩盖数据损失。

## 8. 连续区间、合同边界与年度预算

### 8.1 区间

将同一场景中按 UTC 排序、无缺口、无重叠且每步恰为 15 分钟的 QH 建为 `segment_id`。缺口两侧不能共享 SOC 或承诺。每一段的首末 SOC 约束按既有模型配置（默认首末 10 MWh），但诊断本身不得偷偷裁剪 SOC 或加入恢复动作。

### 8.2 完整合同条件

一个 QH 只有在其所属 DA/IDA 原始合同的全部必要交付映射可解释、状态明确且不跨未知缺口时，才可进入 `valid_qh_mask`。不得把小时合同拆成四个独立订单；不得用缺失的四分之一价格继续交易。滚动窗口可以保留合同义务的结算切片，但 `contract_id/source_contract_id` 和原始数量必须一致。窗口外尚未释放、但对当前窗口有交付义务的合同，必须显式 carry 或按审定的 QH shard 转换，不得静默截断。

### 8.3 EFC 年度预算

按 Europe/Madrid 本地日计算有效小时数 `H_y`，考虑 23/24/25 小时日。用户已批准的年度上限为 600 次完整循环，按有效研究时段覆盖天数折算：

```text
有效日当量_y = sum(每个Madrid当地日纳入小时数 / 该当地日实际小时数)
B_y^{cycles} = 600 × 有效日当量_y / 该自然年天数
```

实际实现应明确区分循环预算和吞吐量预算：使用已确认的 180 MWh 可用电量，完整循环等价吞吐量为 `2 × 180 = 360 MWh`，并约束 `EFC_y = throughput_y / 360 MWh <= B_y^{cycles}`。如采用既有 core 的 `effective_annual_efc_budget`，必须在 manifest 记录使用的分子、分母和 23/24/25 小时处理。所有连续段共享同一 `madrid_year` 预算，不能每个 segment、每个 rolling window 重新获得 600 次。

完整23小时或25小时当地日均计1个有效日；部分日按该日实际长度折算，禁止以全年总有效小时/全年总小时替代此定义。输入`annual_efc_budget`使用该派生上限，既有核心不得再次按覆盖比例重复缩减。

预算覆盖基线充放电和激活电量；不能只统计容量中标量。跨年时按实际 Madrid 年分开约束，SOC 状态仍按真实时间传递或因缺口切断。

## 9. 十六类运行配置

完整笛卡尔积为：

```text
4 个数据情景
× 2 个视野：joint_full、rolling7
× 2 个固定顺序：U、D
= 16 类
```

推荐 `scenario_id`：

```text
<data_scenario>__<view>__<order>
例如 ts_start__cap_old__joint_full__U
```

### 9.1 `joint_full`

- 在该报告口径的全部合格连续段上联合优化，同年度共享预算；最长单段仅作阶段试算，不代替全范围联合模型；
- 年度预算为跨所有 segment 的全局预算；
- 采用事后完美信息价格和激活代理，仅表示理论毛收益上限；
- 不因压力诊断结果修改主路径订单、EFC 或现金账本。

### 9.2 `rolling7`

- 以 Europe/Madrid 本地日为窗口，窗口长度 7 个本地日；
- 订单按 gate、result release 和 freeze 时点逐步冻结；
- pending 与已 awarded 状态必须保留；
- 跨窗口合同义务按原合同保留，不允许重复结算或静默截尾；
- 第 8 日的新交易不得进入第 1—7 日 snapshot，但已在 gate 前形成的有效义务可按合同规则 carry。
- `new_order_allowed` 的边界按 `event_time >= segment_start` 实现；不得把已过 gate 的 D-1/窗口初始订单平移到窗口内来制造可交易性。
- 若首个窗口开始时没有可继承的初始承诺，首日 DA/aFRR 可能为零；这是 rolling 视野的信息边界损失，必须披露，不能用事后信息补建订单。
- `joint_full` 和 `rolling7` 必须使用同一套 gate 解释和同一套可见性边界；不能为使两种视野可比而分别放宽首日 gate。

### 9.3 顺序和收益标签

`U`、`D` 是固定的激活/压力重放顺序，不是概率，也不是模型在 U 与 D 中择优。每类单独报告现金账本、SOC、循环、覆盖率、求解状态和 gap。输出必须带：

```text
input_scope = historical_conditional
perfect_information_override = true
weight_kind = fixed_order_no_probability
pressure_feedback = false
settlement_scope = gross_only
fees_included = false
```

## 10. Manifest 与 provenance

### 10.1 顶层 manifest

每次运行必须有不可变 manifest，至少包括：

```text
run_id
scenario_id / data_scenario / view / order
input_scope = historical_conditional
adapter_version / design_version
model_config_hash / source_code_hash
source_file_paths + SHA-256
raw_batch_id / retrieved_at
target_start_utc / target_end_utc
timezone = Europe/Madrid / tzdata version
qh_hash / contract_hash / mask_hash / segment_hash
assumption_ids = C01..C05
capacity_timetable_rule / implementation_boundary_status
activation_timestamp_rule
budget_definition / per_madrid_year_budget
solver / status / mip_gap / time_limit
```

### 10.2 行级 provenance

每个输入值保留：原始路径、文件哈希、指标 ID/原字段名、原始时间戳、映射后的 QH 起止、原始单位、转换单位、符号方向、数据情景、合同 ID、排除原因（如有）。衍生 alpha 必须同时保存 680/681 与 632/633 的值和公式版本。

### 10.3 运行状态

仅允许以下审计状态：

`conditional_pass`、`conditional_fail`、`not_run`、`environment_gate_failed`、`input_gate_failed`、`solver_infeasible`、`solver_time_limit_feasible`、`solver_gap_unproven`。

不得使用 `formal_approved`、`official_revenue` 或“真实可执行收益”。

## 11. 最小验证测试

### 11.1 字段和单位

- 632/633 识别为 MW；634/2130 为容量 EUR/MW；680/681 暂按 MWh；682/683 为 EUR/MWh；
- 2130/634 和 682/683 的上/下调方向不交换；
- 负价保留，容量不重复乘 0.25；
- 已登记C01能量单位及公开价格代理允许研究；未登记的单位/方向矛盾或缺失才`input_gate_failed`。

### 11.2 时间

- UTC QH 起止严格 15 分钟；Madrid 转换正确处理 DST；
- start/end 激活映射只改变派生区间，不覆盖 raw timestamp；
- old/new 容量时间表只改变名义事件时间；
- 不把 nominal gate/result 写成 actual publish time；
- 每个场景重新生成 mask、segment、budget 和 hash。

### 11.3 数据质量和合同

- 缺失、取消、未知状态三者区分；不补零、不填后值；
- 非有限、零分母、负 alpha、alpha>1、alpha 总和>1 均拒绝；正 tiny alpha 保留；
- 小时合同不能变成四个独立决策；合同边界缺失会切段；
- 已知的小时合同通常不跨 Madrid 午夜；若它在研究首段或 rolling 窗口边界被截断，应收缩研究区间或保留同一原合同的 carry/shard，不能把各片段当成独立决策；
- IDA1/2/3 会话独立，IDA3 只在明确范围内使用；
- common mask 的比较不会伪装成每个场景的自身覆盖率。

### 11.4 预算和模型转换

- 同一年多个 segment 共用年度预算；
- 23/24/25 小时 Madrid 日换算正确；跨年预算不混合；
- QH、合同、gate、release 可无损转为既有 core 输入；
- 100 MW/180 MWh、单向效率 92%、SOC 边界等设备参数来自已批准配置，不被适配器覆盖。

### 11.5 rolling、结算和回归

- gate 等于 pulse start 的边界；submitted_at 存在时还必须不晚于 pulse；
- pending/awarded/frozen 不丢失；跨窗口不重复现金，不静默截断；
- 第 8 日早 gate 的新订单不进入前一窗口；
- DA、IDA、容量、激活现金分项核对；下调激活采用负现金方向；
- 末端价值不自动转为现金；
- 压力失败不改主路径收益、主路径 EFC 或账本；
- 输入和输出 hash 能复现相同快照。

## 12. 短区间试算顺序

试算区间必须按数据完整性选择，不按高收益选择。至少准备以下四类候选：

1. 一个 DA、所需 IDA、八项 aFRR 和完整合同边界均明确的 1 日区间；
2. 一个至少8个当地日的区间检验完整7天视野与次日滚动；另用2—3日短尾检验pending/awarded和日间结转；
3. 一个包含 DST 23/24/25 小时边界的区间；
4. 一个含真实缺口或取消记录的区间，用于验证切段和不补值。

首日试算须额外记录：首日开始前已过 gate 的历史订单是否存在、是否被允许继承、以及因没有初始承诺而被置零的项目。任何缺失的初始承诺都只能作为视野边界结果披露，不能通过移动 gate 或使用交付后数据修复。

执行顺序：

```text
字段/单位/时区单元测试
→ 1 日 adapter + 结算手算
→ 2—3 日 rolling 跨窗
→ DST 区间
→ 最长单一连续段
→ 16 类完整矩阵
```

每一步先通过 input gate 和 review 再进入下一步。短区间输出只作为条件性管线验证，不可外推为年度收益，也不得在缺失区间人工补齐后再宣称连续覆盖。

## 13. 未解决事项与停止条件

以下事项在本规格中明确保留，不得通过代码猜测：

- 680/681 的历史时间戳到底表示 QH start 还是 end；
- 2025-06-27—2026-08-31 实际容量时间表切换日；
- 系统激活量/容量与目标储能站实际激活池的可比性；
- eSIOS 历史批次的完整发布/修订状态；
- OMIE 某些版本的字段粒度与实际发布时间；
- 真实 BSP 个体容量价和激活价与系统指标价格的差异；
- 历史激活的站内上下调先后顺序。

上述未知在C01–C05及本规格显式条件假设范围内不再阻断研究。仅未被覆盖的歧义、矛盾或必要记录缺失导致`input_gate_failed`/`unknown_missing`；不能把真实站内顺序、个体价格差异或未取得发布日志再次列为普遍停止条件。超出已登记假设的新选择须主线程处理并更新版本。

## 14. 实现交接清单

review 通过后，代码实现必须按以下顺序进行：

1. 建立只读 raw adapter 和版本化 processed 输出；
2. 实现单位、字段、时间、状态、合同边界和 alpha 校验；
3. 生成四个数据情景的独立 mask/segment/budget；
4. 转换为带 `historical_conditional` 标签的 core/rolling 输入；
5. 先做短区间结算手算，再做 1 日、跨窗、DST 试算；
6. 通过逐项验证后，才运行 16 类矩阵并提交完整 review。

任何实现都不得改变 `countries/ES/` 的研究事实、覆盖 `data/raw/` 原文件，或用合成 run ID 绕过真实输入门禁。

## 15. 资料定位

本规格依据项目中已审核的本地资料，关键定位如下：

- `project/spain_conditional_backtest_authorization_20260920.md`：授权边界、C01–C05、16 类矩阵；
- `project/spain_conditional_backtest_implementation_plan_20260920.md`：适配器、完整合同、rolling 跨窗及验证顺序；
- `project/esios_indicator_browser_evidence_20260920.md`：632/633/680/681 单位及时段的现有证据及其历史映射限制；
- `countries/ES/data_catalog_and_version_timeline.md`、`spot_data_catalog_and_version_timeline.md`：eSIOS/OMIE 字段、版本边界和覆盖资料；
- `countries/ES/historical_capacity_timetable_followup_20260920.md`：old 16:00/16:30、new 17:00/17:30 及实际切换日阻塞状态；
- `countries/ES/imbalance_settlement_rules.md` §6：已审同向结算来源；
- `project/es_conditional_price_crosscheck_20260920.md`：已独立复核的字段方向、单位和价格来源交叉核验；
- BOE-A-2025-13076，P.O.14.4 §§7.1–7.2、P.O.14.4 §§17.1–17.2：上/下调激活及容量结算方向/单位，URL：<https://www.boe.es/buscar/doc.php?id=BOE-A-2025-13076>，访问日期 2026-09-20；
- `src/es_synthetic_market/core.py`、`rolling.py`：既有 QH、合同、EFC、rolling 输入接口和已知跨窗边界。

设计审核记录：`project/review_ES_CONDITIONAL_ADAPTER_SPEC_20260920.md`，P0/P1/P2 均为 0；审核结论为允许进入适配器实现，但真实收益运行仍需代码 review 和后续门禁。

### 资料限制

上述资料仍不能证明历史每条 eSIOS 记录的真实发布时间、实际容量时间表切换日或某独立储能站的实际激活轨迹。因此本文件及未来输出必须持续使用“条件性历史代理/事后理论上限”措辞。
