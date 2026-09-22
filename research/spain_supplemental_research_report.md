# 西班牙独立储能补充研究汇总报告

> **对象**：西班牙大陆竞价区独立、非水电化学储能。  
> **历史研究期**：2025-01-01—2025-12-31。  
> **规则基准日**：2026-08-11。  
> **补充核验访问日**：2026-09-03/04。  
> **范围**：仅补充核验调频/平衡服务、储能能量边界、2026 RR 与连续日内变更、项目级账户/代码和数据接口；不构成报价策略、收益测算、MILP、代码、回测或预测输入。

## 1. 执行结论

SUP-01 至 SUP-05 已按冻结顺序完成，并经独立 review agent 逐步复审通过（各步骤最终 P0/P1/P2 均为 0）。补充研究的核心结论是：

1. **资格和产品入口可以分层确认，但不能把“存在市场入口”写成独立储能已获准入。** FCR 的欧洲有限能量储备框架、aFRR/mFRR/RR 的西班牙平衡服务程序和 SRAD 的需求响应规则分别属于不同产品/资源边界；独立储能的 FCR 最终资格、SRAD 是否适用于纯独立 BESS 等事项仍按 `open-critical` 保留。[S-ENTSOE-FCR-COOP-2026][S-EU-SOGL-2017][S-CNMC-2024-MP][S-CNMC-2024-6215-PO38][S-CNMC-2023-SRAD-22497][S-REE-BAL-PART-2026]
2. **未发现西班牙统一的电池 MWh/MW 时长或 SOC 门槛。** aFRR/mFRR/RR 规则约束响应、激活和可用性；P.O.9.2 的 SOC 是遥测字段而非 SOC 门槛；SRAD 的 3 小时保持要求属于需求响应，不能移植到独立储能。[S-CNMC-2024-MP][S-CNMC-2024-6215-PO38][S-CNMC-2023-8113-PO92][S-CNMC-2023-SRAD-22497][S-CNMC-2026-14009-TELEMETRY]
3. **TERRE/LIBRA 退出不等于已确认新的 RR 产品。** 2025-12-30 为 REE/REN 最后参与时段，2026-01-01 起为 former members；BOE-A-2026-17285 撤销 P.O.3.3，但截至基准日未确认新的西班牙 RR 替代产品。mFRR、MARI 或连续日内市场不得直接当作 RR 替代。[S-ENTSOE-TERRE-2026][S-SP-BOE-2026-17285][S-SP-BOE-2026-17570]
4. **96 轮连续日内是市场时序修订，不是调频产品。** OMIE Instruction 4/2026 计划 2026-09-22 维护/切换、2026-09-23 首个交付日；截至访问日属于未来计划，不能回填 2025。[S-SP-OMIE-INST4-2026][S-SP-BOE-2026-17570]
5. **项目不能用一个市场代码代表全部身份。** 设施/计量、UF、送出/吸收 UP、OMIE UO、PM/BSP/BRP、EIC/mRID 和结算文件属于不同层次；纯独立 BESS 的实际代码、CUPS/CIL、激活 mRID、SIMEL 和 BRP 私有文件没有公开总表。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES][S-REE-SIMEL-FAQ-STORAGE-2026][S-ENTSOE-MRID-2024]
6. **公开接口可支持规则核验，但不能自动生成项目级审计链。** 数据日期、交付日期、发布日期/发行时间和访问时间必须分开保存；`Europe/Madrid` 的 CET/CEST 偏移、23/25 小时日、15 分钟/小时聚合和未来版本需按数据集逐项核验。[S-REE-ESIOS-API-2026][S-REE-DST-2025][S-SP-OMIE-PUBFILES-2025][S-ENTSOE-TP-QUERY-2025]

## 2. 五步执行与审核状态

| 步骤 | 内容 | 交付文件 | 最终审核 |
|---|---|---|---|
| SUP-01 | FCR/SRAD 资格与预认证 | [supplemental_fcr_srad_eligibility.md](supplemental_fcr_srad_eligibility.md) | [review_SUP_01_final_2026-09-03.md](../../project/review_SUP_01_final_2026-09-03.md)：PASS |
| SUP-02 | SOC、持续时长、补能与恢复 | [supplemental_storage_energy_requirements.md](supplemental_storage_energy_requirements.md) | [review_SUP_02_final_2026-09-03.md](../../project/review_SUP_02_final_2026-09-03.md)：PASS |
| SUP-03 | 2026 RR 替代与 96 轮日内修订 | [supplemental_rr_2026_transition.md](supplemental_rr_2026_transition.md) | [review_SUP_03_final_2026-09-03.md](../../project/review_SUP_03_final_2026-09-03.md)：PASS |
| SUP-04 | 项目级账户与代码映射 | [supplemental_account_code_crosswalk.md](supplemental_account_code_crosswalk.md) | [review_SUP_04_final_2026-09-03.md](../../project/review_SUP_04_final_2026-09-03.md)：PASS |
| SUP-05 | 数据接口、版本、DST 与权限 | [supplemental_data_interface_validation.md](supplemental_data_interface_validation.md) | [review_SUP_05_final_2026-09-04.md](../../project/review_SUP_05_final_2026-09-04.md)：PASS |

