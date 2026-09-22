# 西班牙储能 MILP 两阶段改造方案与 Codex 开发 README

> 版本：v1.0  
> 日期：2026-09-22  
> 适用范围：当前 `es_synthetic_market` / `es_historical_conditional` 西班牙储能联合优化模型  
> 核心市场：DA、IDA1、IDA2、IDA3、aFRR Capacity、aFRR Activation  
> 当前基线内核：`src/es_synthetic_market/_baseline_core.py`，`experimental_a1_a3=False`

---

## 0. 本 README 的目的

当前模型已经具备联合优化的基本骨架：

- DA / IDA 现货净头寸；
- aFRR Up / Down 容量；
- aFRR 激活；
- 电池充放电功率；
- SOC 递推；
- EFC 年度循环约束；
- 现货、容量、激活收益统一进入目标函数。

后续不推倒现有 MILP，而是在现有结构上分两个阶段升级。

### 阶段一：完美历史收益预测（Perfect-History Revenue Benchmark）

目标是得到一个**遵守真实市场决策时序，但仍使用完整历史未来信息**的理论收益基准。

这一阶段继续允许优化器“知道未来”，但必须完成四项 P0 级结构修复：

1. **Rolling Horizon 必须改为 2 日优化 + 1 日执行/冻结，消除最后一天视野缩短与重复结算问题；**
2. **市场承诺必须严格按照各市场 GCT / 结果时序冻结；**
3. **aFRR 容量锁定后，IDA2 / IDA3 必须持续受到 reserve-aware headroom 约束；**
4. **修正滚动窗口 SOC 边界：仅整个回测起点初始化为 10 MWh，中间窗口继承已执行 SOC；普通 rolling window 末端不得强制回到 10 MWh，只有真正回测终点才允许施加 terminal SOC 条件。**

### 阶段二：真实历史数据回测（Realistic Historical Backtest）

在阶段一正确的时间结构之上，逐步取消“完美预知”和“理想成交”等假设，模拟真实交易人在当时信息条件下能实施的策略。

---

# 1. 当前模型：保留什么，不改什么

## 1.1 保留的核心变量体系

当前统一现货净合同变量：

\[
x_j \in [-P^{max}, P^{max}]
\]

其中：

- \(x_j>0\)：卖出；
- \(x_j<0\)：买入；
- \(j\) 表示具体市场合同，可对应 DA / IDA1 / IDA2 / IDA3 及对应交付时段。

为便于开发和日志展示，建议在接口层明确表达为：

\[
x_{DA,q},\quad x_{IDA1,q},\quad x_{IDA2,q},\quad x_{IDA3,q}
\]

但底层仍可继续使用统一 `net_j` 索引。

aFRR 容量变量：

\[
R_q^{up},\quad R_q^{dn}
\]

物理变量：

\[
c_s,\quad p_s,\quad SOC_s,\quad u_s
\]

其中 \(u_s\) 为充放电互斥二元变量。

## 1.2 保留 Up / Down / Idle 子步结构

阶段一不修改当前相位结构：

\[
h_q^{up}=0.25\alpha_q^{up}
\]

\[
h_q^{dn}=0.25\alpha_q^{dn}
\]

\[
h_q^{idle}=0.25(1-\alpha_q^{up}-\alpha_q^{dn})
\]

并保持：

\[
h_q^{up}+h_q^{dn}+h_q^{idle}=0.25
\]

三个 phase 的功率平衡继续为：

\[
p_s-c_s=
\begin{cases}
B_q+R_q^{up}, & up\\
B_q-R_q^{dn}, & down\\
B_q, & idle
\end{cases}
\]

SOC 继续逐 phase 递推：

\[
SOC_s=SOC_{s-1}+\eta_c c_s h_s-\frac{p_s h_s}{\eta_d}
\]

阶段一中，历史 \(\alpha\) 仍作为完全可见的外生输入。

> 注意：`idle` 是 **aFRR no-activation phase**，不是“电池功率为 0”。在 idle phase 中电池仍按现货基线 \(B_q\) 运行。

---

# 2. 两阶段总体架构

| 项目 | 阶段一：完美历史收益预测 | 阶段二：真实历史数据回测 |
|---|---|---|
| 主要目的 | 理论收益 benchmark / upper bound | 模拟真实可执行历史策略 |
| 未来市场价格 | 完全已知 | 仅使用当时可得信息或预测 |
| 未来 \(\alpha\) | 完全已知历史值 | forecast / realized / stress 分离 |
| Rolling Horizon | **2 日规划 + 1 日执行** | 同阶段一 |
| 市场 GCT 冻结 | **必须实施** | 同阶段一 |
| aFRR 后 IDA headroom | **必须实施** | 同阶段一 |
| Spot 成交 | 暂保留理想成交 | 可加入订单成交/深度 |
| aFRR Capacity 成交 | 暂保留申报=中标 | 拆分 bid / award |
| 激活轨迹 | 当前 energy-equivalent phase | 可升级为真实/情景 AGC |
| SOC reserve buffer | 不新增 | 增加 |
| 费用/退化/罚则 | 暂按当前版本 | 完整加入 |
| 风险模型 | 风险中性 | 可加入场景/CVaR |

---

# 3. 阶段一：完美历史收益预测

## 3.1 阶段一目标

阶段一不是“现实交易策略回测”。它的定位是：

\[
\boxed{
\text{Perfect information}
+
\text{Correct market chronology}
+
\text{Correct physical feasibility}
}
\]

即：

- 价格可以提前知道；
- \(\alpha\) 可以提前知道；
- 仍可假设 price taker / full fill；
- 但不能再让已经过 GCT 的市场变量被后续求解重新修改；
- 不能让最后一个正式统计日失去完整 look-ahead；
- 不能让后续 IDA 交易侵占已锁定的 aFRR 容量。

---

# 4. P0-1：重构 Rolling Horizon

## 4.1 当前问题

当前“2 日窗口”如果与输入数据尾部重合，最后一个正式统计日可能没有下一日 look-ahead。

例如正式收益区间只有：

```text
Jan 1 | Jan 2
```

如果 Jan 2 重新求解时没有 Jan 3 数据，则 Jan 2 实际变成 1 日视野。

同时，如果窗口末端被硬约束为：

\[
SOC_{end}=10\text{ MWh}
\]

还会产生明显的 end-of-horizon bias。

## 4.2 阶段一目标结构

统一改为：

\[
\boxed{\text{Planning Horizon}=2\text{ delivery days}}
\]

\[
\boxed{\text{Execution Horizon}=1\text{ delivery day}}
\]

