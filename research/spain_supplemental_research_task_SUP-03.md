# 补充研究任务 SUP-03：2026 RR 替代与 96 轮连续日内修订

## 目标

核实 2025-12-30 TERRE/LIBRA 退出后的 RR/平衡能量替代路径，以及 2026 年连续日内 96 轮修订的实际 application/go-live 日期、市场规则、系统程序、平台和历史适用性。

## 必须覆盖

- TERRE/LIBRA 在 2025-12-30 的准确停止边界和 former-member 状态；
- 2026 RR 替代产品、平台、fallback、资格、报价、激活、计量和结算；
- BOE-A-2026-17285（系统运行程序）与 BOE-A-2026-17570（市场规则）的关系；
- 96 轮连续日内修订的实际 application/go-live 日、公告、市场时段、计划和数据字段；
- 2025 历史期、2026-08-11 基准日及 2026-09-03 之后信息分别标注，不得回填 2025；
- 与 ES-SP-03、ES-SP-06、SUP-01、SUP-02 未决事项的交叉影响。

## 证据与范围

使用 ENTSO-E、REE、OMIE、CNMC/BOE、MITECO、ACER 官方资料。每项关键 claim 必须记录机构、标题、发布日期/生效、URL、访问日、条款/页码/网页定位、历史/基准适用性和 F/I/A/U 状态。若截至基准日未确认，不能以 2026-09-03 的后见信息改写 2025 历史结论。

不得修改 `model/`、`src/`、`tests/`、`outputs/` 或 `data/raw/`；不得开展策略、收益、MILP、代码、回测或预测。只修改 `countries/ES/` 下的报告、来源登记和未决问题。

## 交付物

- `countries/ES/supplemental_rr_2026_transition.md`
- 更新 `countries/ES/sources.md`
- 更新 `countries/ES/spot_open_questions.md`

