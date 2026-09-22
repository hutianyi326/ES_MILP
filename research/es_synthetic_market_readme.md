# `es_synthetic_market`：合成数据联合核心

## 状态

> 后续B阶段的7天滚动与账本也已通过独立审核，59项回归通过；详见 [`滚动与账本说明`](es_synthetic_market_rolling_readme.md)。本文下方“后续阶段”清单保留A交付时的范围说明，当前状态以B说明和审核记录为准；C压力诊断及真实历史门禁仍未通过。

这是西班牙独立储能事后完美信息模型的**第一阶段合成数据核心**，依据：

- `model/es_perfect_information_design_20260920.md` draft4；
- `project/spain_synthetic_full_build_authorization_20260920.md`；
- `project/spain_synthetic_core_hand_checks_20260920.md`。

本模块只接受 `ES_SYNTHETIC_MARKET_` 开头的输入标识，不读取 `data/raw/`、`countries/` 或任何历史收益文件，不访问网络/API，也不接收市场真实凭据。

## 已实现

`src/es_synthetic_market/core.py` 当前实现：

- DA、IDA 合同与 QH 的稀疏映射；所有现货决策变量统一为 MW，交付电量由 QH 小时数和映射权重计算；
- gate / result / delivery 事件顺序检查、合同交付时长守恒、合同不跨 segment/gap、全局 QH 不重叠；
- DA/IDA 买卖互斥、每合同100 MW上限；逐交付QH、逐结果时间戳检查含固定基线的累计净头寸±100 MW。同刻结果合并为一个节点，不按合同名称虚构顺序，不跨交付期相加MW。
- aFRR 上调/下调独立容量变量，新增容量为整数 MW；每个 QH 要求 aFRR gate/result 事件；
- 固定承诺与新承诺分离，使用 `R_fixed + R_new` 形成总容量；上调/下调各自 100 MW，不添加“上下调合计≤100 MW”；
- QH 级基线边界、上调/下调备用头间约束，即使 `alpha=0` 也不删除；
- U（先上调后下调）和 D（先下调后上调）两个 full-joint 物理路径；
- 每个激活子段的实际跨零功率、充放互斥、效率 SOC 递推和 10–190 MWh 电量边界；
- 含激活现金流的四项市场毛收益：DA、IDA、aFRR 容量、aFRR 激活；
- 每个Madrid自然年共享DC吞吐/EFC预算：逐当地日累计“有效小时/当日实际小时”，再乘600/当年日数。完整23/25小时日各算一天；实际额度取此覆盖额度与输入上限较小值。跨缺口重置SOC，同年共享额度；跨年连续区间不重置SOC。
- 独立结果审计：原始变量边界、买卖互斥、所有整数变量、SOC 递推、功率方程、备用头间、年度 EFC、固定/新订单现金重建；
- `tzdata==2026.4` 和 `Europe/Madrid` 环境门禁，并校验显式 `madrid_year` 与 Madrid 本地年一致；不允许静默退回 UTC；
- 有可行解但 solver 因 time limit 未证明最优时仍返回可行结果，并报告 `feasible=True`、`proven_optimal=False`、原始 gap 及收益/上界差距。

## 使用示例

```python
from src.es_synthetic_market import solve_joint, solve_joint_both_orders

result_u = solve_joint(synthetic_input, order_mode="U")
result_d = solve_joint(synthetic_input, order_mode="D")
both = solve_joint_both_orders(synthetic_input)
```

`result.objective_gross_eur` 是本次合成输入、固定顺序和full-joint约束下的毛收益。`cash_breakdown_eur`包含可直接相加的DA、IDA、新容量、新激活和固定承诺现金，不重复放入现货合计。`contract_trades`给出合同买卖MW/MWh、事件时间和现金；`profit_upper_bound_eur`保留同一目标的求解上界。固定承诺现金是显式合成输入，尚非B阶段逐笔持久账本。`residuals`含独立物理/现金复算及完整代数边界核验。

## 尚未实现，不得误称完整模型

以下内容留到后续阶段：

- 7 天滚动执行、日内事件账本和跨窗口 pending/awarded 持久状态；
- 完整订单报价冻结流程、实时结果节点累计净头寸的持久账本；
- 15 分钟事后压力诊断及脉冲后的固定主路径尾部验证；
- 独立结算引擎的生产化输出文件和现金账本；
- 历史价格、REE/OMIE 数据读取、真实激活代理、缺失区间验收和历史收益回测；
- 项目级资格、可用率、恢复、罚则和完整 pre-qualification 合规检查；
- 预测信息模式、非前视策略、CVaR、90/180 天校准场景；
- 成交概率、订单簿、价格冲击、费用、退化和项目净利润。

因此，本模块的通过仅表示“合成 full-joint U/D 核心可运行并通过单元测试”，不表示真实数据门禁通过，也不表示 `implementation_approved=true`。

## 测试

使用隔离环境运行：

```powershell
& ./.venv-es-milp/Scripts/python.exe -m unittest tests.test_es_synthetic_market_core -v
```

测试覆盖严格 synthetic 输入、事件和合同映射、QH 逆序拒绝、aFRR gate/result、full-joint U/D、固定承诺、逐子段 SOC、跨零功率、QH 备用头间、跨 segment 年度预算、激活现金、变量独立审计和可行但未证明最优的 time-limit 返回。