每步均先由主线程检查，再经 review agent 复审；首轮发现的 P1/P2 已在同一步修订并二次复审关闭。

## 3. 规则事实、研究解释与建模边界

### 3.1 规则事实（F）

- 西班牙平衡服务、系统运行程序和市场规则分别规定产品入口、参与主体、计划、激活、计量和结算流程；具体条款以各 SUP 文件和 `countries/ES/sources.md` 为准。[S-CNMC-2024-MP][S-CNMC-2024-6215-PO38][S-CNMC-2023-8113-PO92][S-SP-BOE-2025-RULES][S-REE-LIQ-GUIDE-2024]
- 独立储能的送出/吸收 UP 结构、UP/UF 与 EIC 的关系、OMIE UO 与 UP 的注册关联、PM/BSP/BRP/代表的法律角色可由已登记的 BOE/CNMC、REE、OMIE 资料确认。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES]
- eSIOS/REE、OMIE 和 ENTSO-E 提供公开接口或文件格式；详细 BRP 结算 ZIP、SIMEL 项目资料和部分注册/激活消息属于受限或项目级信息。[S-REE-ESIOS-API-2026][S-SP-OMIE-PUBFILES-2025][S-REE-LIQ-ACCESS-2026]

### 3.2 研究解释（I）

- “项目—UF—UP—UO—报价/计划—激活—计量—BRP 偏差—结算”是跨机构归档和审计的建议身份链，不创造新的市场代码。
- 将送出 UP 与吸收 UP 分开保存、将本地时间与 UTC 同时保存、将公开文件与私有结算文件分开，是数据治理建议，不是额外市场准入条件。
- CUPS/CIL 在特定登记或计量流程中出现，但已审公开资料尚未确认其对纯独立 BESS 的普遍适用路径；不能从发电案例反推。[S-REE-ADMISSION-GUIDE-2024][S-REE-SIMEL-FAQ-STORAGE-2026][S-REE-PF-CIL-2015]

### 3.3 建模假设（A）

本补充报告不新增可执行模型参数。未来如需简化为一个技术单元、一个 BRP、固定 SOC、固定持续时长、静态代码或某个公开指标，必须另行登记假设并取得项目级文件；不得把研究解释直接写入模型。

### 3.4 待确认（U）

未闭合的项目级资格、代码、指标和权限继续保持 `U/open` 或 `U/open-critical`。`open-critical` 事项关闭前不得写入国家模型配置、收益公式、策略或回测。

## 4. 分步骤要点

### 4.1 SUP-01：FCR/SRAD 资格与预认证

- **F**：FCR 的有限能量储备框架来自 SOGL/欧洲合作规则；西班牙 SRAD 是独立的需求响应产品，REE/CNMC 资料规定其参与、测试、计量和可用性框架。[S-EU-SOGL-2017][S-ENTSOE-FCR-COOP-2026][S-CNMC-2024-MP][S-CNMC-2023-SRAD-22497][S-CNMC-2024-SRAD-CAP-24096]
- **I**：不能因为某产品存在合格服务提供方入口，就推定纯独立 BESS 已完成 FCR 或 SRAD 预认证；需区分 PM/BSP 角色、资源类型和产品测试。
- **U**：独立储能 FCR 最终激活期、SRAD 对纯独立 BESS 的资格、容量上限/测试细节和项目级登记回执未公开闭合。[S-REE-BAL-PART-2026]

### 4.2 SUP-02：SOC、持续时长、补能与恢复

- **F**：aFRR/mFRR/RR 文件给出响应和激活时序；P.O.9.2 的 SOC 字段属于遥测；2026-09-01 的实时信息修订不得倒填 2025 或 2026-08-11。[S-CNMC-2024-MP][S-CNMC-2024-6215-PO38][S-CNMC-2023-8113-PO92][S-CNMC-2026-14009-TELEMETRY]
- **I**：没有证据支持“西班牙所有独立储能统一配置 X 小时”或“统一 SOC 下限/上限”。SRAD 的 3 小时要求属于需求响应，不能移植为电池时长。
- **U**：产品级能量充足性、激活后补能/恢复、跨产品 SOC 责任和最终处罚路径仍需产品/项目文件确认。[S-EU-SOGL-2017][S-ACER-2026-FCR-MIN-ACT]

### 4.3 SUP-03：TERRE/RR 与 96 轮连续日内

- **F**：TERRE/LIBRA 于 2025-12-30 10:00 CET 停止，REE/REN 最后参与时段为 09:00—10:00 CET；2026-01-01 起为 former members。[S-ENTSOE-TERRE-2026]
- **F**：BOE-A-2026-17285 使 P.O.3.3 失效；BOE-A-2026-17570 属市场规则层，二者不能合并为“新 RR 产品已上线”。[S-SP-BOE-2026-17285][S-SP-BOE-2026-17570]
- **F/I**：96 轮连续日内按 15 分钟合同逐轮关闭；正常日 96 轮，夏令时短日/长日为 92/100；该变更是现货日内时序修订，不是平衡产品。[S-SP-OMIE-INST4-2026][S-SP-BOE-2026-17570]
- **U**：新 RR 替代产品名称、平台、资格、报价、激活、计量、结算和罚则，以及 96 轮实际 go-live 后的完整文件链，仍需官方运行证据。

