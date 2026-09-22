# 补充研究任务 SUP-02：SOC、持续时长、补能与恢复

## 目标

核实西班牙 aFRR/mFRR/RR、FCR 和 SRAD（如适用）对储能 SOC、持续供能时长、激活后补能、恢复目标、可用率和性能归责的官方要求。若没有统一储能参数，必须明确证据边界，不得从 FAT、交付时长或能量报价反推固定 SOC 约束。

## 必须覆盖

- 各产品是否有最低/最高 SOC、能量容量、持续供能时长或对称能力要求；
- 激活期间、激活后和后续编程期的补能/恢复方式、窗口、费用和责任；
- SOC/能量不足、可用率、响应不足、未交付与罚款/停权的关系；
- 独立储能与需求响应、发电资源在规则上的差异；
- 2025 历史与 2026-08-11 基准版本边界；
- 对前一步 FCR/SRAD 未决资格的交叉影响。

## 证据与范围

使用 CNMC/BOE、REE、OMIE、ENTSO-E、ACER、MITECO 官方资料。每项关键 claim 必须记录机构、标题、发布日期/生效、URL、访问日、条款/页码/网页定位、2025 适用性和 F/I/A/U 状态。

不得修改 `model/`、`src/`、`tests/`、`outputs/` 或 `data/raw/`；不得开展策略、收益、MILP、代码、回测或预测。只修改 `countries/ES/` 下的报告、来源登记和未决问题。

## 交付物

- `countries/ES/supplemental_storage_energy_requirements.md`
- 更新 `countries/ES/sources.md`
- 更新 `countries/ES/spot_open_questions.md`