示意：

```text
Window 1
Jan 1 ---------------- Jan 2
████ execute Jan 1 ████
                       Jan 2 = look-ahead

Window 2
                       Jan 2 ---------------- Jan 3
                       ████ execute Jan 2 ████
                                              Jan 3 = look-ahead
```

### 核心原则

- 每次求解优化两天；
- 每次只将第一天的实际执行结果写入正式 ledger；
- 第二天仅作为 look-ahead；
- 下一次滚动时，第二天重新优化，但继承已经在此前市场 GCT 锁定的承诺；
- 所有收益、EFC、SOC 实际状态只按“已执行部分”向前推进；
- 绝不能把 look-ahead 日收益提前计入正式历史收益。

## 4.3 输入长度要求

如果正式回测区间为：

\[
[D_1,D_N]
\]

则至少需要：

\[
[D_1,D_{N+1}]
\]

的数据输入。

即：

\[
\boxed{N\text{ 天正式收益} \Rightarrow N+1\text{ 天市场数据}}
\]

最后额外一天是 look-ahead buffer，不进入正式收益统计。

### 建议行为

如果缺失 \(D_{N+1}\)：

- 默认不计算 \(D_N\) 为“正式可比结果”；
- 输出 `insufficient_lookahead=true`；
- 禁止静默退化为 1 日 horizon；
- 如确需计算，必须显式使用 `allow_partial_terminal_window=true`，并单独标记结果。

## 4.4 P0-D：滚动窗口 SOC 边界与 Terminal SOC 修正

> **本项作为独立 P0 验收项处理。**  
> 当前测试版本存在每个独立连续段起点 / 终点固定为 10 MWh 的约束；在“2 日窗口恰好等于整个回测段”的测试包中，这会表现为每个 2 日窗口末端都被强制拉回 10 MWh。新的 rolling horizon 中必须消除这一窗口级人工终点效应。

### 4.4.1 整个回测起点

只有正式回测的第一个物理时点初始化为：

\[
SOC_{initial}=10\text{ MWh}
\]

除非输入配置显式提供其他初始 SOC。

### 4.4.2 后续 rolling window 起点

不得重新初始化为 10 MWh。

必须继承上一正式执行区间的真实结束状态：

\[
\boxed{
SOC_{D,start}
=
SOC_{D-1,end}^{executed}
}
\]

因此 SOC 是一个跨 rolling window 持续传递的物理状态，而不是每个窗口独立重置的参数。

### 4.4.3 普通 rolling window 末端

阶段一中不得在每一个滚动窗口末端机械施加：

\[
SOC_{window\_end}=10
\]

普通 2 日 planning window 的第二天只是 look-ahead，不代表项目真正终止。

默认仅要求：

\[
SOC_{min}\le SOC_{window\_end}\le SOC_{max}
\]

不得为了数值便利把窗口末端强制回到最低 SOC 或初始 SOC。

### 4.4.4 真正回测终点

只有在整个研究区间真实结束，且用户要求 energy-neutral terminal condition 时，才允许：

\[
SOC_{final}=SOC_{target}
\]

例如：

\[
SOC_{target}=10\text{ MWh}
\]

否则应使用显式配置的 terminal band 或 terminal value。

### 4.4.5 与 2-day planning + 1-day execution 的关系

对于：

```text
Window 1: Jan 1 + Jan 2  → 只执行 Jan 1
Window 2: Jan 2 + Jan 3  → 只执行 Jan 2
```

Window 2 的初始 SOC 必须等于 Window 1 中 **Jan 1 正式执行结束后的 SOC**，而不是等于 Window 1 对 Jan 2 look-ahead 规划出来的某个 SOC，更不能重新设为 10 MWh。

即：

\[
SOC_{Jan2,start}^{Window2}
=
SOC_{Jan1,end}^{executed}
\]

这一状态传递必须来自 executed ledger / physical state，而不是 planned look-ahead state。

### P0-D 验收要求

Codex 必须保证：

- 整个回测仅在第一个正式物理时点初始化 SOC；
- 后续 rolling window 起点继承上一 executed day 的结束 SOC；
- 中间窗口不再被错误当成项目真正结束；
- 普通 rolling window 末端不再强制 `SOC=10 MWh`；
- 只有真正回测终点才允许施加 terminal SOC / terminal value / terminal band；
- 正式收益期最后一天仍具有完整下一日 look-ahead；
- ledger 不重复计算 look-ahead 日收益。

---

# 5. P0-2：按市场 GCT / 结果事件冻结决策

## 5.1 设计原则

阶段一虽然允许完美信息，但仍必须模拟：

\[
\boxed{\text{Decision commitment chronology}}
\]

市场变量不是在跨 rolling window 的后续求解中无限次自由重写。每个市场的决策在其 Gate Closure Time 到达后必须成为不可撤销承诺。

### 阶段一的性能原则：不要求每个 GCT 都重新完整求解一次

阶段一使用 perfect-history 信息集：在一个 2 日规划窗口内，未来价格和历史 \(\alpha\) 已全部可见，因此 DA、IDA1、aFRR、IDA2、IDA3 的 GCT 之间**没有新的信息到达**。为了表达 GCT 的经济约束，不需要机械地在每个 GCT 重新调用一次完整 MILP。

阶段一默认采用：

\[
\boxed{\text{one MILP solve per rolling step}}
\]

并通过以下两种机制体现 GCT：

1. **窗口内事件约束**：用 \(B^{DA},B^{IDA1},B^{IDA2},B^{IDA3}\) 的累计头寸表达不同事件节点的 headroom 和市场承诺顺序；
2. **跨窗口冻结**：进入下一次 rolling solve 时，所有 GCT 已经过去的合同/容量变量通过固定 bounds 继承上一次求解结果，不允许重写。

因此阶段一的含义是：

```text
一次求解决定当前 2 日窗口中的完整 perfect-history 计划
        ↓
按实际 GCT 记录各市场承诺何时生效
        ↓
下一 rolling window 中，已过 GCT 的承诺固定，仍开放的市场变量可以重新优化
```

只有阶段二在引入新的 forecast / realized information flow 后，才需要根据新信息到达时点考虑 event-driven re-optimization。

## 5.2 市场事件顺序

对当前项目使用的 2025 西班牙历史规则切片，开发时使用以下事件顺序：

```text
D-1

12:00        15:00          16:00              22:00
  │             │              │                   │
  ▼             ▼              ▼                   ▼
DA GCT       IDA1 GCT       aFRR GCT            IDA2 GCT
                               │
                            ~16:30
                           aFRR award

D

10:00
  │
  ▼
IDA3 GCT
```

