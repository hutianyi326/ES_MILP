# 2026-01-01同一时段DA电量估值重算

按用户于2026-11-03确认的新假设：Dn充入电量按同一15分钟DA价格计后续售电价值，Up放出电量按同一15分钟DA价格计补能成本。充、放效率分别92%，往返效率84.64%。沿用此前ENTSO-E API原始抓取，未重抓或覆盖旧试算。

## 计算方法

- Dn净电量收益 = 触发交流购电MWh × (0.92² × 同时段DA价 − Dn激活价)。
- Up净电量收益 = 触发交流售电MWh × (Up激活价 − 同时段DA价 / 0.92²)。
- 上述DA电量价值是独立估值项，不重复计入原50% DA套利部分；不生成实际后续调度。
- 保留原触发条件，不因效率调整阈值：Up价−DA价>200，DA价−Dn价>0；容量两方向报价均1 EUR/MW/15分钟，全额中标或0。
- 电站100 MW/200 MWh，DA比例50%，DA为50 MW/100 MWh，aFRR各方向50 MW；aFRR不限制SOC。

## 当日汇总

| 项目 | 欧元 |
|---|---:|
| DA套利净收益 | 4,022.45 |
| Up容量收益 | 37,118.50 |
| Dn容量收益 | 40,306.00 |
| Up激活收入 | 0.00 |
| Up按DA估算的补能支出 | 0.00 |
| Dn激活购电支出 | -23,678.30 |
| Dn按DA估算的后续售电价值 | 28,534.07 |
| Dn电量净收益（支出+估值；小计） | 4,855.77 |
| 总收益（DA+容量+电量净收益） | 86,302.71 |

相比此前仅计激活现金流的57,768.65欧元，增加28,534.07欧元Dn后续售电价值，总收益为86,302.71欧元。Dn购电388.888889 MWh，经两次92%效率后可售329.155556 MWh；Up未触发，补能成本为0。

## 数据与验证

- 来源不变：ENTSO-E A44日前价格（A01序列）、A81/B95/A51容量价、A84/A96/A67中央选择4秒价格；未新增市场规则，新增的同QH估值是用户确认的简化建模假设。
- DA和容量全天96点完整。激活有价时间覆盖率Up72.85%、Dn45.17%；未给价格的区间保持空值，不补零，本结果仅覆盖有价时段。
- 两条新测试验证Dn乘往返效率、Up除往返效率；连同既有6项共8项通过。独立逐4秒重算与新汇总对账误差小于1e-6欧元。
- 结果输出：output/simple_20260101_da_value_20261103/；summary.json为汇总，qh_detail.json分列激活现金流与DA电量估值，validation.json记录独立复核。
- 代码增加 --activation-value-basis same_qh_da_efficiency；默认cash保留旧口径。旧试算目录和原报告保留。本次更新计算脚本及测试、新增本报告，仍在Simple_MILP，未提交或推送。

## 复现

```powershell
& $esPython code/project/calculate_simple_entsoe_day.py --date 2026-01-01 --source output/simple_20260101_entsoe_20261103 --output output/my_new_da_value_result --da-share .5 --capacity-up-bid 1 --capacity-down-bid 1 --up-spread 200 --down-spread 0 --activation-value-basis same_qh_da_efficiency
```
