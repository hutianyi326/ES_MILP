# 补充研究任务 SUP-01：FCR/SRAD 独立储能资格与预认证

## 目标

核实西班牙独立储能参加 FCR 和 SRAD/需求响应产品的资格、预认证、容量/能量报价、测试、计量、账户入口及与现货计划的接口。不能把未确认资格写成储能收入或模型约束。

## 必须覆盖

- FCR：西班牙本地/欧洲层产品定义、是否存在本地采购或跨区入口、独立储能的资格和预认证条件；
- SRAD：服务定义、合格资源类别、独立储能是否属于需求响应资源、容量拍卖/激活/计量/结算；
- PM/BSP/BRP/UP/UF/UO 及现货计划接口；
- 功率、响应、遥测、测试、持续性、SOC 等要求，仅在官方文本明确时确认；
- 2025 历史适用性与 2026-08-11 基准状态；
- 明确哪些事项仍为 open/open-critical。

## 证据与范围

使用 CNMC/BOE、REE、ENTSO-E、ACER、MITECO 和相关官方平台资料。每项关键 claim 必须含机构、标题、日期/生效、URL、访问日、条款/页码/网页定位、2025 适用性和 F/I/A/U 状态。

不得修改 `model/`、`src/`、`tests/`、`outputs/` 或 `data/raw/`；不得开展策略、收益、MILP、代码、回测或预测模拟。只修改 `countries/ES/` 下的交付报告、来源登记和未决问题。

## 交付物

- `countries/ES/supplemental_fcr_srad_eligibility.md`
- 更新 `countries/ES/sources.md`
- 更新 `countries/ES/spot_open_questions.md`