当前模型对应的 IDA delivery scope：

- DA：D 日；
- IDA1：D 日全日；
- IDA2：D 日全日；
- IDA3：D 日 12:00–24:00；
- aFRR Capacity：D 日各 QH。

> **重要：市场时间不得硬编码在求解器。**
>
> 新增 effective-dated `market_calendar` 配置。  
> 2025 历史切片与后续规则版本必须允许不同配置。  
> 后续规则版本可能调整 aFRR GCT，因此求解器必须按 delivery date / rule version 读取对应市场日历。

## 5.3 “冻结什么”的精确定义

### DA GCT

冻结：

\[
x_{DA,q}
\]

后续 IDA / aFRR 求解不得重写已关闭 DA 的决策。

### IDA1 GCT

冻结：

\[
x_{IDA1,q}
\]

此时累计头寸：

\[
B_q^{IDA1}=x_{DA,q}+x_{IDA1,q}
\]

### aFRR GCT

冻结：

\[
R_q^{up},\quad R_q^{dn}
\]

阶段一暂保留：

\[
R^{bid}=R^{award}
\]

即 full-fill。

### IDA2 GCT

冻结：

\[
x_{IDA2,q}
\]

但必须满足已锁定 aFRR commitment。

### IDA3 GCT

冻结：

\[
x_{IDA3,q}
\]

并继续满足 aFRR commitment。

## 5.4 不要错误冻结原始 `charge_s` / `discharge_s`

P0 中需要冻结的是：

- 市场申报 / 成交头寸；
- aFRR 容量承诺；
- 由这些承诺形成的可用 headroom。

不建议在 DA GCT 后直接冻结未来所有：

- `charge_s`
- `discharge_s`

因为后续 IDA 仍然允许调整商业基线。

更准确的关系是：

```text
冻结市场承诺
      ↓
更新累计商业头寸 B
      ↓
重新计算仍开放市场可调整的部分
      ↓
由最终 B + 已冻结 R 推导物理 charge/discharge/SOC
```

只有当一个交付 QH 的所有允许调整市场都已关闭后，该 QH 的最终 baseline / physical schedule 才真正不再通过这些市场改变。

---

# 6. P0-3：把 Headroom 改为事件节点约束

## 6.1 当前需要改造的点

不能只在最终：

\[
B_q=x_{DA}+x_{IDA1}+x_{IDA2}+x_{IDA3}
\]

上检查一次：

\[
B_q+R_q^{up}\le P^{export,max}
\]

\[
-B_q+R_q^{dn}\le P^{import,max}
\]

因为 aFRR Capacity 在 IDA1 之后、IDA2 / IDA3 之前锁定。

## 6.2 新增累计状态

逻辑上显式构造：

\[
B_q^{DA}=x_{DA,q}
\]

\[
B_q^{IDA1}=x_{DA,q}+x_{IDA1,q}
\]

\[
B_q^{IDA2}=x_{DA,q}+x_{IDA1,q}+x_{IDA2,q}
\]

\[
B_q^{IDA3}=x_{DA,q}+x_{IDA1,q}+x_{IDA2,q}+x_{IDA3,q}
\]

### 实现要求：优先作为线性表达式，不新增决策变量族

上述 \(B^m_q\) 是**累计头寸状态/线性表达式**，阶段一不建议为它们额外创建四组连续 decision variables，更不应新增任何 binary/integer 变量。

推荐直接把表达式写入约束矩阵，例如：

\[
(x_{DA,q}+x_{IDA1,q}) + R_q^{up} \le P_q^{export,max}
\]

而不是新建：

\[
B_q^{IDA1}=x_{DA,q}+x_{IDA1,q}
\]

再为 \(B_q^{IDA1}\) 分配单独 solver column。

如果为了日志/审计需要 \(B^{DA},B^{IDA1},B^{IDA2},B^{IDA3}\)，应优先在求解后从 \(x\) 计算并输出，不增加 MILP 变量规模。

## 6.3 aFRR 决策时的约束

在 aFRR GCT：

\[
B_q^{IDA1}+R_q^{up}\le P_q^{export,max}
\]

\[
-B_q^{IDA1}+R_q^{dn}\le P_q^{import,max}
\]

含义：

> aFRR 只能使用当时尚未被 DA + IDA1 基线占用的功率空间。

## 6.4 IDA2 后的约束

aFRR 已经锁定，因此 IDA2 必须满足：

\[
B_q^{IDA2}+R_q^{up}\le P_q^{export,max}
\]

\[
-B_q^{IDA2}+R_q^{dn}\le P_q^{import,max}
\]

后续 IDA2 只能交易：

\[
\text{remaining headroom after locked reserve}
\]

## 6.5 IDA3 后的约束

同样：

\[
B_q^{IDA3}+R_q^{up}\le P_q^{export,max}
\]

\[
-B_q^{IDA3}+R_q^{dn}\le P_q^{import,max}
\]

因此：

\[
\boxed{R\text{ 一旦锁定，后续 IDA 不能侵占该备用能力}}
\]

---

# 7. DA / IDA 跨拍卖价差交易：阶段一继续保留

阶段一允许：

\[
x_{DA}=-100
\]

\[
x_{IDA1}=+100
\]

最终：

\[
B^{IDA1}=0
\]

并获取不同拍卖之间的价格差。

但开发和文档中不要称为“纯金融衍生品套利”。

应统一定义为：

> **Cross-auction offsetting energy positions / 跨拍卖反向电能头寸**

物理 headroom 检查应基于：

\[
B^m
\]

而不是：

\[
\sum |x_m|
\]

例如：

\[
x_{DA}=-100,\quad x_{IDA1}=+100
\]

则：

\[
B^{IDA1}=0
\]

不应被视为占用 200 MW 物理并网能力。

---

# 8. 阶段一：明确不升级的内容

为了避免阶段一范围膨胀，以下内容明确延后到阶段二：

1. 不引入价格预测模型；
2. 不引入 \(\alpha\) 预测模型；
3. 不引入随机场景树；
4. 不引入 CVaR；
5. 不引入成交概率；
6. 不重建 aFRR merit order；
7. 不模拟市场深度与价格冲击；
8. 不增加真实 AGC 高频轨迹；
9. 不增加独立 SOC reserve buffer；
10. 不增加 imbalance penalty；
11. 不增加 aFRR non-delivery penalty；
12. 不增加完整交易费 / aggregator fee / BRP fee；
13. 不改变当前 Up / Down / Idle energy-equivalent activation 结构；
14. 不改变当前历史 \(\alpha\) 完全可见假设。

