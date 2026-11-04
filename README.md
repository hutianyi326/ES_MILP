# ES_MILP：储能简易收益测算（Simple_MILP）

本分支保存西班牙储能的**非MILP简易模型**：DA每日一次先充后放窗口搜索，aFRR按容量中标和4秒价格阈值模拟激活，再计算Dn后续售电价值、Up潜在补能成本。当前归档截至2026-11-04。

本模型使用事后已知价格；aFRR没有SOC、方向互斥或后续交易时序约束。输出是约定简化口径的毛收益和潜在电量估值，不能直接视为实际可执行或实际结算利润。原MILP模型、历史运行方式和版本说明保存在[README_MILP.md](README_MILP.md)。

## 直接查看当前成果

- [月度收益Excel：三种DA比例＋充50/放100 MW场景](reports/simple_model_release_20261104/artifacts/monthly_strategies_with_asymmetric.xlsx)：17个月汇总、参数、逐日公式、价格覆盖率，以及独立的80% DA月度表。
- [2026-01-01单日4秒公式Excel](reports/simple_model_release_20261104/artifacts/sample_20260101_4s.xlsx)：21,600个4秒时段的五类价格、参数和逐项收益公式。当前文件保存为80% DA，含估值41,392.91 EUR；最初50%基准为91,414.93 EUR，可在参数表恢复50%核对。
- [三种DA策略的月度CSV](reports/simple_model_release_20261104/monthly_three_strategies.csv)、[充50/放100 MW月度CSV](reports/simple_model_release_20261104/monthly_asymmetric_80pct.csv)、[月度充放电均价及循环统计](reports/simple_model_release_20261104/monthly_asymmetric_da_metrics.csv)。
- [配置及累计结果快照](reports/simple_model_release_20261104/benchmark_results.json)、[交付文件SHA256](reports/simple_model_release_20261104/delivery_manifest.json)。

本次Git归档包括代码、测试、计算报告、轻量CSV/JSON和以上最终Excel样本。大型原始行情、逐4秒合并数据和完整中间运行文件位于本地`input/`、`output/`，由`.gitignore`排除；API凭据不入库。只查看结果不需要API或本地行情文件，重新计算需要准备下述输入。

## 必要参数

| 参数 | 单位/取值 | 当前采用值 | 对计算的作用 |
|---|---|---|---|
| 交付日期与时区 | 当地日期；Europe/Madrid | 2025-06-01至2026-10-31；另有2026-01-01单日样本 | 决定当地日、月份及23/25小时夏令时边界 |
| AC充电功率 | MW | 对称100；不对称50 | 约束DA充电；剩余部分用于Dn申报 |
| AC放电功率 | MW | 100 | 约束DA放电；剩余部分用于Up申报 |
| DC额定电量 | MWh | 200 | 按DA比例分配可用直流电量 |
| DA参与比例`s` | 小数0—1 | 对称场景1.0、0.5、0.8；不对称场景0.8 | DA功率、电量均按`s`分配；aFRR按`1−s`分配 |
| 充、放电单向效率 | 小数 | 各0.92 | DA能量转换及aFRR补能/售电估值；往返效率0.8464 |
| Up/Dn容量报价 | EUR/MW/15分钟 | 各1 | 市场容量价严格高于报价才全额中标 |
| Up激活价差阈值 | EUR/MWh | 200 | Up价−同15分钟DA价严格大于阈值才激活 |
| Dn激活价差阈值 | EUR/MWh | 0 | 同15分钟DA价−Dn价严格大于阈值才激活 |
| 激活后电量估值方式 | `cash` / `same_qh_da_efficiency` / `daily_da_quantiles_efficiency` | 当前采用最后一种 | 单日CLI支持三种历史口径；全区间采用P25/P75口径 |
| Up补能、Dn售电参考价 | EUR/MWh | 当日DA P25、P75 | 由当日数据自动计算，无需手工输入价格 |

80% DA的两种配置如下，aFRR的Up、Dn分别申报并独立筛选：

