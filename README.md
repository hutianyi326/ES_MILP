# 西班牙储能 MILP

本目录是独立整理副本；原项目和桌面文件保留。整理日期：2026-09-22。

## 版本记录

### V1.1 — aFRR 容量收益敏感性（2026-09-24）

- 新增逐 QH、分方向 aFRR 容量系数整理流程，以及 `full_fill`、`optimize`、`posthoc` 三种运行模式；默认 `full_fill` 保持原 V1 口径。
- 增加 posthoc 容量现金折减、可恢复检查点的模式识别与结果口径标记、重复折减保护，以及收益比较脚本和对应测试。
- 36 项相关回归测试通过；真实两日输入下三种模式均成功，optimize 和 posthoc 的中途检查点恢复结果已核对。
- 系数是系统分配容量与报价量之比形成的事后敏感性代理，不代表单站真实中标率；REE 报价曲线的地域匹配仍待确认。完整范围、假设和限制见[敏感性方案及验收记录](research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)。

## P0 完美预测模型 V1

P0实现使用独立入口，原v5入口保留供复现。新增GCT备用检查、正式终点SOC、空值时间轴/空闲桥接、显式预算和冻结审计；这些包含可行域变化，不承诺收益或耗时不变。

```powershell
$esPython = '..\..\..\.venv-es-milp\Scripts\python.exe'
# 正式交付日1月1日至8日，额外加载1月9日；--end为排除的当地日期。
& $esPython code/project/run_es_perfect_v1.py --start 2025-01-01 --end 2025-01-09 --output output/my_perfect_run
```

输出目录必须为新目录。输入默认读取`input/raw/ES`归档，不访问API；缺失数据留空并输出质量摘要。`--preflight-only`仅预检；`--budget-json`接受正式年份到EFC额度的JSON映射。全量v5相同日期默认读取归档的两年预算；归档不在时须显式提供，不能悄悄改用单场景预算。跨年观察额度独立按有效日生成。

输出包含输入证据、正式/规划区间、配置和源码哈希、逐窗消元映射和独立验收、冻结与现金账本、检查点、六项月度收益及数据质量。Python接口`PerfectEngine.restore`可用相同输入及配置恢复检查点，校验失败不得继续复用状态。

验证及边界见[本次实施与验收记录](reports/完美预测模型优化V1_实施与验收.md)，[review记录](reports/完美预测模型优化V1_review.md)。原全量结果和下列旧入口仍对应v5。

2026-09-22已完成当前P0模型2025-01-01至2026-08-31全量测算：100 MW / 200 MWh，608个逐日窗口，条件毛收益782.296071 k€/MW；原模型成功归档（v5执行版，比较中称V0）为796.611354 k€/MW，相差−1.797%。详见[全量V1与V0对比](reports/perfect_v1_vs_v0/结果对比.md)，含月度总额、六项市场收益、图表、共同结算QH对比和用时口径。

本次仅对2025-11-22窗口的数值不可行报告以presolve=True重试一次，预算与模型约束不变；正式续跑使用`code/project/resume_es_perfect_full.py`，未改核心模型。完整成果位于`output/perfect_v1_full_completed_retry/`，原始失败现场位于`output/perfect_v1_full_20260922/`。额外观察日2026-09-01全部缺失，不提供有效价格前瞻。本次没有调用agent审核。

## aFRR 容量收入敏感性

此情景用每个QH、每个方向的“系统实际分配容量/总报价容量”作为容量收入系数，并以1封顶。它是事后系统比例代理，并非单个储能站的真实中标概率；本轮仅折减容量收入，激活收益及完整容量的物理承诺沿用V1。方案、缺失处理和数据来源见[容量收益中标率敏感性方案](research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)。

主入口`code/project/run_es_perfect_v1.py`现有`--capacity-award-mode`开关，分为`full_fill`、`optimize`和`posthoc`。`full_fill`是默认模式，保持V1的100%容量中标计价；`optimize`要求`--award-rate-file`，把QH/方向比例放入容量收入目标后重新优化；`posthoc`也要求系数文件，先按V1全额中标口径优化，再只折减容量现金流，交易决策保持不变。举例：

```powershell
# 中标率进入优化函数
& $esPython code/project/run_es_perfect_v1.py --start 2025-01-01 --end 2025-01-09 --output output/cap_opt --capacity-award-mode optimize --award-rate-file input/processed/ES/afrr_capacity_award_rate_202501_202608.csv.gz

# 对V1决策作事后容量收益折减
& $esPython code/project/run_es_perfect_v1.py --start 2025-01-01 --end 2025-01-09 --output output/cap_posthoc --capacity-award-mode posthoc --award-rate-file input/processed/ES/afrr_capacity_award_rate_202501_202608.csv.gz
```

今后只需把REE archive 234的**原始月度ZIP**逐月放入`C:\Users\Tianyi\Desktop\西班牙数据\容量报价曲线`，保留原始文件名，一个月一个ZIP，不必解压或手工汇总。用`code/project/prepare_es_afrr_award_rates.py`形成QH压缩表与来源清单；报价ZIP的读取需要`xlrd==2.0.2`。632/633分配容量仍来自eSIOS原始数据。

如 REE 对旧月份发布修订包，保留旧文件并将新 ZIP 原样放在上述目录的`revisions`子目录；清洗时以重复的`--offer-zip`参数显式指定各修订月份。每次清洗会保存实际使用的文件路径、SHA-256和逐日/QH完整性检查；不能直接覆盖既有系数表或历史运行结果。