阶段一的原则是：

\[
\boxed{\text{只修复时序与滚动机制，不同时重写经济假设}}
\]

---

# 9. 阶段一推荐的软件结构改造

以下为开发建议，不要求严格按文件名执行，但职责需要拆清。

```text
src/es_synthetic_market/
│
├── core.py
├── _baseline_core.py
├── rolling.py
├── ledger.py
│
├── market_calendar.py      # NEW
├── event_state.py          # NEW
└── freeze.py               # NEW / optional

src/es_historical_conditional/
├── adapter.py
└── runner.py

config/
└── es_market_calendar.yaml # NEW
```

## 9.1 `market_calendar.py`

职责：

- 根据 delivery date 返回规则版本；
- 构造 DA / IDA1 / aFRR / IDA2 / IDA3 事件；
- 输出：
  - `gate_close_utc`
  - `result_release_utc`
  - `delivery_start_utc`
  - `delivery_end_utc`
  - `eligible_qhs`
  - `market`
  - `rule_version`

禁止在 `_baseline_core.py` 中写死市场时间。

## 9.2 `event_state.py`

建议新增：

```python
class FrozenState:
    as_of_utc
    fixed_net_by_contract
    fixed_reserve_up_by_qh
    fixed_reserve_down_by_qh
    executed_until_utc
    physical_soc_mwh
    efc_used_ytd
```

功能：

- 保存已经过 GCT 的决策；
- 在下一次 MILP 求解时转为固定变量 bounds：
  - `lb = ub = frozen_value`
- 保留跨 rolling window 的承诺。

## 9.3 `_baseline_core.py`

新增能力：

### A. 接收 fixed decisions

例如：

```python
solve_window(
    input,
    fixed_net={...},
    fixed_reserve_up={...},
    fixed_reserve_down={...},
    as_of_utc=...
)
```

### B. 创建 event-specific headroom

不再只有 final headroom。

新增：

- `headroom_at_afrr`
- `headroom_after_ida2`
- `headroom_after_ida3`

### C. 保留当前 SOC / phase 方程

阶段一不修改 activation phase algebra。

## 9.4 `rolling.py`

这是阶段一最主要的改造文件。

需要从“简单窗口切片”升级为：

\[
\boxed{
\text{Rolling horizon}
+
\text{Event-driven freeze}
+
\text{Execution-only settlement}
}
\]

## 9.5 `ledger.py`

必须明确区分：

### Planned

来自 2 日优化窗口的计划收益：

```text
planned_revenue
```

### Executed

仅第一天实际冻结执行的收益：

```text
executed_revenue
```

正式回测汇总只能使用：

```text
executed_revenue
```

禁止把 look-ahead 日重复计入。

---

# 10. 阶段一推荐运行流程

## 10.1 默认：每个 rolling step 只完整求解一次

阶段一不建议按 DA / IDA1 / aFRR / IDA2 / IDA3 五个 GCT 分别重复 solve，因为在 perfect-history 模式下这些事件之间没有新的信息集变化。

推荐流程：

```python
state = initialize_state()

for execution_day in target_days:

    planning_window = [
        execution_day,
        execution_day + 1 day,
    ]

    assert complete_market_data(planning_window)

    # 1. 读取 2 日窗口内的完整历史未来信息
    model_input = build_perfect_information_input(
        planning_window=planning_window,
        prices="historical_realized",
        alpha="historical_realized",
    )

    # 2. 根据绝对 GCT 时间识别：
    #    - 已关闭且从上一窗口继承的 frozen commitments
    #    - 本窗口内仍可规划的 open decisions
    frozen_state = state.commitments_closed_before(
        rolling_solve_time=execution_day.start
    )

    # 3. 一次 MILP 同时包含：
    #    - DA / IDA1 / IDA2 / IDA3 x_j
    #    - aFRR R_up / R_down
    #    - event-specific headroom
    #    - power / SOC / EFC
    solution = solve_window(
        model_input,
        frozen_state=frozen_state,
    )

    # 4. 保存该 2 日窗口计划，但不提前确认 look-ahead P&L
    planned = build_planned_schedule(solution)

    # 5. 仅执行 execution_day
    execution = execute_first_day(
        planned=planned,
        state=state,
    )

    ledger.book(execution)
    state.advance_physical_state(execution)

    # 6. 按真实绝对 GCT，把 execution_day 内已经发生的市场事件
    #    对应计划值晋升为 frozen commitments，供下一 rolling solve 继承。
    state.promote_closed_commitments(
        planned=planned,
        until_utc=execution_day.end,
        market_calendar=market_calendar,
    )

return ledger
```

## 10.2 为什么一次 solve 仍然可以表达 GCT 冻结

阶段一允许未来信息完全可见，因此不需要用“重新求解次数”模拟信息到达。GCT 的作用通过两层表达：

### A. 当前窗口内部

通过 event-specific cumulative position / headroom constraints 表达：

\[
B^{IDA1}+R \rightarrow B^{IDA2}+R \rightarrow B^{IDA3}+R
\]

保证 aFRR commitment 与后续 IDA 调整在同一个 MILP 内满足正确的物理顺序。

### B. 下一 rolling window

如果某一市场 GCT 已经过去，则上一窗口计划中的对应值变成：

```python
lb[j] = frozen_value
ub[j] = frozen_value
```

即后续窗口无法重写历史承诺。

这种实现同时满足：

- perfect-information benchmark；
- GCT commitment chronology；
- 较低的求解次数；
- 跨窗口决策一致性。

## 10.3 什么时候才需要 event-by-event re-solve

以下情形放到阶段二：

- DA 之后产生新的价格预测；
- IDA1 后新的系统状态/预测到达；
- aFRR award 在 result release 后才成为已知；
- 新的 SOC / telemetry / activation realization 到达；
- 真实策略要求“每获得一轮信息就重新优化”。

这时可以升级为：

```text
new information
    ↓
re-optimize remaining open decisions
    ↓
freeze decisions whose GCT has passed
```

但这不属于阶段一 P0 的默认计算路径。

## 10.4 全局事件时间线仍然必须保留

即使阶段一不在每个事件点重新求解，仍必须建立：

```python
global_market_event_timeline
```

并按绝对时间记录：

- gate close；
- result release；
- commitment effective time；
- delivery interval；
- rule version。

原因是：D 日上午的 IDA3 与 D+1 日 DA 等事件会交错，只有统一绝对时间轴才能正确判断哪些承诺在下一 rolling window 中已经冻结。