| 项目配置 | DA充/放功率 | DA电量 | aFRR Up | aFRR Dn |
|---|---|---:|---:|---:|
| 充100/放100 MW、200 MWh | 80/80 MW | 160 MWh | 20 MW | 20 MW |
| 充50/放100 MW、200 MWh | 40/80 MW | 160 MWh | 20 MW | 10 MW |

**当前脚本是已验算的固定历史样例，并非通用配置界面。**

- 单日入口支持命令行修改日期、DA比例、四个报价/阈值及估值方式；项目功率、电量、效率当前固定100/100 MW、200 MWh、92%。单日CLI的DA比例要求`0<s<1`。
- 全区间入口固定518天、100/100 MW、200 MWh、三种DA比例及上述报价/阈值；检查中明确要求49,732个15分钟和11,189,700个4秒时段。它支持纯DA场景`s=1`。
- 不对称入口固定50/100 MW、200 MWh、80% DA，并重新搜索每天的40/80 MW、160 MWh DA计划。
- `da_search(prices, charge_power, energy, eta, discharge_power=...)`支持单独的充、放电功率。更换历史区间、功率、电量或报价需更新相应入口及其边界检查，不能只改Excel标题。
- 改报价/激活阈值后必须重新筛选原生4秒价格；不能复用旧的每MW激活积分。不对称场景复用旧积分的前提是报价、阈值、DA价格和效率一致，程序会核对相应配置与价格文件哈希。

## 必要行情数据

货币均为EUR。时间列是区间左端，终点不包含；UTC为唯一时间键，本地ISO时间必须带`+01:00`/`+02:00`偏移。负价和有效零价保留原值。

| 数据 | 必要原生频率 | 单位 | 使用方式 |
|---|---|---|---|
| DA日前电价 | 15分钟；早期历史源为小时 | EUR/MWh | DA窗口搜索、激活价差基准、每日P25/P75 |
| aFRR Up容量价格 | 15分钟 | EUR/MW/15分钟 | 中标筛选及容量收入 |
| aFRR Dn容量价格 | 15分钟 | EUR/MW/15分钟 | 中标筛选及容量收入 |
| aFRR Up激活价格 | **原生4秒** | EUR/MWh | Up触发及售电收支 |
| aFRR Dn激活价格 | **原生4秒** | EUR/MWh | Dn触发及购电收支 |

早期小时DA只在原交付小时内重复映射，保留`da_native_resolution=PT60M`；原生15分钟为`PT15M`。15分钟激活均价只能用于观察，不能替代4秒阈值回测。

### 全区间输入目录

本机已整理的数据包：`input/datasets/ES/market_20250601_20261031_20261103/`。

```text
processed/
  market_prices_15min.csv
  prices_4s/2025-06.csv.gz ... 2026-10.csv.gz
  daily_coverage.csv
  remaining_price_gaps.csv.gz
sources.json                  # 来源ID、不可变原始快照及SHA256
summary.json                  # 覆盖统计，计算入口会使用
validation.json               # 数据验证记录
raw/reused/                   # 复用官方快照
raw/fetched/                  # 本次API响应
```

`market_prices_15min.csv`的主要列：`start_utc`、`start_europe_madrid`、`da_eur_mwh`、`capacity_up_eur_mw_qh`、`capacity_down_eur_mw_qh`、`da_native_resolution`、三个DA/容量`source_id`、`activation_up/down_valid_seconds`、`activation_up/down_mean_eur_mwh`、`activation_up/down_reported_seconds`、`activation_source_id`。其中DA、双向容量要求完整；有价秒数用于逐4秒回读对账。

每月4秒CSV主要列：`start_utc`、`start_europe_madrid`、重复对齐的DA及双向容量价格、`da_native_resolution`、`activation_up_eur_mwh`、`activation_down_eur_mwh`、`up_price_status`、`down_price_status`、`activation_source_id`。上下调状态区分`valid`、`source_explicit_null`、`source_unreported`和`api_no_matching_data`。

所有官方空值保留，不补零、不插值、不跨显式空块延续价格。当前全区间Up激活有价率55.15%、Dn为58.20%，DA和双向容量均100%；空激活价不能据此判定本站未被调用。

