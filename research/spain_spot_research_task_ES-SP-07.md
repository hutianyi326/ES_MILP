# 西班牙现货市场研究任务：ES-SP-07 数据目录与版本时间线

## 任务状态

- 阶段：ES-SP-07
- 前置门禁：ES-SP-06 已通过独立 review agent，P0/P1/P2=0
- 研究对象：2025-01-01—2025-12-31 的西班牙独立储能现货研究所需官方数据
- 规则基准日：2026-08-11
- 执行 Agent：`market_researcher`
- 交付后必须提交独立 review agent；未通过不得进入 ES-SP-GF

## 研究目标

建立可复核的数据目录和版本时间线，覆盖 OMIE、REE/eSIOS、ENTSO-E Transparency、CNMC/MITECO/BOE 公开规则及结算接口。重点说明哪些数据可用于交易决策、哪些只适用于事后结算或研究核验。

## 必须覆盖

1. 数据入口、机构、页面/API 标题、发布日期/生效日期、URL、访问日期和版本状态；
2. 日前价格、日内拍卖/连续成交、跨区容量、订单/成交、计划、激活、计量、BRP 偏差和结算字段；
3. 每个数据集的时间分辨率、时区（CET/CEST）、DST 处理、单位、币种和方向定义；
4. 发布时滞、重发布、修订号、历史覆盖、API key/账户权限和公开/私有边界；
5. 2025 年 MTU15、ISP15、MARI/PICASSO/TERRE 和其他规则切换的版本时间线；
6. 决策时可获得输入与事后结算输入的分离，明确不得用未来发布或修订数据回填决策；
7. 记录数据缺失、字段映射、权限和历史覆盖的 open/open-critical 问题。

## 证据要求

每项关键数据集或版本 claim 必须记录机构、标题、发布日期或生效日期、URL、访问日、API 路径/指标 ID/章节/表格定位、2025 适用性和 confirmed/open 状态。规则事实、研究解释和建模假设分栏；本阶段不新增建模假设。

## 明确排除

- 不下载或覆盖 `data/raw/`；
- 不写入 `model/`、`src/`、`tests/` 或 `outputs/`；
- 不做价格预测、收益测算、策略、MILP、代码或回测；
- 不把 ES-SP-06 中 SOC、FCR/SRAD 或 2026 RR 替代等未决事项改写为已确认数据字段。

## 交付物

- `countries/ES/spot_data_catalog_and_version_timeline.md`
- `countries/ES/sources.md` 的新增来源登记
- `countries/ES/spot_open_questions.md` 的 ES-SP-07 未决事项