---

# 11. 阶段一新增输出

## 11.1 `event_decision_ledger`

字段至少包括：

```text
event_time_utc
delivery_day
market
contract_id
qh_id
decision_before
decision_after
frozen_value
is_frozen
```

用途：证明后续求解没有改写早期市场决策。

## 11.2 `position_timeline`

```text
qh_id
B_DA
B_IDA1
reserve_up
reserve_down
B_IDA2
B_IDA3
```

## 11.3 `headroom_audit`

```text
qh_id
event
baseline_mw
reserve_up_mw
reserve_down_mw
export_headroom_mw
import_headroom_mw
constraint_slack_up
constraint_slack_down
```

## 11.4 `rolling_window_audit`

```text
execution_day
planning_start
planning_end
lookahead_complete
executed_start
executed_end
terminal_soc_rule
```

## 11.5 `daily_execution_ledger`

正式历史收益汇总唯一来源。

```text
date
spot_revenue
afrR_capacity_revenue
afrR_activation_revenue
cost
executed_revenue
start_soc
end_soc
efc
```

---

# 12. 阶段一验收标准

## Test P0-ROLL-01：最后一天必须有完整 look-ahead

输入正式收益：

```text
Jan 1 - Jan 2
```

提供数据：

```text
Jan 1 - Jan 3
```

要求：

- Jan 1 求解能看到 Jan 1 + Jan 2；
- Jan 2 求解能看到 Jan 2 + Jan 3；
- Jan 3 收益不能进入正式结果。

## Test P0-ROLL-02：禁止重复结算

如果 Jan 2 在 Jan 1 窗口作为 look-ahead 出现：

- Jan 1 账本不能确认 Jan 2 收益；
- Jan 2 收益只能在 Jan 2 正式 execution 时入账一次。


## Test P0-TERM-01：中间 rolling window 不得强制回到 10 MWh

构造一个 3 日测试集，使 Jan 2 末端保持较高 SOC 对 Jan 3 有明显价值。

要求：

- Window 1 / Window 2 的普通 planning horizon 末端不得出现自动 `SOC=10 MWh` 的硬约束；
- 如果最优解选择窗口末端 SOC 高于 10 MWh，应允许该解存在；
- solver matrix / audit 中不能出现中间窗口对应的 `SOC_end = 10` 固定行。

## Test P0-TERM-02：SOC 必须按 executed state 跨窗口继承

假设 Window 1 正式执行 Jan 1 后：

\[
SOC_{Jan1,end}^{executed}=87\text{ MWh}
\]

则 Window 2 的起点必须满足：

\[
SOC_{Jan2,start}=87\text{ MWh}
\]

不得：

- 重置为 10 MWh；
- 使用 Window 1 对 Jan 2 look-ahead 计划出的 SOC 代替真实 executed SOC。

## Test P0-TERM-03：仅真正回测终点允许 terminal SOC

对于正式回测区间：

```text
Jan 1 - Jan 31
```

要求：

- Jan 1 至 Jan 30 的 rolling planning horizon 末端不施加 `SOC=10 MWh`；
- 如果配置 `final_soc_target_mwh=10`，只在 Jan 31 的真正研究终点生效；
- 如果未配置 final SOC target，则采用配置的 terminal band / terminal value 逻辑。

## Test P0-FREEZE-01：DA 决策不能被 IDA 改写

DA GCT 后记录：

\[
x_{DA,q}=a
\]

在 IDA1 / aFRR / IDA2 / IDA3 后重新检查：

\[
x_{DA,q}=a
\]

必须完全一致。

## Test P0-FREEZE-02：aFRR 决策不能被 IDA2 / IDA3 改写

aFRR GCT 后：

\[
R_q^{up}=r_u,\quad R_q^{dn}=r_d
\]

IDA2 / IDA3 求解后必须保持：

\[
R_q^{up}=r_u,\quad R_q^{dn}=r_d
\]

## Test P0-HR-01：IDA2 不得侵犯已锁定 aFRR

100 MW 电站：

\[
B^{IDA1}=30
\]

\[
R^{up}=70
\]

IDA2 尝试：

\[
x_{IDA2}=20
\]

导致：

\[
B^{IDA2}+R^{up}=120>100
\]

必须判定不可行或限制 IDA2 新增卖出量。

## Test P0-HR-02：反向 DA / IDA 交易按净头寸占用 headroom

\[
x_{DA}=-100
\]

\[
x_{IDA1}=+100
\]

则：

\[
B^{IDA1}=0
\]

不能按 200 MW gross trade 占用并网功率。

## Test P0-SOC-01：phase 时长守恒

每 QH 必须满足：

\[
h^{up}+h^{dn}+h^{idle}=0.25
\]

允许数值容差：

```text
<= 1e-9 h
```

## Test P0-SOC-02：能量恒等

忽略充放跨零和效率用于测试时，应满足：

\[
E_q
=
0.25B_q
+
0.25\alpha_q^{up}R_q^{up}
-
0.25\alpha_q^{dn}R_q^{dn}
\]

与三个 phase 逐段累加结果一致。

## Test P0-CAL-01：市场日历版本化

至少建立两个 fixture：

```text
historical_2025
newer_rule_version
```

确认不同 delivery date 可读取不同 aFRR GCT，而无需修改求解器源码。

---

# 13. 阶段一完成定义（Definition of Done）

- [ ] 2 日规划 + 1 日执行正式落地；
- [ ] 正式回测最后一天始终具有完整下一日 look-ahead；
- [ ] look-ahead 收益不重复结算；
- [ ] 市场 GCT 使用统一 event calendar；
- [ ] DA / IDA / aFRR 已关闭变量能够跨求解冻结；
- [ ] aFRR 后的 IDA2 / IDA3 受到 reserve headroom 约束；
- [ ] market position 与 physical dispatch 分层明确；
- [ ] 仅整个回测起点初始化 SOC，后续窗口起点继承上一 executed day 的结束 SOC；
- [ ] 普通 rolling window 末端不再强制 `SOC=10 MWh`；
- [ ] 只有真正回测终点才允许施加 terminal SOC / terminal band / terminal value；
- [ ] event decision ledger 可完整审计；
- [ ] 所有 P0 单元测试和集成测试通过；
- [ ] 阶段一不新增新的 binary/integer variable families；
- [ ] 累计事件头寸优先使用线性表达式，而非新增 solver columns；
- [ ] frozen decisions 优先通过固定上下界实现，而非额外增加等式行；
- [ ] 完成与旧 baseline 的求解性能回归测试；
- [ ] 阶段一仍保留 perfect price / perfect alpha / full-fill 假设；
- [ ] 输出明确标记 `model_mode=perfect_history_v2`。

