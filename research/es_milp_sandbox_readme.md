# Spain MILP sandbox: synthetic battery foundation

状态：有限范围工程骨架，**不是生产模型，也不是历史回测**。  
适用范围：独立储能的通用充放电物理与单一合成能量价格。  
输入标识要求：所有输入必须以 `ES_SYNTHETIC_` 开头；代码没有任何历史文件、市场接口或 API key 读取入口。这个标识是工程边界检查，不是对人工构造数值来源的真实性证明。

## 本次已实现

- 交流侧充电／放电功率上限：默认各 100 MW；
- 直流侧 SOC：默认 10–190 MWh；初始 SOC 可配置；
- 充电和放电效率：默认各 0.92；
- 充放电互斥：每个时段使用一个二元运行状态；
- 终端 SOC 可选固定值；
- 直流吞吐循环约束：

  ```text
  DC 吞吐量 = Σ(η充 × 充电功率 × Δt + 放电功率 × Δt / η放)
  完整循环数 = DC 吞吐量 / [2 × (190 − 10)]
  ```

- 独立残差审计：先检查解数组有限性、功率非负、原始二元变量在 `[0,1]`，再检查 SOC递推、功率、SOC边界、循环上限、终端SOC、二元变量整数性，以及 solver 原始目标与独立现金流反算的一致性；目标绝对残差原则上不超过 `1e-6`。

## 本次明确不实现

- 西班牙日前、日内或 aFRR 的真实价格、订单、出清和结算；
- REE／OMIE 文件、API key、历史激活数据读取；
- aFRR 容量中标、激活电量、15分钟内部激活顺序、偏差结算和罚则；
- 任何真实收益、年化收益或可执行交易结论。

这些项目必须等数据语义、历史激活场景和完整实施门禁通过后另行实现。当前模型是后续市场耦合的物理底座。

## 输入、变量与目标

输入为一个合成价格序列 `energy_price[t]`（€/MWh）及每个时段长度 `dt_hours[t]`。决策变量是：

- `charge_mw[t]`：交流侧充电功率；
- `discharge_mw[t]`：交流侧放电功率；
- `is_discharging[t]`：充放互斥二元变量；
- `soc_end_mwh[t]`：时段末直流电量。

目标是最大化合成价格下的能源现金流：

```text
Σ 价格[t] × (放电功率[t] − 充电功率[t]) × Δt
```

SOC递推为：

```text
SOC[t] = SOC[t−1] + η充 × 充电功率[t] × Δt
                  − 放电功率[t] × Δt / η放
```

求解器使用 SciPy `milp` 的 HiGHS 后端。仅在项目隔离环境 `.venv-es-milp` 中固定 `scipy==1.15.3`；捆绑 Python 运行时未被修改。

## 合成测试

测试文件：[tests/test_es_milp_sandbox.py](../tests/test_es_milp_sandbox.py)

运行命令：

```powershell
.venv-es-milp\Scripts\python.exe -m unittest -v tests.test_es_milp_sandbox
```

覆盖六组测试：小型套利与效率、负电价、SOC／功率／互斥、0.25 EFC（90 MWh DC吞吐）硬约束、非合成／NaN／Inf／非法效率输入拒绝，以及损坏解的故障注入拒绝。

结果文件：[synthetic_test_results.json](../outputs/es_milp_sandbox/synthetic_test_results.json)

## 交接边界

本骨架只证明：给定合成价格和明确技术参数时，基本储能物理可被 MILP 表达并由独立审计复核。它不证明西班牙市场规则已经编码，也不改变项目状态中的 `implementation_approved=false`；有限范围标记只授权该合成底座。
