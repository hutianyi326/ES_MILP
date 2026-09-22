# 西班牙辅助服务市场研究计划

## 1. 冻结基线

- 国家/竞价区：西班牙（ES）
- 研究主题：辅助服务市场及其直接相关的平衡能量与不平衡结算
- 历史研究期间：2025-01-01 至 2025-12-31
- 规则基准日：2026-08-11
- 研究对象：独立电化学储能
- 执行 Agent：`market_researcher`
- 建模 Agent：本阶段不启动
- 当前状态：ES-GF 已通过第三轮独立复审（P0/P1/P2=0）；西班牙研究状态转为 `research_confirmed`

## 2. 研究边界

### 2.1 核心纳入范围

1. 西班牙辅助服务的监管、市场运营和系统运营职责；
2. FCR、aFRR、mFRR、RR，以及经官方规则核实的西班牙对应产品；
3. 平衡容量采购、申报、出清、定价、可用率、容量费和罚则；
4. 平衡能量报价、激活、计量、定价、结算和未交付处理；
5. 西班牙与欧洲平衡平台的接入、角色和结算接口；
6. 不平衡责任、结算周期、方向、价格形成、更正和储能适用方式；
7. 独立储能的市场身份、BSP/BRP 关系、预认证、聚合、最小规模、遥测、计量、SOC/能量持续性和履约要求；
8. 容量需求、中标量/价、能量报价、激活量、平衡能量价格和不平衡价格的官方数据源；
9. 2025 年历史规则版本与截至 2026-08-11 的现行规则差异。

### 2.2 条件纳入范围

- 技术约束和偏差管理：只研究其与储能、平衡容量、平衡能量或不平衡结算的直接接口；
- 现货/日内接口：只有在其直接进入不平衡价格、辅助服务结算、SOC 恢复或履约规则时，才记录必要输入和依赖，不展开现货市场规则。

### 2.3 明确排除范围

- 日前市场和日内市场的申报、出清、价格及结算全流程；
- OMIE 现货产品、EUPHEMIA 和跨区现货容量分配；
- 现货套利、现货—辅助服务联合策略；
- 电压控制、无功和黑启动等非核心系统服务的详细技术与补偿机制；
- 交易策略、MILP、国家配置、生产代码、历史回测和预测模拟。

## 3. 研究和证据原则

1. 第一方资料优先级：西班牙法律/监管机关、CNMC、MITECO、Red Eléctrica、ENTSO-E、ACER及相关欧洲平衡平台规则；
2. 搜索摘要、咨询报告和新闻只能用于发现线索，不能作为关键规则的唯一证据；
3. 每项关键规则记录机构、标题、发布日期/生效日、URL、访问日期及章节/页码/表格位置；
4. 2025 历史适用规则与 2026-08-11 现行规则必须分开；
5. 严格分开规则事实、研究解释、建模假设和待确认问题；
6. 无法确认的产品名称、对应关系、参数或生效日期标为 `unresolved`，不得写入模型；
7. 西班牙本地产品与 FCR/aFRR/mFRR/RR 的对应关系必须由官方材料证明，不按名称或经验直接映射；
8. 所有时序数据必须记录时区、夏令时、分辨率、单位、币种、发布延迟和修订机制。

## 4. 阶段与门禁

### ES-00：范围冻结

责任人：主线程。状态：已完成。

输出：

- `project/scope.md` 西班牙范围段落；
- 本文件；
- `project/country_status.yaml` 的 ES 状态；
- `project/spain_research_task_ES-01.md`。

### ES-01：官方制度、产品清单与规则版本地图

责任人：`market_researcher`。状态：已完成，主线程 ES-G1 已通过（2026-08-11）。

研究内容：

- 建立机构、法律规则层级和官方资料入口；
- 建立辅助服务候选产品清单和官方术语 crosswalk；
- 识别 2025 历史规则及截至 2026-08-11 的现行版本入口；
- 建立后续容量、能量、储能、不平衡和数据研究所需的来源地图；
- 登记未能确认的范围和版本问题。

输出：

- `countries/ES/sources.md`；
- `countries/ES/open_questions.md`；
- `countries/ES/product_scope.md`。

质量门禁 ES-G1：

- 关键制度模块均有第一方入口；
- 产品对应关系有官方依据或明确标为待确认；
- 2025 历史版本和 2026 基准版本初步分开；
- 没有越界研究现货市场；
- 没有形成建模假设或修改模型代码。

审核结论：**通过**。

- 19 项第一方来源登记覆盖欧盟框架、国家监管/BOE、REE 操作入口、欧洲平台和官方数据入口；
- FCR/aFRR/mFRR/RR 与西班牙官方术语的 crosswalk 已建立；
- 2025 MARI/PICASSO/ISP/TERRE 关键版本边界已形成证据链；
- 21 项未决问题已登记，未确认内容没有转为规则参数或建模假设；
- 研究未越界进入日前、日内、策略、模型、代码或原始数据下载。