---

# 14. 阶段二：真实历史数据回测

## 14.1 阶段二目标

阶段二是在阶段一正确的时间骨架上回答：

> 如果交易员在当时只能看到当时已经公开的信息，并使用当时可生成的预测，他实际可能做出什么决策？

阶段二模型应从：

\[
\text{Perfect Information Optimization}
\]

升级为：

\[
\boxed{\text{As-of Information Backtest}}
\]

---

# 15. 阶段二 P1：信息可得性与非预知约束

## 15.1 新增 `as_of_time`

所有输入必须携带：

```text
available_at_utc
```

求解时间为 \(t\) 时，只能使用：

\[
available\_at\_utc\le t
\]

的数据。

## 15.2 Price 三层结构

拆分：

```text
price_forecast
price_realized
price_settlement
```

### 优化

使用：

```text
price_forecast
```

### 历史结算

使用：

```text
price_realized / settlement
```

禁止在真实回测中把未来实际 ID / aFRR 价格提前送给求解器。

---

# 16. 阶段二 P1：Alpha 三层结构

当前：

\[
\alpha^{realized}
\]

直接进入优化。

阶段二改为：

\[
\boxed{
\alpha^{forecast},
\alpha^{realized},
\alpha^{stress}
}
\]

## 16.1 `alpha_forecast`

优化器可见。

可先从简单方法开始：

- rolling mean；
- hour-of-day conditional mean；
- weekday/weekend；
- month / season；
- reserve requirement 条件；
- system imbalance 条件。

后续再升级机器学习。

## 16.2 `alpha_realized`

真实历史回放与 settlement 使用。

它不能提前进入当时决策。

## 16.3 `alpha_stress`

用于可交付性 / SOC reserve stress。

目的不是预测收益，而是避免：

> 因 expected alpha 很低而把所有 SOC 都拿去做现货，导致真实长时间激活无法交付。

---

# 17. 阶段二 P1：增加 aFRR SOC Reserve Buffer

除 expected activation SOC 外，增加：

\[
SOC_q
\ge
SOC_{min}+E_q^{up,reserve}
\]

以及：

\[
SOC_q
\le
SOC_{max}-E_q^{dn,reserve}
\]

其中：

\[
E_q^{up,reserve}
=
f(R_q^{up},T_q^{up,stress},\eta_d)
\]

\[
E_q^{dn,reserve}
=
f(R_q^{dn},T_q^{dn,stress},\eta_c)
\]

`T_stress` 必须来自后续正式规则研究或经过批准的投资假设，不在代码中写死。

---

# 18. 阶段二 P1：预测与真实执行分离

形成两个对象：

```python
PlannedSchedule
RealizedExecution
```

### PlannedSchedule

由当时：

- price forecast；
- alpha forecast；
- frozen commitments；
- SOC estimate；

共同生成。

### RealizedExecution

使用：

- realized market price；
- realized activation；
- actual SOC transition；

进行回放。

两者差异必须写入：

```text
forecast_error_ledger
```

---

# 19. 阶段二 P2：aFRR bid 与 award 分离

阶段一：

\[
R^{bid}=R^{award}
\]

阶段二至少拆分：

\[
R^{bid}
\]

\[
R^{award}
\]

进一步可增加：

\[
P^{bid}
\]

形成：

```text
Bid Quantity
Bid Price
↓
Market Acceptance
↓
Awarded Capacity
```

然后：

\[
Activation
=
f(R^{award},\alpha^{realized})
\]

而不是继续：

```text
optimizer chooses R
→ automatically fully awarded
```

---

# 20. 阶段二 P2：市场深度与价格冲击

对于规模较大的 BESS，逐步加入：

- market depth；
- marginal stack；
- acceptance probability；
- own-volume price impact。

可先做 scenario / haircut，不要求第一版即重建完整市场曲线。

例如：

```text
award_ratio = 100%
award_ratio = 75%
award_ratio = 50%
```

用于投资敏感性。

---

# 21. 阶段二 P2：真实 Activation Path / AGC Replay

当前：

\[
\alpha\times15min
\]

相当于把 activation energy 转成“满 R MW 等效持续时间”。

这对总能量一致，但不保证真实 QH 内路径。

阶段二可分三层：

### Level A

继续使用当前 energy-equivalent phase。

### Level B

Stress path：

```text
Up → Down → Idle
Down → Up → Idle
Long Up
Long Down
```

检查中间 SOC 极值。

### Level C

如拿到秒级/分钟级信号：

```text
actual AGC replay
```

直接驱动物理模型。

---

# 22. 阶段二 P2：成本、偏差与罚则

逐步进入目标函数：

\[
\max
[
Spot
+
Capacity
+
Activation
-
TradingFee
-
AggregatorFee
-
BRPFee
-
Degradation
-
Imbalance
-
NonDeliveryPenalty
]
\]

至少分别输出：

```text
gross_market_revenue
transaction_cost
degradation_cost
imbalance_cost
non_delivery_penalty
net_operating_revenue
```

不要只输出一个总收益。

---

# 23. 阶段二 P2：风险目标

在确定性 expected-value 模型稳定后，再考虑：

- scenario optimization；
- CVaR；
- chance constraint；
- robust reserve buffer。

不建议在阶段一或阶段二首轮同时加入。

---

# 24. 阶段二验收标准

## Test RB-INFO-01：禁止未来信息泄露

在 `as_of=15:00 D-1` 求解时：

- 不得访问 IDA2 realized price；
- 不得访问 IDA3 realized price；
- 不得访问 delivery-day realized alpha；
- 可以访问当时已经发布的数据和生成的 forecast。

## Test RB-FCST-01：预测与结算分离

修改未来 realized price：

- 不应改变已经冻结的早期历史决策；
- 应改变后续 realized settlement。

## Test RB-ALPHA-01

修改未来 `alpha_realized`：

- 不应改变当时使用 `alpha_forecast` 作出的已冻结决策；
- 应改变 realized SOC / activation revenue。

## Test RB-SOC-01

在 expected alpha 很低、stress alpha 很高的情况下：

- Stage 1 可以出现高 reserve；
- Stage 2 SOC reserve buffer 应限制 reserve，避免不可交付。

## Test RB-AWARD-01

`R_bid=100`、`R_award=60` 时：

- capacity revenue 只能按 60 MW；
- activation 只能基于 60 MW；
- headroom commitment 使用 awarded commitment 的具体规则应在市场规则层配置。