2025-01 至 2026-08 的 [容量收入敏感性结果对比](reports/capacity_award_rate_sensitivity_20260923/结果对比.md) 包含 V1、固定调度折减和重新求解的总/月度收益，以及六项市场分解、EFC 用量与求解时间。原始月度 ZIP、处理后的系数表及大型结果保存在本机，不随 Git 上传。

## 文件分类

| 目录 | 内容 |
|---|---|
| `code/` | 桌面 pkg_patched 源码、全量v5执行入口、数据适配、测试与依赖 |
| `input/` | 官方原始文件，以及全量共同输入和来源清单 |
| `output/` | full_range最终v5结果、two_day两日结果、two_day_timing计时结果、benchmarks紧凑性能证据 |
| `reports/` | 最新中文报告、SVG图表、月度及小时CSV、整理校验记录 |
| `research/` | 市场研究、官方来源索引、数学模型、假设及历史验证说明 |

代码内的 `src/`、`project/`、`countries/ES/` 和 `model/` 是Python导入或依赖指纹所需结构。`code/model`中的适配说明保留供指纹计算，阅读材料集中于research。

## 默认模型和结果

- 100 MW充放电功率，SOC 10–190 MWh，充放电效率各92%。
- 两日滚动，ts_start / cap_old / D（先下后上），gap=1e-4，presolve=False，30秒/窗口，A1–A3关闭。
- 测算交付日：马德里当地2025-01-01至2026-08-31。
- 全量结果：52,247个有效QH，覆盖89.52%，636个窗口；条件毛收益796.61 k€/MW。
- 完美信息条件测算；未包含费用与退化现金。cap_old历史时表适用日期仍待核实。缺失数据未补齐。

成功v5除了pkg_patched源码，还使用执行入口中的EFC终端预留、1e-6 EFC数值余量，以及容差内SOC/备用边界归一。**复现v5应使用以下全量入口；直接调用src中的普通CLI不包含这些运行修复。**

## 环境与运行

使用Python 3.12；版本见[requirements.txt](code/requirements.txt)。本副本不包含虚拟环境、缓存和凭据。当前机器可继续使用原项目的`.venv-es-milp`。

在本目录（countries/ES/MILP）中打开PowerShell：

```powershell
$esPython = '..\..\..\.venv-es-milp\Scripts\python.exe'
& $esPython code/project/run_es_full_ts_start_cap_old_d_20260921.py --help

# 从本目录官方原始数据重新构造输入，仅预检
& $esPython code/project/run_es_full_ts_start_cap_old_d_20260921.py --output output/preflight_new --preflight-only

# 正式运行；输出必须为不存在的新目录
& $esPython code/project/run_es_full_ts_start_cap_old_d_20260921.py --output output/full_range_new

# 可选：重用已保存的精确输入配置；此方式会读取大型结果，内存开销较高
& $esPython code/project/run_es_full_ts_start_cap_old_d_20260921.py --output output/full_range_reuse_new --reuse-input-result output/full_range/ES_HISTORICAL_CONDITIONAL_ts_start__cap_old__rolling2__D.json

# 根据已归档v5结果更新中文分析报告和图表
& $esPython code/project/build_es_full_result_analysis_20260921.py
```

新运行会在自身输出目录保存输入证据，因此output中保留与历史结果配套的输入副本；input中另提供集中查阅副本。完整结果未重复复制。历史JSON中的原始来源路径和代码哈希不改写，新运行生成新指纹。

## 常用成果

- [MILP数学规格：第一版保留＋第二版完整公式](research/spain_milp_mathematical_spec_2026-09-16.md#milp-v2)：v2.0对应当前P0实现，变更带颜色标识。
- [完美预测模型优化V1：方案评估与P0数学实施细则](research/完美预测模型优化V1_方案评估与P0数学实施细则_20260922.md)：批准的设计、验收规格及实施状态索引。
- [中文结果汇总](reports/西班牙储能MILP全量测算结果汇总.md)：k€/MW、六项方向收益、收益占比和容量图表。
- [完整结果与计时](output/full_range/)：完整JSON约1.32 GB，建议日常先看final_report.json、summary.json、solver_timing.json。
- [市场来源索引](research/sources.md)、[模型适配与假设](research/es_conditional_adapter_spec_20260920.md)。
- [文件来源与SHA256](reports/file_manifest.json)：每项复制源、目标、原哈希及整理后的哈希；仅少量路径适配文件会不同。

## 整理范围及验证

Git仓库纳入代码、报告、研究资料及说明；`input/`、`output/`仅保留本地，不上传GitHub。从远程克隆后需另行准备这些数据方可运行历史测算或重建报告。

原始数据来自现有本地REE/eSIOS、OMIE等ES归档，本次未下载新数据、未重跑经济求解。研究文件保留原状态，归档不代表新增规则批准。

纳入最终v5与已选两日成果和紧凑性能证据；失败v1–v4、庞大中间快照、虚拟环境及缓存留在原目录。部分历史快照对比测试依赖这些未纳入的旧outputs，不能在整理副本中直接全量运行。

整理检查包括逐文件SHA256复制核对、Python语法解析、运行入口帮助和依赖导入、报告图片引用检查；见reports/organization_checks.json。路径调整仅用于本目录布局，未修改求解公式、参数及历史结果。
