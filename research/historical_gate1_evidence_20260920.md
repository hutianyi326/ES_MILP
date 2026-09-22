# 西班牙门禁一：历史激活数据口径复核

> 同日后续补充：主线程现已直接读取四指标当前官方页面，单位680/681为MWh、632/633为MW。见 `project/esios_indicator_browser_evidence_20260920.md`。下文“未独立复核的当前页面线索”保留前轮审核时点的事实，不再代表最新主线程见证状态；历史单位适用范围、时间边界和统计总体仍未放行。

核查日期：2026-09-20（Asia/Shanghai）。目标：Madrid当地2025-01-01至2026-08-31。范围：680/681激活能量、632/633备用容量的单位、时间边界和统计总体。仅研究证据，不修改原始数据、模型或真实回测批准。

## 1. 最终结论

| 子项 | 状态 | 边界 |
|---|---|---|
| 官方aFRR结算规则量纲 | PASS（规则层面） | MWh；不能自动等同于680/681历史API字段合同 |
| 680/681指标级历史单位 | PARTIAL，尚未关闭 | API可复核标签为Energía，尚缺适用于目标历史序列的直接单位/正式字典证据 |
| 当前分析页单位 | 研究者观测，未独立复核 | 不作为门禁关闭证据 |
| datetime_utc起点/终点 | BLOCKED | 不擅自平移15分钟 |
| 632/633与680/681统计总体可比性 | BLOCKED | 不因方向和地理标签相同就假定分子分母可比 |
| 门禁一整体 | BLOCKED | 真实历史MILP不放行 |

**审计更正**：研究初稿曾将当前eSIOS分析页的MWh展示记为PASS。研究者报告使用浏览器读取，但未向主线程及独立review交付可直接核验的原始DOM结果或截图；主线程和review重复访问未取得可读正文，review未发现可访问的浏览器标签。因此撤回该PASS，保留为线索。访问失败不证明网页不存在，同样，文字转述也不能冒称独立核验。即使以后核验当前展示，仍须说明其对目标历史字段的适用范围。

## 2. 已核验的官方证据

### 2.1 REE结算检查指南

机构：REE。文件：Guía de ayuda para la comprobación de la liquidación de los servicios de ajuste del sistema。文件标注2024年12月。访问2026-09-20。

