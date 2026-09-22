# 西班牙储能 MILP

本目录是独立整理副本；原项目和桌面文件保留。整理日期：2026-09-22。

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

- [中文结果汇总](reports/西班牙储能MILP全量测算结果汇总.md)：k€/MW、六项方向收益、收益占比和容量图表。
- [完整结果与计时](output/full_range/)：完整JSON约1.32 GB，建议日常先看final_report.json、summary.json、solver_timing.json。
- [市场来源索引](research/sources.md)、[模型适配与假设](research/es_conditional_adapter_spec_20260920.md)。
- [文件来源与SHA256](reports/file_manifest.json)：每项复制源、目标、原哈希及整理后的哈希；仅少量路径适配文件会不同。

## 整理范围及验证

Git仓库纳入代码、报告、研究资料及说明；`input/`、`output/`仅保留本地，不上传GitHub。从远程克隆后需另行准备这些数据方可运行历史测算或重建报告。

原始数据来自现有本地REE/eSIOS、OMIE等ES归档，本次未下载新数据、未重跑经济求解。研究文件保留原状态，归档不代表新增规则批准。

纳入最终v5与已选两日成果和紧凑性能证据；失败v1–v4、庞大中间快照、虚拟环境及缓存留在原目录。部分历史快照对比测试依赖这些未纳入的旧outputs，不能在整理副本中直接全量运行。

整理检查包括逐文件SHA256复制核对、Python语法解析、运行入口帮助和依赖导入、报告图片引用检查；见reports/organization_checks.json。路径调整仅用于本目录布局，未修改求解公式、参数及历史结果。