ES-01 审核记录见 `project/review_ES_01_2026-08-11.md`。独立复审维持 ES-G1，但要求 ES-02 先关闭两项 P1：补强 BOE 约束性条款证据并消除来源状态矛盾。

### ES-02：平衡容量规则

责任人：`market_researcher`。状态：已完成，主线程 ES-G2 已通过（2026-08-11）。

逐产品研究准入、预认证、采购周期、产品时段、申报、最小规模、对称性、出清、定价、容量费、可用率、未履约和罚则。

启动前置修订：

- 将 BOE-A-2024-11535 Art.7、Art.9 和 P.O.3.8 对储能 BSP、一般 1 MW 报价门槛、aFRR BSP 100 MW 条件和测试入口的约束性证据补入 ES-01 文件；
- 将 RR 储能状态改为“一般资格已确认，产品专门条件待确认”；
- 统一 `S-CNMC-2020-PO` 的标题状态和 `evidence_status`；
- 修正 FCR/ACE、RR 24 gates/96 closures/TERRE 切点、ACER IF 和 EBGL consolidated 文本的 P2 表述。

任务书：`project/spain_research_task_ES-02.md`。

输出：

- `countries/ES/balancing_capacity_rules.md`；
- 更新 `countries/ES/sources.md`、`product_scope.md` 和 `open_questions.md`；
- ES-02 规则声明、版本矩阵及后续问题清单。

质量门禁 ES-G2：

- 独立复审 P1 已关闭，P2 已处理或显式登记；
- 每个产品明确是否存在可由 BSP 竞价取得的容量收入，不把能量产品误写成容量市场；
- 2025 规则和 2026-08-11 当前规则分开；
- 储能一般准入、产品专门准入和建模参数候选分开；
- 价格、容量、产品时段、方向、门槛、罚则均有官方定位或标记为未确认；
- 不越界进入 ES-03 完整激活/能量结算、ES-05 不平衡公式、现货或建模。

审核结论：**通过**。

- 独立复审两项 P1 已关闭，四项 P2 已修正或完成来源登记；
- 已确认仅 aFRR 存在本地 D-1、QH、上/下独立、边际定价的标准平衡容量市场；
- mFRR 和 RR 在已审 2025 规则中是能量报价/激活产品，未识别独立容量采购或容量费；
- FCR 约束性文件只确认物理响应/需求入口，REE 非规范性指南描述其为并网发电机强制无偿服务；独立储能资格和补偿保持未决；
- SRAD 存在需求响应特定容量拍卖，但独立储能资格保持未决；
- 储能一般 BSP 资格、一般 1 MW 门槛、aFRR BSP 上下方向合计 100 MW 条件已有 BOE 约束性证据；
- 未越界进入完整能量激活、不平衡结算、现货、策略、模型或代码。

ES-02 审核记录见 `project/review_ES_02_2026-08-11.md`。独立复审建议为 CONDITIONAL PASS；ES-03 已完成并通过ES-G3，已关闭claim引用和Art.9(2)(d)测试例外问题。

### ES-03：平衡能量、激活与欧洲平台

责任人：`market_researcher`。状态：已完成，主线程 ES-G3 已通过（2026-08-11）。

研究能量报价、激活顺序、响应时间、持续时间、计量、边际价格、结算接口、未交付及欧洲平台接口；完整不平衡价格公式留给ES-05。

启动前置修订：

- 为ES-02中未显式挂内部source ID的claim补齐source ID、日期/生效期、URL和条款定位；
- 修正Art.9(2)(d)允许在规定比例内并入既有合格UP的测试例外；
- 修正FCR“同步发电机路径”、SRAD正式需求侧边界和来源地图陈旧引用；
- 继续维持ES-G2为条件通过，未修订内容不得成为模型参数。

任务书：`project/spain_research_task_ES-03.md`。

输出：

- `countries/ES/balancing_energy_rules.md`；
- 更新 `countries/ES/sources.md`、`product_scope.md` 和 `open_questions.md`；
- ES-03规则声明、平台/本地fallback版本矩阵及后续问题清单。

质量门禁 ES-G3：

- ES-G2独立复审P1全部关闭，P2已修正或显式登记；
- aFRR/PICASSO、mFRR/MARI、RR/TERRE和IN/IGCC分别记录本地与欧洲平台的报价、激活、门槛、时序、价格和fallback；
- 2025历史适用版本与2026-08-11当前版本分开；
- 能量价格和激活量与容量费、不平衡价格分开；
- 未交付、资格暂停和罚则仅记录规则接口，公式若属于结算模块则转ES-05；
- 不越界进入日前/日内现货完整规则、策略、模型或代码。

审核结论：**通过**。