### 4.4 SUP-04：项目级账户和代码

- **F**：UP 是计划基本单元，UP 可由 UF 组成；独立非水电储能原则上按送出/吸收方向组织 UP；UP/UF 使用 EIC；OMIE UO 与 UP 存在注册关联。[S-SP-PO31-2024-STORAGE][S-REE-PARTICIPANT-2026][S-REE-EIC-2026]
- **F**：Rule 12 区分注册关联层的 biunívoca 关系与代表执行层的聚合限制：仅间接代表可在一个 UO 聚合多个被代表程序，直接代表受单一被代表程序限制。[S-SP-BOE-2025-RULES]
- **I/U**：CUPS/CIL、mRID、SIMEL 点位、激活资源 ID、CCGD/调节区/组合代码和 BRP 私有结算字段不能从公开网页推导出一个真实项目的完整 crosswalk。[S-REE-SIMEL-FAQ-STORAGE-2026][S-ENTSOE-MRID-2024][S-REE-LIQ-ACCESS-2026]

### 4.5 SUP-05：数据接口、版本、DST 与权限

- **F**：REE REData/eSIOS、OMIE 公共文件和 ENTSO-E 平台均提供不同层级的公开查询/文件入口；eSIOS 区分指标查询与归档的 `datos`/`publicacion` 日期字段。[S-REE-REData-API-2026][S-REE-ESIOS-API-2026][S-REE-ESIOS-ARCHIVE-API-2026]
- **F**：`Europe/Madrid` 冬季偏移为 CET（UTC+1）、夏季偏移为 CEST（UTC+2）；2025-03-30 与 2025-10-26 分别为 23/25 小时日。应保留本地 offset、UTC、市场/交付日期和数据集自身时段标签。[S-REE-DST-2025][S-SP-OMIE-FORMATS-2024][S-ENTSOE-TP-QUERY-2025]
- **I/U**：公开目录出现 2025 文件不等于全年逐项完整或不可修订；指标 ID、单位、最终性、缺失/估算标志、API 限额、SIMEL/BRP 权限和历史版本仍需逐项核验。[S-SP-OMIE-PDBC-ARCHIVE-2026][S-REE-LIQ-GUIDE-2024][S-REE-LIQ-ACCESS-2026]

## 5. 未决事项与后续取证

下表仅列核心未决族，完整问题 ID 和证据边界见 `countries/ES/spot_open_questions.md`。

| 未决族 | 代表问题 ID | 当前状态 | 关闭所需资料 |
|---|---|---|---|
| 独立储能 FCR/SRAD 资格、预认证和激活期 | ES-SUP-01-Q01—Q10、ES-SUP-02-Q04/Q08 | open-critical | REE/BSP 资格回执、测试/预认证结果、产品适用声明 |
| SOC、持续时长、补能/恢复和可用率 | ES-SUP-02-Q01—Q13 | open/open-critical | 产品技术规范、激活记录、补能/恢复规则、处罚/不支付通知 |
| RR 替代产品和 96 轮实际运行 | ES-SUP-03-Q01—Q10 | open-critical | 新 RR 官方规则/产品文件、REE/平台运行公告、实际文件样例 |
| 项目级账户/代码 crosswalk | ES-SUP-04-Q01—Q10 | Q01/Q04/Q05/Q06/Q07/Q09 为 open-critical；其余为 open | REE UP/UF/EIC 回执、OMIE agent/UO 注册、代表/BRP/BSP 合同、SIMEL/计量和激活样例 |
| API 指标、版本、DST 和权限 | ES-SUP-05-Q01—Q10 | Q01/Q02/Q04—Q10 为 open-critical；Q03 为 open | 逐指标元数据、归档盘点、DST 文件抽样、版本/修订记录、项目私有 API/结算权限 |

## 6. 来源和证据管理

- 关键来源优先采用 CNMC/BOE、REE、OMIE、MITECO、ENTSO-E 和 ACER 的第一方资料；每个 `S-*` source block 在 [sources.md](sources.md) 记录机构、标题、发布日期/生效关系、URL、访问日、条款/页码/API 定位、2025 适用性和证据状态。
- 本报告只引用来源 ID，不重复展开完整元数据；如需逐条复核，应以 `countries/ES/sources.md` 为准。
- 规则事实、研究解释、建模假设和待确认事项分离；任何无法确认的内容均标记 `U`，没有为模型补齐缺失规则。

## 7. 建模门禁

本补充研究完成不等于建模批准。西班牙 `country_status.yaml` 继续保持 `status: research_confirmed`、`modeling_approved: false`。在用户/主线程另行立项并完成交易策略、MILP、输入输出规范、代码实现、历史测算、预测模拟和验证前，不得将本报告或任何 `open-critical` 项目写入模型配置。