---

# 25. 阶段二完成定义

- [ ] 所有优化输入具有 `available_at_utc`；
- [ ] 真实回测中无 future leakage；
- [ ] price forecast / realized 分离；
- [ ] alpha forecast / realized / stress 分离；
- [ ] forecast decisions 与 realized execution 分离；
- [ ] SOC reserve buffer 已实现；
- [ ] 至少一种 aFRR award haircut / acceptance 模式；
- [ ] 成本与处罚可以配置；
- [ ] 输出 forecast error 与 realized P&L；
- [ ] 保留阶段一结果作为 benchmark；
- [ ] 输出明确标记 `model_mode=realistic_historical_backtest`。

---

# 26. 两阶段最终输出应并列，而不是互相覆盖

最终报告建议同时保存：

| 指标 | Perfect History | Realistic Backtest |
|---|---:|---:|
| Spot Revenue | | |
| aFRR Capacity | | |
| aFRR Activation | | |
| Gross Revenue | | |
| Costs | | |
| Net Revenue | | |
| EFC | | |
| Max / Min SOC | | |
| aFRR Awarded MW | | |
| Non-delivery | | |

并计算：

\[
ExecutionGap
=
Revenue^{PerfectHistory}
-
Revenue^{RealisticBacktest}
\]

这个 gap 本身就是投资研究的重要结果：它衡量理想历史收益与实际可交易策略之间由信息不完美、成交不确定、风险约束和交易成本造成的损失。

---

# 27. 推荐迁移顺序

## PR / Commit 1 — Market calendar abstraction

- 新增 effective-dated market calendar；
- 保持现有求解结果暂不变；
- 所有 GCT / result release 从 config 读取。

## PR / Commit 2 — Frozen state infrastructure

- 加 `FrozenState`；
- solver 支持 fixed bounds；
- 加 freeze audit。

## PR / Commit 3 — Event-specific position & headroom

- 新增 \(B^{DA}\)、\(B^{IDA1}\)、\(B^{IDA2}\)、\(B^{IDA3}\)；
- 加 aFRR/IDA2/IDA3 headroom。

## PR / Commit 4 — 2-day planning / 1-day execution

- 重构 rolling；
- 解决 look-ahead；
- 解决重复结算；
- terminal SOC 改造。

## PR / Commit 5 — Stage 1 regression & audit

- 加所有 P0 tests；
- 输出 `perfect_history_v2` benchmark。

## Stage 2 PR / Commit 6 — Information availability

- `as_of_time`
- `available_at_utc`
- non-anticipativity / input masking

## PR / Commit 7 — Forecast / realized split

- prices
- alpha
- execution ledger

## PR / Commit 8 — SOC reserve & stress activation

## PR / Commit 9 — Bid / award / market depth

## PR / Commit 10 — Costs / penalties / risk

---

# 28. Codex 开工前必须先确认的事项

Codex 在改代码前先完成以下检查，不要直接编码：

1. 阅读：
   - `MILP公式索引.md`
   - `西班牙MILP模型结构与耦合详解_20260921.md`
   - `spain_milp_mathematical_spec_2026-09-16.md`
   - `es_perfect_information_design_20260920.md`
   - `es_conditional_adapter_spec_20260920.md`

2. 阅读代码：
   - `src/es_synthetic_market/_baseline_core.py`
   - `src/es_synthetic_market/rolling.py`
   - `src/es_synthetic_market/ledger.py`
   - `src/es_synthetic_market/core.py`
   - `src/es_historical_conditional/adapter.py`
   - `src/es_historical_conditional/runner.py`

3. 先画出现有：
   - window boundary；
   - freeze boundary；
   - execution boundary；
   - settlement boundary。

4. 明确现有 `x_j`：
   - 是 bid quantity 还是 assumed awarded quantity；
   - 当前 full-fill 下二者等价，但阶段二必须拆开。

5. 明确当前 `result_release_utc` 与 `gate_close_utc`：
   - Stage 1 决策在 GCT 冻结；
   - award 信息在 result release 后可用；
   - 当前 full-fill 可简化，但数据模型不要混成同一字段。

---

# 29. Codex 开发约束

## 不允许

- 不允许为通过测试直接删除当前物理约束；
- 不允许把未来真实数据偷偷作为 Stage 2 feature；
- 不允许在 solver 内硬编码西班牙市场时刻；
- 不允许用 gross DA+IDA volume 直接替代净 physical position；
- 不允许把 look-ahead 日收入提前结算；
- 不允许把所有 rolling window 末端强制等同于项目真实终点；
- 不允许在 Stage 1 顺手加入 Stage 2 功能导致无法解释 benchmark 变化。

## 必须

- 每一项 P0 修改都有独立测试；
- 所有冻结决策可审计；
- 所有 market event 可追踪；
- 每日 executed P&L 可回溯到合同 / reserve / activation；
- Stage 1 新结果与旧结果的差异必须能解释到：
  - rolling change；
  - freeze change；
  - headroom change；
  - terminal change。

---

# 30. 最终架构

```text
                         Historical data
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        Stage 1 Perfect History      Stage 2 As-of Information
                 │                           │
         realized future price            forecasts only
         realized future alpha            alpha forecast
         full fill                        bid/award logic
                 │                           │
                 └─────────────┬─────────────┘
                               │
                     SAME MARKET CLOCK
                               │
            DA → IDA1 → aFRR → IDA2 → IDA3
                               │
                     SAME FREEZE ENGINE
                               │
                    SAME PHYSICAL MODEL
                               │
                 Power / SOC / EFC constraints
                               │
                               ▼
                     Realized execution ledger
```

最重要的架构原则：

\[
\boxed{\text{Stage 2 不重新发明一套模型}}
\]

而应当：

\[
\boxed{
\text{Stage 2 = Stage 1 的时间/物理骨架 + realistic information / execution layer}
}
\]

这样才能保证两个阶段的收益差异具有明确的经济解释，而不是来自两套不同代码逻辑。

---

# 31. 本次改造优先级总结

## P0 — 必须在阶段一完成

### P0-A

\[
\boxed{\text{2-day planning + 1-day execution rolling horizon}}
\]

### P0-B

\[
\boxed{\text{GCT-based market decision freeze}}
\]

### P0-C

\[
\boxed{\text{aFRR commitment-aware event headroom}}
\]

### P0-D

\[
\boxed{\text{SOC state continuity + correct terminal SOC boundary}}
\]

具体要求：

