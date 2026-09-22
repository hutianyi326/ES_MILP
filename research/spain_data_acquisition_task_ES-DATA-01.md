# 西班牙数据采集任务 ES-DATA-01

## 1. 目标

核验并建立可复现的数据采集链，用于下载和分析西班牙现货、aFRR、系统负荷及按电源类型划分的历史出力数据。

## 2. 已确认目录

- 项目工作目录：`C:\Users\Tianyi\OneDrive\融和元储工作\模型等其他参考资料\Python\Counry_Investigation`
- 采集程序：`src/data_ingestion/es/`
- 官方原始数据：`data/raw/ES/<source>/<period>/<retrieval_batch>/`
- 清洗数据：`data/processed/ES/`
- 数据字典、来源证据与研究结论：`countries/ES/`

原始数据不可覆盖。每个下载批次必须记录获取日期、请求参数、响应文件、校验结果和来源 URL。

## 3. 数据范围

| 数据组 | 首选官方源 | 目标时间分辨率 |
|---|---|---|
| 日前价格 DA | OMIE | 官方原生 15 分钟；历史小时级保留原粒度 |
| 日内拍卖 IDA1/2/3 | OMIE | 15 分钟 |
| 连续日内 IDC | OMIE | 15 分钟周期的最高、最低和成交量加权均价 |
| aFRR 容量需求、成交容量、容量价格 | REE eSIOS | 15 分钟 |
| aFRR 激活电量、能量价格 | REE eSIOS | 15 分钟 |
| 不平衡价格 | REE eSIOS | 15 分钟；区分实时临时值与历史结算口径 |
| 系统实际负荷 | REE eSIOS | 原始粒度保留，并以平均值聚合至 15 分钟 |
| 按技术实际发电量 | ENTSO-E Transparency A75；REE REData 仅作对照 | 15 分钟或小时，以官方响应粒度为准 |
| 按技术计划发电量 P48 | REE eSIOS | 15 分钟；不得标记为实际出力 |

## 4. 验证期与时间口径

- 首次验证期：`2026-08-01T00:00:00` 至 `2026-08-31T23:59:59`。
- 市场本地时区：`Europe/Madrid`。
- 原始时间戳、UTC 时间戳、本地时间戳、UTC offset 和 DST fold/duplicate 标识必须保留或可重建。
- 数据单位和币种按官方元数据保存，不在原始层隐式换算。
- 2026 年 8 月数据如属 provisional，必须显式标注，不得称为最终结算数据。

## 5. 阶段门禁

1. `market_researcher` 核验官方接口、指标、文件命名、字段、单位、时区、发布延迟、历史范围和访问条件。
2. 主线程审核规则事实、研究解释和待确认问题。
3. 审核通过后，`modeling_engineer` 才可修改 `src/`、`tests/`、`data/processed/` 和 `outputs/`。
4. 先完成 2026 年 8 月验证下载；多年全量下载需另行确认起止期。

## 6. 交付物

- `countries/ES/spain_data_api_catalog.md`
- `countries/ES/spain_data_api_sources.md`
- `countries/ES/spain_data_api_open_questions.md`
- `data/raw/ES/` 下的官方响应、请求清单与 manifest
- `src/data_ingestion/es/` 下的可配置采集程序
- `tests/` 下的解析、时区、粒度和完整性测试
- `data/processed/ES/` 下的标准化样本数据及质量报告

## 7. 安全与凭据

- eSIOS Token 只从环境变量 `ESIOS_API_KEY` 读取；ENTSO-E Token 只从环境变量 `ENTSOE_API_KEY` 读取。任何凭据都不写入代码、日志、manifest 或数据文件。
- 日志中的请求头必须脱敏。
- 不把网页抓取当作优先方案；有官方文件端点或 API 时优先使用官方机器接口。

## 8. 当前建模边界

本任务只建立数据采集、字段语义和质量验证，不实现交易策略、MILP 或收益回测。计划出力、实际出力、临时价格和最终结算价格必须分别保存。
