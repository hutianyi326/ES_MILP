# ES-01/ES-02 辅助服务产品范围与术语 crosswalk

> 仅建立官方名称与欧洲标准产品的候选对应和研究范围；不提前给出 ES-02/ES-03 的完整参数、结算公式或建模参数。`confirmed` 表示官方材料直接使用“对应/等效”表述；`provisional` 表示官方入口已找到但版本/运行细节待后续核对；`unresolved` 不得写入模型。

## 1. 官方 crosswalk

| 欧洲标准/流程 | 西班牙官方名称（西语） | 官方依据与定位 | 容量采购 | 能量报价/激活 | 不平衡接口 | 独立电化学储能范围状态 |
|---|---|---|---|---|---|---|
| FCR（Frequency Containment Reserves） | Regulación primaria / reserva de regulación primaria | **S-CNMC-2024-MP** Art.5(1); **S-CNMC-2024-11535-PO** P.O.1.5 §§4.1（primary requirement/response）; **S-REE-GUIDE-2024** v5.0 Dec-2024 pp.9-10 | REE 非规范性指南将 primary 描述为**并网发电机/调速器路径**的强制、无偿自动响应；约束性 P.O.1.5 仅确认年度需求和物理响应，尚无面向 BSP 的可竞价容量采购证据 | 物理频率响应；不直接恢复 ACE，也不是独立 BSP 能量或不平衡结算产品 | 通过本地/同步区频率响应稳定频率；ACE 恢复由后续 aFRR/mFRR 等承担 | `unresolved`：Art.7 一般允许储能持有人成为 BSP，但 P.O.7.1/3.8 尚未确认独立电池可作为 primary provider 或取得补偿 |
| aFRR（automatic Frequency Restoration Reserves） | Regulación secundaria / reserva automática para la recuperación de la frecuencia | CNMC 2024 BOE Arts.7(1)(c), 7(4)-(5), 9, 10; P.O.7.2 §§5.1-5.3/Annex I; REE Guía pp.10-12 | **已确认本地 aFRR reserve/capacity market**：上、下独立，D-1每日、每15分钟，边际价格容量费 | 容量中标后至少提交相同量的aFRR能量支持报价；PICASSO自2025-06接入 | aFRR 自动恢复频率/交换计划；IN/IGCC仅为跨TSO netting接口 | `confirmed`（一般储能参与原则）：storage可成为BSP，UP/BSP一般≥1 MW；aFRR BSP总上/下已 habilitado reserve 合计≥100 MW；产品测试、SOC和持续时间留 ES-04 |
| mFRR（manual Frequency Restoration Reserves） | Regulación terciaria / reserva manual para la recuperación de la frecuencia | CNMC 2024 BOE Art.5(1), P.O.7.3 pp.155-160; BOE-A-2025-5342 §§1362-1395; REE Guía pp.12-13 | **未发现独立 mFRR 容量采购/容量费**：P.O.7.3公布次日备用需求，但要求提交可用备用的能量报价（MW+€/MWh）；不将“reserva disponible”视为容量中标 | 手动mFRR能量报价/激活，MARI自2024-12；本地算法为故障后备 | mFRR激活和履约由P.O.7.3/14.4结算；完整能量激活留 ES-03 | `confirmed`（一般储能参与原则）：storage可申请并需 habilitación；≥1 MW一般门槛；SOC/持续供能和技术测试留 ES-04 |
| RR（Replacement Reserves） | Reservas de sustitución; 旧称 gestión de desvíos | CNMC 2024 Art.5(1-2); BOE-A-2025-5342 P.O.3.3 §§13.1、Annex I（pp.123-127）; S-ACER-RR-IF; S-ENTSOE-TERRE-2026 | **未发现独立 RR 容量采购/容量费**：P.O.3.3仅规定“ofertas de energías de balance”并按€/MWh激活结算；2025 TERRE运行至12-30 | 2025 RR标准能量产品，FAT 30 min、最小1 MW；24个小时级activation horizons与96次连续日内闭市是不同条件 | 2025-12-30 TERRE停止；2026替代机制未确认，不能外推 | `confirmed_general/unresolved_product`: 2025储能一般BSP/测试入口已由Art.7/9确认；P.O.3.3/3.8的储能专门SOC、持续时间、未交付细则仍待确认 |
| IN（Imbalance Netting） | Compensación de desequilibrios / proceso IN（IGCC） | S-ACER-IN-IF; CNMC 2022 BOE §§3224-3235; REE platforms page | **非BSP容量市场**；是TSO-TSO netting过程，储能不能单独报价取得容量费 | 自动净额aFRR需求，不是本地储能能量产品 | 影响aFRR需求与TSO-TSO结算接口；不直接构成储能收入产品 | `out_of_scope_for_direct_storage`：仅保留aFRR/BRP接口 |
| 本地特定产品 | Servicio de Respuesta Activa de la Demanda（SRAD） | **S-SRAD-2025**（BOE-A-2025-22853）P.O.7.5 §§119-138, 167-179, 217-225; **S-SRAD-2026**（BOE-A-2026-10602）P.O.7.5 §§124-138；**S-REE-FAQ-2026** pp.13-14 | **有容量拍卖/容量费**：2025适用年度拍卖框架；2026起原则上六个月、可两次/年，容量按MW及边际拍卖价支付 | mFRR-like手动激活、单独P.O.7.5/14.4结算；正式对象为需求UP/需求响应。独立储能能否作为需求UP参加未由上述公开条文确认，不能从标准储能BSP资格推断 | 仅为需求响应特定产品，解决tertiary up reserve不足 | `unresolved`：独立储能是否能以demand/storage身份参加不得从标准产品储能资格推断 |

## 2. 研究范围分类

### 核心纳入（本轮及后续 ES-02—ES-06）

