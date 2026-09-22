# 西班牙门禁共同确认：本轮进度

> 2026-09-20状态入口：用户最新两版完美信息基线见 `spain_perfect_information_baseline_20260920.md`。已启动数据确定性代理复核和新数学/IO统一、独立审核；下文为2026-09-17已完成成果，不把旧预测校准要求延续为首版门禁。

日期2026-09-17。用户已确认四项原则，见 `spain_gate_confirmation_and_limited_build_20260917.md`。

## 当前成果

1. 授权和顺序讨论草案经Astra/high二轮只读审核PASS；用户随后确认先固定订单双顺序对比、待数据与本站映射验收后分别重优化。合成固定订单诊断已完成，Astra/medium二轮PASS，17项测试通过；真实历史持续时间映射与参数仍未验收。
2. 单位报告经二轮审核PASS，7份REE新原始响应hash、字节数、记录数匹配。Phase I规则结算量纲为MWh，但680/681公开字段直接单位/逐条映射、历史时段和step填补语义未闭合，G1未通过。
3. 项目隔离求解环境和合成电池MILP已实现；主线程复跑6组测试通过，包括损坏解拒绝。工程独立二轮PASS（P0/P1/P2=0），额外10类故障输入正确拒绝；主线程验收G5的合成电池基础子集，不放行完整模型。
4. 旧数学/IO不一致项已列入 `spain_spec_alignment_register_20260917.md`，G4尚未完成。旧版压力路径反馈保证不能沿用到独立事后诊断版本。

## 已确认的下一阶段路径

用户确认先以同一组固定订单作先上后下/先下后上物理对比；输入和本站映射验收后，两种顺序再各自重优化。两结果分别披露，不赋50:50权重、不选高收益作为基准。满幅持续时间映射仅在a_up+a_down≤1等前提下适用，不满足时退回研究，不裁剪数据。真实数据能否适用仍待验收，本轮只做合成假设诊断，见 `spain_fixed_order_diagnostic_plan_20260917.md`。

## 文件与检查

主线程新增授权、顺序、差异、进度及review文档；更新国家状态、决策日志及旧数学/确认文件的授权提示。

研究交付：`countries/ES/afrr_units_gate_followup_20260917.md`，7份响应另存 `data/raw/ES/esios/gate_units_20260917T083907Z/`，不覆盖旧raw；官方来源REE/eSIOS指南v1.7.2、API文档与本次指标响应，定位/日期在报告中。

工程交付：`src/es_milp_sandbox/`、`tests/test_es_milp_sandbox.py`、`model/es_milp_sandbox_readme.md`、`outputs/es_milp_sandbox/synthetic_test_results.json`，隔离依赖scipy1.15.3。通用物理关系和合成算例不是新增西班牙市场规则。

检查：初版5组正常测试通过但独立审计发现缺陷；返修后6组测试通过，包含NaN、负功率、终端SOC及二元越界的故障注入，增加solver目标与独立现金核对。未运行真实历史收益、市场耦合、年度滚动或完整场景测试。

新增固定订单诊断实现、11项测试、说明及JSON结果；加上既有6项底座回归，共17项通过。主线程结果见 `spain_fixed_order_diagnostic_results_20260917.md`，独立二轮审核见 `review_ES_FIXED_ORDER_20260917.md`。严格输入、真实触界、未激活备用头寸和连续季度衔接均检查；无真实历史收益。

完整实施和历史收益仍未放行：`implementation_approved=false`；有限合成开发单独授权。下一步为API口径证据、历史场景与本站映射校准及完整规格统一，不能把多个报告PASS合并成全模型PASS。