- ES-G2前置P1/P2已处理：8条claim补齐内部source ID和完整定位，Art.9(2)(d)测试例外已加入，FCR/SRAD/ACER/来源地图措辞已修订；
- aFRR/PICASSO、mFRR/MARI、RR/TERRE、IN/IGCC及本地fallback分别建立能量规则和版本边界；
- 容量费、能量价格、激活量和不平衡结算接口已分层；
- 2025历史版本、TERRE 2025-12-30停止点和2026 RR替代未决已分开；
- 29条ES-03 claim均有内部source ID、官方日期/生效期、URL和定位；
- 未越界进入现货、策略、模型或代码。

ES-03审核记录见 `project/review_ES_03_2026-08-11.md`。ES-04 已完成并通过 ES-G4，详见下节及 `project/review_ES_04_2026-08-18.md`。

### ES-04：储能准入与技术履约

责任人：`market_researcher`。状态：已完成，独立复审 ES-G4 已通过（2026-08-18，P0/P1/P2=0）。

研究独立储能的市场身份、BSP/BRP 安排、预认证、聚合、遥测、双向计量、SOC/能量持续性、容量预留和恢复要求。

输出：`countries/ES/storage_access_technical_requirements.md`，并更新 `countries/ES/sources.md`、`countries/ES/open_questions.md`。

审核结论：**通过**。一般 1 MW、aFRR 上下方向合计 100 MW、aFRR AGC/4 秒遥测、mFRR 12.5 分钟、RR 30 分钟、双向计量/15 分钟 ISP 和履约监测已有官方定位；FCR、独立 SRAD、Art.9(2)(d) 比例、SOC/持续时长/补能、强制可用率/恢复、2026 RR 替代保持未决。15 个编号 claim 已在技术要求文件 §13.1 逐项绑定来源元数据，未越界进入现货、策略、模型、代码或回测。复审记录见 `project/review_ES_04_2026-08-18.md`。

### ES-05：不平衡结算

责任人：`market_researcher`。状态：已完成，ES-G5 第二轮独立复审已通过（2026-08-18，P0/P1/P2=0）。

研究 BRP 责任、结算周期、方向、价格形成、单/双价、净额、更正、偏差管理接口和储能适用规则。

任务书：`project/spain_research_task_ES-05.md`。完成初审后，需将 review 问题与 ES-04 未决事项统一整改并提交二次复审。

输出：`countries/ES/imbalance_settlement_rules.md`，并更新 `countries/ES/sources.md`、`countries/ES/open_questions.md`。

审核结论：**通过**。第二轮复审及整改后验证确认 13/13 claim 均具备完整机构、标题、日期/生效、URL、定位、访问日和 2025 适用性字段；DESV、单/双价、未交付支付、CET/CEST、遥测边界、aFRR 储能 BRP 特例和 BOE-A-2025-13076 版本登记均通过。ES-04 未决事项保持 `open/open-critical`，未进入现货、策略、模型、代码或回测。详见 `project/review_ES_05_initial_2026-08-18.md` 和 `project/review_ES_05_second_2026-08-18.md`。

### ES-06：官方数据目录与历史版本整合

责任人：`market_researcher`。状态：已完成，ES-G6 第二轮独立复审已通过（2026-08-18，P0/P1/P2=0）。

建立数据目录、字段字典、发布延迟和版本时间线，并形成完整西班牙辅助服务研究报告。

任务书：`project/spain_research_task_ES-06.md`。本阶段不下载或覆盖 `data/raw/` 原始时序文件，不进入策略、模型、代码或回测。

输出：`countries/ES/data_catalog_and_version_timeline.md`，并更新 `countries/ES/sources.md`、`countries/ES/open_questions.md`。

审核结论：**通过**。12 类数据集、字段字典、权限、时滞/闭算/修订/缺失、2025→2026-08-11 时间线和平台映射均完成；API 字段、历史覆盖、revision、TERRE 归档、2026 RR 替代保持 `open/provisional`。BOE-A-2026-14009 明确为 2026-09-01 future-effective，不覆盖历史期或基准日。复审记录见 `project/review_ES_06_initial_2026-08-18.md` 和 `project/review_ES_06_2026-08-18.md`。

### ES-GF：主线程研究终审

责任人：主线程。

只有第一方证据、版本边界、规则/解释/假设分层、储能规则和数据可得性均通过审核，ES 才能进入 `research_confirmed`。即使通过，也不自动批准策略或建模。

终审稿：`countries/ES/spain_ancillary_services_research.md`。终审任务记录：`project/spain_research_task_ES-GF.md`。第一轮 P1=2、第二轮 P1=1 均已整改；第三轮独立复审结论为 **PASS，P0/P1/P2=0**。西班牙研究状态转为 `research_confirmed`，但不自动批准策略或建模。

## 5. 当前执行任务

ES-GF 已通过，最终研究报告为 `countries/ES/spain_ancillary_services_research.md`。下一步须另行确认辅助服务交易策略范围；`modeling_engineer` 继续禁用，不修改 `model/`、`src/`、`tests/`、`outputs/` 或 `data/raw/`。