- 仅整个回测起点初始化 SOC；
- rolling window 之间传递 executed SOC；
- 中间 planning horizon 末端不得强制 `SOC=10 MWh`；
- 真正研究终点才允许 terminal SOC / terminal value / terminal band。

这四项完成后，阶段一才可以作为正式 Perfect-History Benchmark。

## P1 / P2 — 阶段二

- as-of information；
- price forecast / realized；
- alpha forecast / realized / stress；
- SOC reserve buffer；
- bid / award；
- market depth；
- AGC replay；
- fees；
- degradation；
- imbalance；
- non-delivery penalty；
- scenario / CVaR。

---

# 32. 外部规则版本提醒

市场日历必须采用 effective-dated 配置。

当前项目 2025 历史规则切片中：

- IDA1 GCT：D-1 15:00；
- aFRR Capacity GCT：D-1 16:00；
- IDA2 GCT：D-1 22:00；
- IDA3 GCT：D 10:00；
- aFRR award 约在 D-1 16:30。

后续规则版本可能调整 aFRR GCT，因此：

```python
get_market_calendar(delivery_date)
```

必须成为唯一时钟来源。

---


# 33. 求解规模与性能设计要求

## 33.1 当前基线规模

当前 192 QH / 2 日窗口的已知基线规模约为：

| 指标 | 当前基线 |
|---|---:|
| 总变量 | 2,340 |
| 整数/二元变量 | 约 705 |
| 约束行 | 3,110 |
| 非零系数 | 约 9,160 |

P0 改造的性能目标不是“完全不增加约束”，而是：

\[
\boxed{\text{不显著增加整数/二元变量数量}}
\]

MILP 的求解复杂度通常对 binary/integer branching 更敏感。因此阶段一允许增加少量稀疏线性约束，但原则上不增加新的离散变量族。

## 33.2 P0 各修改项对 MILP 规模的预期影响

| 修改 | 新增连续变量 | 新增整数/二元变量 | 新增约束 | 性能判断 |
|---|---:|---:|---:|---|
| 2-day planning + 1-day execution | 0 | 0 | 近似 0 | 主要影响外层 rolling，不扩大单次 MILP |
| GCT frozen state | 0 | 0 | 0 为优先实现 | 用 `lb=ub=frozen_value` |
| 事件累计头寸 \(B^m\) | 0 为目标 | 0 | 直接写表达式 | 不创建额外 solver variables |
| event-specific headroom | 0 | 0 | 增加稀疏线性行 | 可控 |
| effective-dated calendar | 0 | 0 | 0 | MILP 外层逻辑 |
| P0-D terminal SOC / SOC state continuity 修正 | 0 | 0 | 替换现有边界与跨窗口状态传递 | 基本无规模影响 |

### 关键实现规则

1. **不要把 \(B^{DA},B^{IDA1},B^{IDA2},B^{IDA3}\) 建成新的 solver variable family。**
2. **不要为了 freeze 新增 `x = frozen_value` 等式；优先固定变量上下界。**
3. **阶段一默认每个 rolling step 只完整 solve 一次。**
4. **使用 HiGHS presolve 让固定变量自动消元。**
5. **只在阶段二出现真实新信息时再考虑 event-by-event re-solve。**

## 33.3 阶段一新增 headroom 约束的规模

事件 headroom 会新增约束，但不新增 binary。

例如对适用的 QH，新增的主要约束为：

\[
B^{IDA1}+R^{up}\le P^{export,max}
\]

\[
-B^{IDA1}+R^{dn}\le P^{import,max}
\]

以及 IDA2 / IDA3 后对应约束。

因此相对于当前约 3,110 条约束，新的模型可能增加数百至约千条稀疏线性行；具体数量取决于各市场覆盖的 QH 数量，特别是 IDA3 只覆盖后半日。

这种增长本身通常不是 P0 的主要性能风险。更大的风险是**不必要地把一次 daily rolling solve 扩展成多个完全重复的信息集求解**。

## 33.4 阶段一性能回归测试

每次 P0 PR 都记录：

```text
n_variables
n_continuous
n_integer
n_binary
n_constraints
n_nonzeros
presolve_time_s
solve_time_s
mip_nodes
mip_gap
objective_value
```

测试要求：

- 使用同一机器；
- 使用同一 HiGHS / SciPy 版本；
- 使用同一 2 日测试窗口；
- 至少运行多个窗口，比较 median / p95，而不是单次偶然值。

### 建议软门槛

阶段一 P0 完成后：

\[
\boxed{
\text{median solve time}_{new}
\le 2\times
\text{median solve time}_{baseline}
}
\]

该门槛作为 **performance investigation trigger**，不是数学正确性的硬拒绝条件。

若超过 2x，优先排查：

1. 是否错误地在每个 GCT 重复完整 solve；
2. 是否把累计头寸建成了大量显式变量和等式；
3. 是否 freeze 通过额外约束而非固定 bounds；
4. presolve 是否失效；
5. 是否新增了不必要的 Big-M / binary；
6. event headroom 矩阵是否存在大量重复行。

## 33.5 阶段二的性能风险

阶段二真正可能导致模型规模数量级增长的是 stochastic / scenario expansion。

例如若将 20 个 activation / price scenarios 分别复制：

- charge / discharge；
- SOC；
- activation；
- operation mode binary；

则变量规模可能从几千迅速扩大到数万；如果二元变量也按 scenario 复制，branch-and-bound 复杂度会显著增加。

因此阶段二推荐升级顺序：

```text
deterministic forecast backtest
        ↓
stress constraints / SOC reserve buffer
        ↓
small scenario set
        ↓
scenario reduction
        ↓
full stochastic / CVaR（如确有必要）
```

不要在阶段二首轮同时引入：

```text
forecast uncertainty
+ activation scenarios
+ bid acceptance scenarios
+ AGC paths
+ CVaR
```

到一个单体 MILP 中。

## 33.6 性能设计结论

阶段一 P0 的目标应保持：

\[
\boxed{
\text{same integer structure}
+
\text{more correct linear constraints}
+
\text{one solve per rolling step}
}
\]

因此 P0 正确实现后，预计主要是**约束数量小幅上升**，而不是整数变量数量大幅增加；单次 MILP 求解时间应保持在同一数量级。

---

## 参考项目资料

本 README 的当前模型描述基于：

- `MILP公式索引.md`
- `西班牙MILP模型结构与耦合详解_20260921.md`
- 当前项目中列出的数学规格、完美信息设计、条件适配器规格及对应代码文件

外部市场时序在正式编码前应以 delivery date 对应生效版本的西班牙系统运行程序和 SIDC/SDAC 市场日历再次核验。