### 单日输入与官方来源

单日抓取保存`DA.json`、`capacity_A01.json`、`activation_A67.json`及原始XML/ZIP、请求记录、哈希；计算读取这些JSON中的原生有效区间。另保存的`activation_A16.json`是查询证据，不替代A67输入。

- [ENTSO-E生产API](https://web-api.tp.entsoe.eu/api)，西班牙区域`10YES-REE------0`。DA为A44并筛选A01日前序列；容量为A81/B95/A51、日合同A01、方向A01/A02；激活为A84/A67/A96、标准产品A01、原生PT4S、A08价格。
- 前期DA来自[OMIE官方文件](https://www.omie.es/en/file-download)，容量来自[REE/eSIOS](https://api.esios.ree.es/)的2130/634指标；缺失月份由ENTSO-E补抓。
- A03有效区间与空值展开遵循[ENTSO-E曲线说明](https://transparencyplatform.zendesk.com/hc/en-us/articles/30262342482961-CurveType-A01-vs-CurveType-A03)。源字段与版本记录见[数据整理报告](reports/simple_market_data_20250601_20261031_20261103/数据整理与验收.md)。

上述是数据来源和语义；以下分配、触发及估值方法是本次模型假设，不等同于完整BSP市场结算规则。

## 收益计算

1. **DA**：在每日15分钟时间轴上搜索一次连续充电、随后一次连续放电，深度1%—100%，允许末段部分功率，也可不交易。初末可用直流电量为0。交流购电量×充电效率＝直流充入量；交流放电量÷放电效率＝直流取出量。净收益＝售电收入−购电成本。
2. **容量**：市场容量价严格大于报价，中标MW取对应申报MW，否则取0；不考虑部分中标。每15分钟收益＝中标MW×原生容量价，**不再乘0.25**。展开成4秒账本时按`4/900`分摊，避免重复计费。
3. **激活**：每4秒同时满足对应容量中标及价差条件时，以中标MW计量。Up收入＝Up交流售电MWh×Up价；Dn收支＝−Dn交流购电MWh×Dn价。负价购电可能产生正收支。
4. **后续电量估值**：Dn售电价值＝Dn交流购电MWh×`0.92²`×当日DA P75；Up补能收支＝−Up交流售电MWh÷`0.92²`×当日DA P25。触发条件仍使用同15分钟DA，P25/P75只用于估值。分位数采用当地日全部15分钟价格等权、含重复值、索引`(n−1)×p`的线性插值。
5. **合计**：当期收支＝DA净收益＋双向容量＋双向激活收支；含估值总收益再加Dn售电价值、Up补能收支。后续估值计入激活发生日/月，没有安排实际后续交易或检查其时序、功率及成交量。

aFRR方向独立筛选，没有SOC、互斥、持续能量或补能功率限制；系统价格不是本站实际指令。无价方向的逐日激活项目留空，汇总只包含可计算部分。模型未扣税费、网络费、交易费、退化、投资及运营成本。

## 环境与运行

Python建议3.12及以上。抓取和收益核心使用标准库；Windows时区数据以及独立校验所需NumPy/Pandas列于`code/requirements-simple.txt`，不需要MILP求解器。

在仓库根目录打开PowerShell：

```powershell
py -3.12 -m venv .venv-simple
$py = '.\.venv-simple\Scripts\python.exe'
& $py -m pip install -r code/requirements-simple.txt
$env:PYTHONPATH = "$PWD\code"
```

已有本地行情时可以完全离线计算。运行目录须为新目录，以下示例使用此前归档目录名；本机已存在时请换名，并在后续命令传入对应路径。

### 单日抓取和测算

`ENTSOE_SECURITY_TOKEN`从进程环境读取；也可用抓取入口的`--credential-file`读取本地`.env`。这里只填写占位符，真实Token不要写入Git。

```powershell
$env:ENTSOE_SECURITY_TOKEN = 'YOUR_ENTSOE_TOKEN'
& $py -m project.fetch_simple_entsoe_day --date 2026-01-01 --output output/simple_20260101_entsoe_20261103
& $py -m project.calculate_simple_entsoe_day --date 2026-01-01 --source output/simple_20260101_entsoe_20261103 --output output/simple_20260101_p75_p25_20261103 --da-share .5 --capacity-up-bid 1 --capacity-down-bid 1 --up-spread 200 --down-spread 0 --activation-value-basis daily_da_quantiles_efficiency
```

25小时日的A84分段抓取由全区间适配器处理；单日抓取入口主要用于本次普通24小时样本，秋季时钟切换日应使用分段归档。单日计算器可按完整输入的实际当地日长度计算，但单日Excel模板仍固定为本次24小时样本。

### 全区间三策略及充50/放100 MW场景

先准备完整数据包，再执行：

```powershell
$dataset = 'input/datasets/ES/market_20250601_20261031_20261103'
& $py -m project.calculate_simple_market_period --source $dataset --output output/simple_period_20250601_20261031_20261103
& $py -m project.calculate_simple_asymmetric_period --source $dataset --basis output/simple_period_20250601_20261031_20261103 --output output/simple_asymmetric_50_100_200_80pct_20261104
```

历史补抓适配器`consolidate_simple_market_data`目前依赖完整父项目`Counry_Investigation`：其`src/data_ingestion/es/omie.py`、`data/raw/ES/omie`、`data/raw/ES/esios`和`project/es_afrr_cbmp_20261101`。单独克隆本仓库不会自动获得这些目录；可以直接恢复上面的完整已整理数据包来运行测算。

完整父项目布局下，可依次运行`python -m project.consolidate_simple_market_data inventory`、`fetch`、`merge`，再运行`python -m project.validate_simple_market_dataset`及`python -m project.report_simple_market_dataset`。默认目标及日期定义在适配器顶部，`inventory`要求目标尚不存在，`fetch`支持有效回执续用。抓取优先读环境Token，再兼容父目录`Country Dashboard/.env`，请求记录不保存凭据。

### Excel导出

Excel由Node.js＋`@oai/artifact-tool`生成，使用Codex桌面捆绑运行库；这是可选导出依赖，Python的CSV/JSON测算不依赖它。普通克隆若未提供该运行库，仍可计算并读取CSV/JSON以及仓库中的最终Excel样本。

将`code/project/node_modules`连接到已提供的捆绑`node_modules`目录（本机可用目录为`$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\node\node_modules`；以实际加载器路径为准），用同一捆绑Node依次运行：

```powershell
$runtime = Join-Path $env:USERPROFILE '.cache/codex-runtimes/codex-primary-runtime/dependencies'
$node = Join-Path $runtime 'node/bin/node.exe'
if (!(Test-Path 'code/project/node_modules')) {
    New-Item -ItemType Junction -Path 'code/project/node_modules' -Target (Join-Path $runtime 'node/node_modules') | Out-Null
}
# 每个入口均支持--help及自定义路径。
& $node code/project/build_simple_day_excel.mjs
& $node code/project/build_simple_monthly_excel.mjs
& $node code/project/add_simple_80pct_excel_sheet.mjs
& $node code/project/add_simple_asymmetric_excel_sheet.mjs
```

前两者的参数是`--source`结果目录、`--output`输出目录、`--qa`检查目录；后两者使用`--input`原Excel、`--output`新Excel文件、`--source`对应计算结果目录、`--qa`检查目录，另支持`--inspect-only`。默认Excel落在`output/excel_sample/outputs/simple_model`、`output/excel_monthly/outputs/simple_model`，QA图像和检查JSON在`output/simple_excel_qa`。默认计算目录与上面示例一致。

这些导出入口保留当前固定样例的日期、行数和表结构；单日4秒Excel固定为2026-01-01的50% DA样本，月度固定为当前17个月。修改基础场景或频率后需同步更新导出模板及核对值。Excel编辑DA比例可重算已登记的线性分配；改变功率、电量或效率后，不能依赖旧DA窗口直接得到重新搜索结果。

## 产出清单

| 入口 | 主要文件 | 内容 |
|---|---|---|
| 单日计算 | `summary.json` | 配置、DA窗口、分方向容量/激活/估值、总收益、来源哈希 |
| 单日计算 | `qh_detail.json`、`normalized_prices.json` | 15分钟账本、原生4秒价格及空值 |
| 单日计算 | `matrices.json` | 容量报价0—100步长1；激活绝对价及价差0—1000步长20的超阈值比例；按样本月-小时分组 |
| 全区间计算 | `daily_inputs.csv`、`daily_scenarios.csv`、`monthly_scenarios.csv` | 日度每MW筛选积分、三策略逐日及月度收益 |
| 全区间计算 | `quarter_hour_calculation_basis.csv`、`results.json` | DA计划与每QH筛选依据、配置、总/月/日结果和哈希 |
| 不对称场景 | `da_schedule_15min.csv`、`daily_results.csv`、`monthly_results.csv`、`results.json` | 新功率下重搜的DA计划、SOC轨迹、逐日和月度结果 |
| 独立验证 | `validation.json`、`workbook_validation.json` | 数据覆盖、现金/能量误差、Excel核对与保留记录；后者为本次归档记录 |
| Excel | 单日4秒样本、月度收益工作簿 | 价格、参数、逐项公式、三策略汇总及两个独立80% DA月度视图 |

单日矩阵只是该日样本的统计；当前全区间入口没有额外的交互式月-小时选价界面。运营指标CSV中的充放电均价按DA成交电量加权，价差为两者相减；等效循环＝交流放电量÷0.92÷160 MWh或200 MWh，不包含aFRR循环。

## 已归档结果与验证

2025-06-01至2026-10-31，单位EUR：

| 配置 | DA净收益 | 容量收益 | 电量净收益（含估值） | 含估值总收益 |
|---|---:|---:|---:|---:|
| 100/100 MW、200 MWh，100% DA | 10,402,104.34 | 0.00 | 0.00 | 10,402,104.34 |
| 100/100 MW、200 MWh，50% DA | 5,201,052.17 | 26,295,257.00 | 10,640,968.76 | 42,137,277.94 |
| 100/100 MW、200 MWh，80% DA | 8,321,683.47 | 10,518,102.80 | 4,256,387.51 | 23,096,173.78 |
| 50/100 MW、200 MWh，80% DA | 8,144,494.13 | 8,801,938.20 | 2,391,405.09 | 19,337,837.43 |

2026-01-01、100/100 MW、200 MWh、50% DA的单日含估值基准为91,414.92750724638 EUR。归档Excel当前参数已保存为80% DA，对应41,392.90761159608 EUR；代码默认重新导出的仍是50%基准，两个值按各自参数核验。大部分aFRR容量按本模型门槛全额中标，激活又无SOC限制，这些假设会使比较结果较乐观；50%比例最高不代表实际可执行最优策略。

```powershell
& $py -m unittest discover -s code/tests -p 'test_simple*.py'
# 无须大型行情即可核对本次已提交的Excel/CSV、参数、哈希及缓存金额：
& $py -m project.validate_simple_release
# 有全区间数据及原三策略工作簿时进行独立全量复核：
& $py -m project.validate_simple_market_period --source $dataset --results output/simple_period_20250601_20261031_20261103 --workbook 'output/excel_monthly/outputs/simple_model/西班牙_100MW200MWh_三策略月度收益_20250601_20261031.xlsx'
```

当前24项简化模型测试通过，覆盖严格阈值、空值/零价、负价现金、A03、夏令时、充放顺序、效率、电量平衡及不对称功率。此前独立重读全部11,189,700行4秒数据、核验1,531份原始快照；不对称DA的518天/49,732个15分钟功率及SOC检查通过。完整记录见[月度测算报告](reports/simple_period_20250601_20261031_20261103/月度收益测算与验证.md)、[不对称场景报告](reports/simple_asymmetric_50_100_200_80pct_20261104/测算说明与验证.md)。历史报告中的“未提交”描述为生成时点状态，版本归档状态以Git历史为准。