[官方PDF](https://www.ree.es/sites/default/files/12_CLIENTES/Documentos/normativa_guias/Guia_comprobacion_liquidacion_servicios_ajuste_sistema.pdf)

定位采用一基PDF viewer页码：

- viewer5：BRP摘要由UP、BRP和aFRR BSP等结算单元记录汇总。
- viewer6–7：按UP或UP_BSP及调度期间呈现能量和价格。
- viewer7：示例列明Energía (MWh)、Precio (EUR/MWh)、Importe (EUR)；该示例不是680/681接口字典。
- viewer17：reganecu/reganecuQH字段含MWh能量、EUR/MWh价格及结算归属信息。

结论：结算文件明确使用MWh，并存在不同参与者汇总层级，但未给680/681到该文件的指标级对应关系。

### 2.2 REE SRS实施指南

机构：REE/eSIOS。文件：Guía de implantación del Servicio de Regulación Secundaria en el sistema eléctrico español，2024年10月版。访问2026-09-20。

[官方指南](https://api.esios.ree.es/documents/2399/download?locale=es)

定位：PDF viewer53附近的ESECS/ESECB及控制周期汇总定义；网页抽取零基P52不能写成viewer52。未进一步独立确认的印刷页号不使用。

规则量纲为MW×秒÷3600=MWh；上、下调结算能量按QH汇总。该版本属于本地Phase I，不能单凭它证明PICASSO接入后每个公开API指标的历史统计定义。

### 2.3 2025决议的P.O.9.1公开信息条款

机构：CNMC/BOE。文件：Resolución de 12 de junio de 2025，BOE-A-2025-13076，公布2025-06-26。访问2026-09-20。

[官方PDF](https://www.ree.es/sites/default/files/2025-07/BOE-A-2025-13076.pdf)

该决议修改P.O.3.1、3.6、7.4、9.1和14.4，不能把整份文件称为“P.O.7.2 2025版”。

定位：P.O.9.1附件I §1.13.3，viewer90–91，BOE印刷84822–84823。条款区分半岛系统aFRR总量/加权价格、参与者结果和BSP结果，并说明接入PICASSO后的价格涉及欧洲平台边际价格。

研究解释：系统地理总量与参与者结算结果有不同统计层级。该规定本身不能判定680/681究竟包含何种跨境、无容量中标者或其他成分，更不能证明它与632/633分母同口径。

### 2.4 REE平台接入信息

机构：REE，Participa en los servicios de balance，持续维护页面；访问2026-09-20。

[官方页面](https://www.ree.es/es/clientes/consumidor/participacion-en-servicios-de-balance)

页面记录2025年6月接入PICASSO。更精确的连接日期及规则切片参见本轮Gate2报告。连接日期不替代指标单位或时间边界说明，也不要求本阶段重建逐4秒实际激活序列。

### 2.5 eSIOS API文档

机构：REE/eSIOS，无明确发布日期；访问2026-09-20。

[日期筛选与magnitud](https://api.esios.ree.es/doc/indicator/getting_a_specific_indicator_with_magnitud_and_filtering_values_by_a_certain_datetime.html)、[日期范围接口](https://api.esios.ree.es/doc/indicator/getting_a_specific_indicator_filtering_values_by_a_date_range.html)。

参数/返回示例涉及datetime、datetime_utc、start_date、end_date、time_agg、time_trunc和magnitud，支持fifteen_minutes分组。已查文档未明确680/681历史数值单位、QH起点/终点或与632/633统计总体的对应。

不使用前填时，step_type的保持/插值定义不是单独前置门禁；不能把它和必须确认的时间区间边界混为一谈。

## 3. 未独立复核的指标页线索

研究Agent报告通过站内搜索进入以下页面，看到680/681的MWh、632/633的MW及15分钟分组：

- [680](https://www.esios.ree.es/es/analisis/680)
- [681](https://www.esios.ree.es/es/analisis/681)
- [632](https://www.esios.ree.es/es/analisis/632)
- [633](https://www.esios.ree.es/es/analisis/633)

该报告目前只有研究者文字叙述，没有供主线程/review直接核验的DOM片段或截图。以上链接可作为后续入口，**不把相应单位展示记为已独立通过，也不将当前样例值回写历史输入**。后续若取得可审页面或下载文件单位，即可评估单位子项，不强制必须映射到ESECS/ESECB某个指定变量。

## 4. 原始数据和条件性诊断

项目已有raw元数据把632/633标为Potencia、680/681标为Energía，方向在名称中，地理为Península。目标期四指标共同显式交集57,069，条件性可映射57,065；原四指标候选129段见旧门禁报告及JSON。

本轮全市场重算加入价格、取消状态和合同边界后为146段、52,375个条件性时段，详见 project/spain_historical_joint_coverage_20260920.md。这两组统计范围不同，不能混用，也都不是已验收生产数据。

时间戳排列与起点解释相容，不构成官方起点证明。当前仅按原索引做条件性覆盖诊断，不移动时间、不归一化alpha、不把大于1的点裁回1。

## 5. 分层和剩余最小工作

规则事实：结算资料以MWh计量并区分系统、参与者和BSP信息层级。

研究解释：指标名称、方向、地理标签可支持发现映射线索，不能替代单位、时间和总体证据。

既定建模假设：系统平均强度作为本站代理；历史alpha进入事后完美信息优化；固定U/D两路径分别计算。它们不等于本站实测，不要求逐4秒日志或实际内部先后重建。

仍需取得：

1. 指标本身的官方单位/正式字典/可审下载说明及历史适用范围；或可用字段交叉证据，不强制指定内部变量。
2. datetime_utc代表的区间起止和边界归属。
3. 四指标统计总体及PICASSO前后可比性，明确无同向容量中标者、跨境交换等是否纳入。
4. 与Gate2规则/事件/价格联合验收后，才生成正式有效输入区间。

## 6. 检查与交付边界

新增本报告；读取既有门禁报告、用户确认、raw示例及官方网页/PDF。独立review已核对结算规则和多程序来源归属；指标分析页观测未独立复核，按上文降级。没有新API数据下载、原始文件覆盖、凭据输出、模型改动或真实收益运行。

```text
rule_energy_unit                    = PASS (rule-level MWh)
current_display_unit                = UNVERIFIED_RESEARCH_OBSERVATION
historical_indicator_unit_mapping   = PARTIAL
datetime_utc_start_end_semantics     = BLOCKED
scope_comparability                 = BLOCKED
gate_1_overall                      = BLOCKED
historical_MILP_authorization        = NOT_GRANTED
```
