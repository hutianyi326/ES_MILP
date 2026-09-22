# 西班牙合成 7 天滚动层（B 阶段）

本模块仅接受 `ES_SYNTHETIC_MARKET_` 前缀的 `SyntheticMarketInput`，不读取真实文件、不调用 API，也不产生历史收益结论。

## 执行口径

- 每轮窗口是 `date(start_local) + 7` 个 Madrid 当地日，下一轮只执行首个当地日；窗口边界不使用固定 168 小时，因此春秋 DST 日自然为 23/25 小时。
- 物理MILP包含窗口内**全部7个当地日**的QH、价格、激活与合同；求解后只执行第一个当地日（含首个日内前缀），其余是未执行计划，不计入现金或已用循环。初稿“仅首日优化”已被主线程替换，不是本实现。
- 新订单只有在其 gate 当地日到达且交付完整落在当前 7 当地日窗口内时才提交；跨窗口已有合同按原始合同 MW 保持，不截断。通过 gate 但优化量为零的订单记录为 `not_submitted`，后续窗口不重选。
- `pending` 与 `awarded` 通过 result 时间单向转换，订单 snapshot/hash 随每窗口输出。
- 同一连续 segment 的 SOC 跨窗口、跨年连续；缺口由输入的不同 segment 表示并从 10 MWh 重新开始。年度 EFC 预算按每个 Madrid 日 `valid_hours / actual_hours / 365(or366) * 600` 得到并由各执行日共享，只有实际执行日的吞吐量计入。
- 窗口一旦触及segment真正尾部，窗口末端硬约束SOC=10，关闭估值，但仍逐日执行。非尾窗以**窗口最后一个Madrid日**实际时长加权DA均价，先求均价再取max(均价,0)，乘0.92及窗口末端(E−10)。salvage只进窗口目标，不进现金。末日每QH必须有唯一DA参考合同，缺少或多义则明确拒绝，不猜价格。
- 当前窗口使用**全运行范围年度预算减已执行循环**，不按当前7天重新发额度。窗口目标及上界对应“窗口毛收益＋非现金尾值”，不能跨窗口相加为总收益或全期收益上限。
- 已提交合同的尚未交付分片继续保留原合同MW、价格和结果发布时间。已交付部分不重新优化或付款；未交付部分不得因窗口末端而被丢弃。超过窗口的非零既有承诺明确失败。

## 公开接口

```python
from src.es_synthetic_market import RollingEngine, solve_rolling

run = solve_rolling(input, run_id="ES_SYNTHETIC_ROLLING_DEMO", order_mode="U")
assert run.success
run.windows[0].gross_eur
run.windows[0].salvage_eur
run.windows[0].objective_eur
run.windows[0].order_snapshot_hash
run.ledger.cash_by_type()
```

`SettlementLedger` 按 `run/path/type/object-shard/direction` 幂等记账；DA、IDA、aFRR 容量和 aFRR 激活分开核算。跨日小时合同按 QH shard 结算一次，重复窗口重放不会重复现金。无解、硬约束失败或输入时态不完整时窗口和整次运行返回失败，不能发布有效总收益。

## 现金单位、保存与恢复

- `settle_capacity`：容量MW×已标准化EUR/MW/period，只乘一次，不再次乘0.25。
- `settle_activation`：激活MWh×有符号EUR/MWh，不自动翻转下调符号。
- 现货按买卖方向、合同MW、交付分片小时数和EUR/MWh结算；负电价保留。
- 账本拒绝未知现金类型、终端估值、非有限值、单位不匹配和不符合数量价格公式的金额。JSON结构编码避免分片编号碰撞；同笔重放幂等、异值冲突拒绝。
- `run.execution_cash_eur`仅在全程成功时返回有效合成毛收益。失败前已提交现金只保留为诊断，不冒充完整运行结果。

```python
engine = RollingEngine(input, run_id="ES_SYNTHETIC_ROLLING_DEMO")
engine.step()                         # 完整窗口求解，只提交首执行日
checkpoint = engine.checkpoint()      # 可用JSON保存的状态快照
resumed = RollingEngine.restore(input, checkpoint,
    run_id="ES_SYNTHETIC_ROLLING_DEMO")
run = resumed.run()
```

快照包括SOC、循环累计、冻结订单、容量、现金分片与已执行窗口。输入/config/state哈希不一致拒绝恢复；哈希用于一致性检查，不是带密钥的权限认证。失败窗口不提交任何新订单、现金或循环；完整运行重复调用不重复执行。源码未自动写文件，`as_dict()`与`checkpoint()`提供可保存的交付结构。

## 验证状态与边界

完整B阶段与A核心扩展已获Astra/medium独立审核PASS，P0/P1/P2=0，59项测试全部通过。测试覆盖跨日优化、pending迁移、未来订单冻结、恢复幂等、失败原子性、跨日小时合同、DST短尾、跨年SOC、第8天信息隔离及估值单位；包含原38项回归。审核快照与边界见 [`B终审记录`](../project/review_ES_SYNTHETIC_ROLLING_B_final_20260920.md)。

真实历史输入、真实收益、C阶段压力脉冲及承诺尾部诊断仍未放行。手续费、退化、聚合商费未纳入，不解释为实际不存在。

## 规则与假设分层

规则接口沿用已审核 draft-4 的 DA、IDA、aFRR 独立合同/事件/价格账本、逐方向 100 MW 上限和事件时间要求。滚动窗口、合成价格、订单接受者、未来订单冻结、末端 salvage 与价格符号均为项目明确的合成建模假设，不是新增西班牙规则事实。