- FCR/ regulación primaria：仅保留强制/无偿制度入口、是否允许独立储能及补偿状态；完整技术参数在 ES-04 核实。
- aFRR/ regulación secundaria：容量市场及容量收入已在 ES-02 确认；能量激活、PICASSO/IGCC 接口、计量和履约继续分层研究。
- mFRR/ regulación terciaria：ES-02确认未发现独立容量市场；能量报价/激活、MARI、备用算法、未交付和结算留 ES-03。
- RR/ reservas de sustitución：ES-02确认2025为TERRE能量产品而非容量市场；保留2025-12-30断点，2026替代机制须另找官方版本。
- IN/IGCC：仅作为系统 aFRR 需求和不平衡/TSO-TSO 结算接口。
- BRP/BSP、不平衡责任、15 分钟 ISP、储能双向计量和数据。

### 条件纳入

- 技术约束（restricciones técnicas）：REE 页面确认 generation/demand/storage 可被限发/改程序；仅研究其对平衡资格、储能程序和履约的直接接口。
- SRAD：本地特定产品；登记规则版本和储能资格问题，不在本轮提取完整拍卖参数。
- 聚合：CNMC 2019/2024 条件允许 generation、demand、storage aggregation；具体 UP/BSP 结构、同组限制和最小规模留 ES-04。

### 仅登记、不展开

- 电压/无功控制、黑启动、完整非频率服务：REE regulatory framework 将其列为另一套“Condiciones servicios no frecuencia”，本项目只保留入口。
- 日前/日内市场、OMIE/EUPHEMIA、跨区现货容量分配：不展开；仅在RR证据中区分24个activation horizons与96次连续日内闭市触发条件。

## 3. 版本边界（产品层）

| 产品 | 2025 历史适用入口 | 2026-08-11 现行入口/边界 | 状态 |
|---|---|---|---|
| FCR/primary | CNMC 2024 条件 + P.O.1.5/7.1入口；REE guide Dec-2024（非规范性） | REE指南所述强制、无偿并网发电机响应；独立储能产品资格未闭合 | `provisional/unresolved` |
| aFRR/secondary | CNMC 2024 Art.10 + P.O.7.2市场；PICASSO 2025-06 接入 | 本地容量市场（上/下独立、D-1/QH、边际容量费）与PICASSO能量市场分开 | `confirmed` capacity market; storage product parameters pending |
| mFRR/tertiary | P.O.7.3 BOE-A-2024-11535 pp.155-160；MARI 2024-12 | 仅备用/能量报价和激活；未发现独立容量采购市场 | `confirmed` no separate capacity market; energy details pending |
| RR | P.O.3.3 BOE-A-2025-5342 pp.123-127；TERRE until 2025-12-30 | 仅RR能量报价；24 horizons≠96 closures；2026替代路径 unresolved | `confirmed` 2025 energy product; `unresolved` 2026 |
| IN | IGCC since 2020-10; CNMC 2022/REE pages | current IGCC/TSO-TSO settlement source to verify | `provisional` |
| SRAD | BOE 2025-22853 published Nov-2025; service delivery from 2026-01-01 | BOE 2026-10602 effective 2026-05-16; confidential annexes | `conditional`, storage eligibility unresolved |

## 4. 术语和数据标签约定（供后续模块使用）

| 统一标签 | 西班牙语原文 | 不得混淆 |
|---|---|---|
| `FCR_primary` | reserva/regulación primaria | 与aFRR secondary band分开；primary是并网发电机/调速器路径的物理频率响应（REE指南层级），不直接恢复ACE或进入BRP不平衡结算 |
| `aFRR_secondary` | regulación secundaria / reserva automática | 本地 capacity market 与 PICASSO energy activation 分开 |
| `mFRR_tertiary` | regulación terciaria / reserva manual | mFRR 标准产品与 SRAD 特定产品分开 |
| `RR_replacement` | reservas de sustitución / gestión de desvíos（旧称） | 2025 TERRE能量产品、24 activation horizons与96连续日内闭市分开；2026后续机制分开 |
| `IN_IGCC` | compensación de desequilibrios | TSO-TSO netting，不是 BSP 储能投标产品 |
| `SRAD_specific` | servicio de respuesta activa de la demanda | P.O.7.5正式对象为需求UP/需求响应；不能自动等同独立储能资格，公开文本未闭合storage作为demand UP路径 |
| `BSP` | proveedor de servicios de balance | 供应平衡容量/能量；与 `BRP` 财务偏差责任分开 |
| `BRP` | sujeto de liquidación responsable del balance | 对偏差承担财务责任；可由代表承担 |
| `UP/UF` | unidad de programación / unidad física | 储能聚合和 BSP 结构的西班牙本地单位 |

## 5. 未确认项（禁止作为模型参数）

1. 独立电化学储能是否可直接提供 FCR/primary，以及适用 P.O.7.1/3.8 测试、SOC 和持续时间。
2. 2025 年 RR/TERRE 对 storage 的正式产品最小功率（一般1 MW已确认）、预认证、双向报价和未交付规则；REE guide 的一般“storage可成为BSP”不能替代产品专门条款。
3. TERRE 关闭后（2026-01-01 起）西班牙 RR/替代服务的有效 P.O.、平台或本地 fallback。
4. SRAD 法定“需求响应”产品是否允许独立储能以 demand/储能身份参加；2026 版保密附件的实际参数。
5. 2025/2026 aFRR capacity market 的100 MW BSP条件已由Art.7(5)确认（上/下方向合计）；仍需核实聚合储能具体过渡、资格保持及当前P.O.修订。
6. REE/eSIOS 数据门户的 API 字段、时区（CET/CEST）、15 分钟分辨率、发布延迟、修订号及 2025 历史覆盖。
