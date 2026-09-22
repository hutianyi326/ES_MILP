# 西班牙现货—调频耦合报告更新任务

## 任务目标

对现有西班牙现货市场研究基线及用户引用的“西班牙调频和现货市场耦合”对话进行完整一致性审核，然后根据审核结论决定是否重写 `countries/ES/spain_spot_market_research.md`。

## 审核范围

### 必审文件

- `countries/ES/spain_spot_market_research.md`
- `countries/ES/spot_market_structure.md`
- `countries/ES/day_ahead_market_rules.md`
- `countries/ES/intraday_market_rules.md`
- `countries/ES/storage_spot_access_and_settlement.md`
- `countries/ES/spot_arbitrage_mechanisms.md`
- `countries/ES/spot_frequency_coupling.md`
- `countries/ES/spot_data_catalog_and_version_timeline.md`
- `countries/ES/spain_ancillary_services_research.md`
- `countries/ES/supplemental_*.md`（与现货—调频耦合相关部分）
- `countries/ES/sources.md`、`countries/ES/spot_open_questions.md`

### 引用对话中的待核验断言

1. 西班牙 aFRR capacity 按每个 15 分钟周期采购，而非德国式 4 小时 block；
2. 同一 15 分钟可同时申报 Up 和 Down，且方向独立、容量不必对称；
3. 每方向/每 period 最多 25 个报价段、最多一个 indivisible block；aFRR capacity 按方向独立边际容量价格结算；
4. 负的 storage telemetry 只有消费模式 UP（Unidad de Programación）取得相应服务资格时才计入 aFRR 计算；
5. 区分 PTR（计划/基准功率）、PGC、PGCSUP、PGCINF、LIMSUP、LIMINF；核验 `RESAUP = PGCSUP - PGC`、`RESADW = PGC - PGCINF` 和激活后剩余 offer 公式；
6. 核验 Down reserve 示例：PGC=+50 MW、PGCINF=-100 MW 时可达 150 MW；SOC=100% 时下限应受实时 LIMINF 约束，不能直接使用铭牌充电功率；
7. 区分 capacity market 的 habilitated reserve 上限、实时物理 reserve 和已激活后剩余 offer；
8. 识别引用对话中可能混淆 Up/Down 缩写、PTR 与 PGC、调频容量与调频能量、规则事实与研究解释的地方。

## 证据要求

- 优先用 CNMC/BOE、REE、OMIE、ENTSO-E、ACER、MITECO 第一方资料；每条关键判断记录 source ID、条款/页码/API 定位和适用日期。
- 必须检查引用对话中内部搜索引用是否能映射到本地 `S-*` source block；不能映射的内容标为待核验，不得直接写入规则事实。
- 分离 F（规则事实）、I（研究解释）、A（建模假设）、U（未决事项）。
- 明确 2025 历史期、2026-08-11 基准日和 2026-08-11 之后的规则/接口信息，不得倒填历史。

## 审核输出

请生成 `project/review_ES_SP_BASELINE_FULL_2026-09-04.md`，包含：

- 基线各文件覆盖和缺口；
- 引用对话七类断言的逐项核验结果；
- P0/P1/P2 问题及精确定位；
- 是否需要 research agent 修改 `spain_spot_market_research.md`；
- 建议的重写范围、文字风格和必须补充的公式/流程图。

审核期间不得修改 `countries/ES`、模型、代码或数据文件。审核结论明确前，不启动重写。
