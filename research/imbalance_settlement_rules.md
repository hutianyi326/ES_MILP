# ES-05 西班牙不平衡结算与独立储能接口

> 研究对象：西班牙半岛电力系统、独立电化学储能；历史期 2025-01-01—2025-12-31，规则基准日 2026-08-11。本文只覆盖 BRP/BSP、平衡激活与不平衡结算接口；不展开日前/日内市场交易规则、策略或模型。访问日期：2026-08-18。

## 1. 规则版本和适用边界（规则事实）

1. **ISP15 的时间线。**《EBGL》Art.53要求15分钟ISP；西班牙原获临时例外。CNMC Resolución 3-10-2024（BOE-A-2024-20995）规定 ISP15 版本的 P.O.14.1/14.4 自 **2024-12-01** 生效。因此 2025 年初已经按15分钟计算偏差。该决议的 P.O.14.4 版本随后由 CNMC Resolución 6-03-2025（BOE-A-2025-5342）替代；后者将生效日绑定为 OMIE 宣布的 MTU15 投产日（Resuelve Primero），没有在决议中给出固定日。2025 年回测必须保存版本切片，不能把 2025-5342 追溯到 1 月 1 日。
2. **计量实施。**MITECO Resolución 28-03-2025（BOE-A-2025-6693）自 **2025-05-01** 生效，批准 P.O.10.1/10.2/10.4/10.5/10.6/10.11 的15分钟计量、最佳能源值、发布和更正流程；其前言确认 2024-03-01 起 RR/tertiary 等服务已可使用15分钟表计验证。计量规则生效日与 ISP15 结算生效日不同。
3. **版本风险。**BOE 页面显示 2025-5342 的 P.O.14.4 又由 2025-06-12 的电压控制决议（`S-CNMC-2025-VOLTAGE-13076`，BOE-A-2025-13076）部分替换/修改，且 2026 年仍有后续修订。本文仅提取 2025-5342 中不平衡核心条款；具体交易日的有效文本需按 BOE“effects/references posteriores”核对。

## 2. BRP、BSP、储能持有人和代表

### 2.1 规则事实

| 项目 | 已确认规则（2025适用） | 官方定位 |
|---|---|---|
| BRP 身份 | 参与者必须自己成为 BRP，或以合同方式把责任委托给所选 BRP；每个 BRP 对偏差承担财务责任并向连接 TSO 结算。 | S-CNMC-2024-MP Art.16(3)(g), Arts.17–18；S-CNMC-2025-QH P.O.14.4 §2.3（BOE HTML §§1695–1699） |
| 储能 BRP 选择 | 一般规则允许储能设施持有人成为其设施 BRP 或委托其他 BRP；储能连接被视为该设施全部边界点集合。对属于 aFRR BSP 的储能，2024-20995 版本 P.O.14.4 §3.2 另有服务特例：BRP 须委托给 BSP 持有人，不能按一般路径另选 BRP；后续版本和具体日期仍须逐日切片核对。 | 一般路径：S-CNMC-2024-MP Art.16(1),(3)(g)（BOE §§757–770）；aFRR 特例：S-CNMC-2024-ISP15 P.O.14.4 §3.2 |
| BSP 与 BRP 分离 | BSP 是向 TSO 提供平衡能量/备用的市场参与者；被激活的 BSP 能量先分配给“BSP同时为BRP”的 BRP，否则分配给 BSP 按 P.O.14.1 指定的 BRP。 | S-CNMC-2024-MP Arts.12–13（BOE §§718–729） |
| 储能 UP/方向 | 每个连接的进入（充电）和流出（放电）测量分别分配到对应方向的 UP；UP 的聚合按 generation、demand、storage 活动类型分开。 | S-CNMC-2024-MP Art.8(2)、Art.16(1)–(2)（BOE §§676–684、757–760）；S-MITECO-2025-ISP P.O.10.5 表/§4.9 |
| 计划修改 | BRP 可在日内跨区闭市前通过日内交易修改计划；闭市后仅可在 P.O.3.1 规定条件下进行内部平衡修改，且需向 OS 通报。 | S-CNMC-2024-MP Art.20（BOE §§789–796） |

### 2.2 研究解释

- BSP 能量收入与 BRP 偏差成本是两本账：激活能量按 P.O.14.4 作为 BSP/UP 的收付款；同一激活量同时进入其 BRP 的 `AJUDSV`（偏差调整），避免把激活收入和不平衡价格相加为一笔。
- “储能可成为 BRP”是一般责任路径，并不证明储能已获得 FCR、aFRR、mFRR、RR 或 SRAD 的产品资格；SOC、持续时长、补能、可用率、FCR/SRAD资格仍按 ES-04 未决事项处理。

## 3. 计划、实际、激活、偏差和储能计量

### 3.1 规则事实

1. **符号和单位（P.O.14.4 §3.1–3.2）。**发电/进口为正，消费/出口为负；上调（增发/增进口/减消费/减出口）为正，下调为负。能源以 MWh（最多3位小数）、功率以 MW（最多3位小数）、能源价格为 EUR/MWh；收付款以 EUR 两位小数。公式默认按每15分钟值。
2. **BRP 偏差公式（P.O.14.4 §§12–13）。**
   ```text
   DESV_brp = MEDBC_brp − (POSFIN_brp + AJUDSV_brp)
   ```
   `MEDBC` 是 BRP 各发电/消费 UP 在中央母线（barras de central）的计量之和；`POSFIN` 是 PHFC 最终计划加 BRP 间计划变更；`AJUDSV` 是平衡能量（RR、tertiary、secondary）、实时技术约束能量和 aFRR BSP 的 `P48−PTR` 差额之和。正偏差=上调（多发/少用），负偏差=下调（少发/多用）。
3. **储能的双向计量。**MITECO P.O.10.5 表中 storage 边界同时记录 active saliente（流出/放电）、active entrante（流入/充电）及必要时 reactive。对于 P.O.10.5 适用接口且没有合格 15 分钟表计的情形，OS 可按该程序允许的实时有功遥测积分形成 QH 值；其他缺测按相应估计/插值规则处理，不能泛化为所有平衡服务 UP 均自动采用遥测积分。缺失的 generation/storage 类型3–5 计量在相应期间可按 P.O.10.5 §4.5 估计为0 kWh，但这不代表储能的 SOC 为0。
4. **不平衡调整的激活归属。**CNMC Art.21(6)把“日内连续市场最终计划之后分配给 BRP 的能量”定义为 `AJUDSV`；P.O.14.4 §13.3进一步列明 EB、ERTR 和 aFRR 的 `EPTR`。因此已计入 BRP 调整的激活能量不再作为未解释的偏差。

### 3.2 研究解释

储能的充电与放电在计量上是相反符号，但 BRP 最终位置按 generation、international exchange、consumption 合并为一条净位置（Art.21(5)）。这属于 BRP 结算层的净额化，不是电池内部 SOC 或循环能量的净额化；不能从结算公式推导 SOC/持续时长约束。

## 4. 15分钟结算周期、时区、发布与更正

### 4.1 规则事实

- ISP 是计算 BRP 偏差和偏差价格的时间单位，固定15分钟；不平衡区和不平衡价格区为西班牙半岛系统（Art.21(2)–(3)、Art.22）。CET/CEST 的时间口径定位在 2024-20995 版本 P.O.14.4 §2.3，以及 2025-5342 版本 P.O.3.1 §3；不能把该定位写成 2025-5342 P.O.14.4 §2.3。夏令时日的缺口/重复时段处理需按 OS 时间序列字段核对，本文不外推间隔数量。
- 每个 ISP，OS 对每个 BRP 在专用结算单元写入一笔偏差收付款；登记至少包括偏差能量、方向、价格和金额（Art.21(1),(12)、P.O.14.4 §12）。
- MITECO P.O.10.5：最佳能源值在具备数据后最长24小时内计算/提供；按月 M+1、M+2 等阶段发布，最终能源闭算通常在 M+11 月第3个工作日前完成；闭算后120天内可申请/提交计量更正，异常时 OS 可重新发布闭算。具体公开接口的 `revisionNumber`/API 字段仍需 ES-06 核验。
- BRP 可按 P.O.14.1 期限对偏差计算提出异议；计量更正先由读表责任方校验，再由 OS 更新结算输入。通知的停运/偏差（例如储能≥30 MW 或服务UP）仅供运行信息使用，不自动改变最终市场位置或 `AJUDSV`（Art.25）。

### 4.2 研究解释

2025 年数据应至少保留时区（CET/CEST）、15分钟 period start/end、版本/修订号、计量来源（表计或遥测积分）、发布/闭算日期。不能用小时均值替代QH偏差，也不能把 M+11 最终闭算误当成实时可得数据。

## 5. 不平衡价格（单价/双价、方向和净额）

### 5.1 规则事实

P.O.14.4 §14（BOE-A-2025-5342）逐 ISP 判断：

1. **单价条件。**该 ISP 没有 FRR 激活；或仅一个方向激活；或两个方向激活但少数方向能量 < 多数方向的 2%。此时所有 BRP 偏差共用一个价格。其他 TSO 需求激活的 FRR 不计入单/双价判断。
2. **单价形成。**上调激活时使用 `PBALSUB`（西班牙系统及其他 TSO BSP 的 RR+FRR 上调激活量加权平均价，剔除其他 TSO 需求，四舍五入至0.01）；下调激活时使用 `PBALBAJ`（下调激活量加权平均价）。若 RR/FRR 均无激活，使用“避免激活值”——该 ISP 西班牙 BSP 的 RR 上调最低报价与下调最高报价的算术平均。
3. **RR 方向边界。**RR 与 FRR 方向相反或 RR 双向激活时，偏差系统净方向决定使用 `PBALSUB`（系统下调）或 `PBALBAJ`（系统上调）；RR 每个编程期先取净激活量。
4. **双价条件和方向。**两个方向均有 FRR 激活且少数方向≥多数方向的2%时，偏差上调价 `PDESVS = PBALBAJ`，偏差下调价 `PDESVB = PBALSUB`。这不是“BSP上/下激活价”的同义词，而是 BRP 偏差方向对应的结算价。
5. **符号和付款。**价格可为正、零或负；正偏差×`PDESVS`形成 BRP 收款（负价时转为付款），负偏差×`PDESVB`形成 BRP 付款（负价时可转为收款）。P.O.14.4 §3.1 将负价导致的符号转换写入通用规则。

### 5.2 研究解释

西班牙规则是“默认单价、按FRR双向激活触发双价”；2%阈值与 QH 激活量有关。`PDESVS=PBALBAJ`、`PDESVB=PBALSUB` 的交叉方向意味着偏差成本反映系统避免/反向平衡能量，不应直接用同向激活价格替换。

## 6. 平衡能量激活与未交付/响应不足支付

### 6.1 规则事实

| 产品/事项 | 结算和支付义务（P.O.14.4，2025文本） | 定位 |
|---|---|---|
| RR | 上调激活按 RR 边际价 `DCRR = ERRS×PMRR` 收款；下调激活按 `OPRR = ERRB×PMRR` 付款。平台取整/系统信息异常时可使用 P.O.3.3/平衡条件的保障机制。 | §5.1–5.2（BOE HTML §§1757–1799） |
| mFRR/tertiary | 计划和直接 tertiary 激活按对应方向的边际价结算；不存在可用激活时，MER 规则使用最近月均价并按 1.15/0.85 系数。 | §6（HTML §§1806–1912） |
| aFRR/secondary | 每 QH，aFRR 上调 `DCSEC=ESECS×PMSECS` 收款，下调按 `ESECB×PMSECB` 付款；价格为 P.O.7.2 §9.2 的QH均价。 | §7.1–7.2（HTML §§1914–1938） |
| aFRR 跟踪不足 | OFF、响应不当、实时备用不足分别计算未履约能量和QH未履约价，形成 `−E×P` 付款义务；实时备用不足指每个4秒控制周期可用备用低于有效报价。 | §7.3（HTML §§1940–2000）；P.O.7.2 §9.3.1–9.3.3（BOE-A-2024-11535 §§2498–2581） |
| RR/tertiary 未交付 | 按同一 BRP/BSP 聚合净上调/下调分配核验。上调未交付支付 `EINCLEBALS×abs(PBAL)×0.2`；下调未交付支付 `EINCLEBALB×abs(PMD)`。 | §8.1–8.3（HTML §§2002–2058） |
| aFRR 容量/能量报价义务 | reserve 中标必须提交至少等量能量支持；未送备用支持报价 `−RSSRES×PMRSS×KRES`（KRES=0.15），未送能量报价 `−RSS×PMRSS×KI`（KI=1.5），上/下分开。 | §17.3.1–17.3.2（HTML §§2391–2453）；Art.10(2)(c)、Art.10(4) |
| 信息系统异常 | 平台价格异常时，OS 可将同产品、同方向、最近一个月相同编程期的激活边际价算术平均作为保障价，并向 CNMC 报告；差额由西班牙拥塞收入承担。 | §10（HTML §§2090–2094） |

### 6.2 资格暂停和 BRP 支付义务（规则事实）

- OS 持续检查 BSP 的 FAT、交付期和“分配功率—实际功率”偏差，至少每五年进行一次资格再评估；未满足服务要求、服务质量不当、未报告影响能力的变化或违反条件时，可在通知并给予最长一个月整改/说明不可抗力后暂停（S-CNMC-2024-MP Art.14）。
- BRP 未履行付款/保证金义务可被临时暂停；暂停不免除已产生的付款义务（Art.24；P.O.14.2 §3.4）。
- 未交付支付（§7.3、§8、§17.3）是 BSP/BRP 与 TSO 的服务结算项目，不能直接当作“偏差价格罚款”；同一事件可能同时影响 BSP 付款和 BRP `DESV`，但两者公式和账户不同。

### 6.3 研究解释

“未交付”分至少三层：aFRR实时跟踪/备用不足、RR/mFRR净能量未交付、aFRR reserve/energy 报价义务未履行。每层有独立能量基数和价格系数；ES-04 未确认的 SOC/持续时长只能解释为可能导致上述未交付，不能写成额外规则约束。

## 7. 独立储能接口边界

### 7.1 已确认

- 储能可申请 BRP 或委托 BRP；其连接的所有边界点组成结算连接，进入/流出分别测量并映射 UP。
- 储能作为 BSP 的一般资格、实时控制中心、产品测试入口已在 ES-02/ES-04 规则中确认；激活量按方向进入 P.O.14.4，计量缺失按 P.O.10.5 处理。
- 结算公式未出现 SOC、可用能量、持续时长或补能字段；P.O.10.5 的 `active entrante/saliente` 仅是能量计量方向，不等于 SOC。

### 7.2 与 ES-04 保持未决（不得建模）

`SOC/持续时长/补能或恢复`、`aFRR/mFRR/RR 可用率和资格阈值`、`FCR/primary 储能资格`、`SRAD 独立储能资格`、`2026 TERRE 停止后的 RR 替代机制`仍是 ES-04/ES-01-Q06、Q10、Q11、Q16、ES04-U01–U08 的 open/open-critical 项。本文不将其写成结算事实。

## 8. 结算数据目录（官方入口）

| 数据集 | 提供方/入口 | 关键字段（需保留） | 分辨率/时区 | 发布/修订 |
|---|---|---|---|---|
| 不平衡价格 | REE/eSIOS “Precio de los desvíos en tiempo real” (`S-eSIOS-PRICES-2026`) | ISP起止、`PDESV`/`PDESVS`/`PDESVB`、单/双价标志、EUR/MWh、版本 | QH；CET/CEST（以 2024-20995 P.O.14.4 §2.3、2025-5342 P.O.3.1 §3 为准） | 入口已确认，API字段、延迟和历史覆盖待 ES-06 |
| BRP 偏差/结算 | REE eSIOS/OS 结算与 P.O.14.1 账户 | BRP、UP、MEDBC、POSFIN/PHFC、AJUDSV（EB/ERTR/EPTR）、DESV、方向、价格、EUR | QH；CET/CEST | 最终闭算在 M+11 月第3个工作日前；更正期120天（P.O.10.5） |
| RR/mFRR/aFRR 激活价格和量 | REE “Energía de balance” (`S-REE-DATA-BAL-2026`) | 产品、方向、激活 MWh、边际价 EUR/MWh、BSP/UP（如公开）、跨TSO标记 | QH（RR/mFRR/aFRR）；时区字段待验证 | 官方入口确认；字段、修订和延迟待 ES-06 |
| 15分钟计量/最佳能源 | MITECO P.O.10.5、REE/读表责任方 | active saliente/entrante/reactive、来源（表计/遥测积分）、period、计量版本、估计/实测标志 | QH；CET/CEST | 最佳值通常≤24h；M+1…M+11闭算和120天更正 |

## 9. 研究解释与建模假设分栏

### 研究解释

- 结算链条为“计划（PHFC/IT）→实时激活（EB/ERTR/EPTR）→实际计量（MEDBC）→BRP偏差（DESV）→单/双偏差价格”。BSP 能量支付和 BRP 偏差支付必须分开建账。
- 储能充放电双向计量与 BRP 的净位置并存：前者保留方向，后者在 BRP 层按符号合并。没有证据表明西班牙结算按电池循环或 SOC 进行内部净额化。

### 建模假设（本任务不采用）

无。任何缺失的 SOC、持续时长、补能、可用率、数据延迟或版本切片，只能在后续模型任务中以显式假设登记，不能从本文规则公式推导。

## 10. 关键 claim 登记

```yaml
claims:
  - claim_id: ES05-BRP-001
    rule_fact: 储能持有人可自任BRP或委托BRP；BRP对偏差承担财务责任。
    source_id: S-CNMC-2024-MP
    institution: CNMC / BOE
    title: Resolución 25-Apr-2024, Condiciones aplicables a los servicios de balance (BOE-A-2024-11535)
    source_date: 2024-06-06 publication; conditions effective 2024-07-06
    url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf
    location: Arts.16-18, BOE HTML §§757-785
    accessed_at: 2026-08-18
    applicability_2025: confirmed
    interpretation: BSP payment and BRP imbalance are separate accounts.
    confidence: confirmed
  - claim_id: ES05-BRP-002
    rule_fact: 对属于 aFRR BSP 的储能，2024-20995 P.O.14.4 §3.2 要求 BRP 委托给 BSP 持有人，不得按一般路径另选 BRP；后续版本适用日需切片核对。
    source_id: S-CNMC-2024-ISP15
    institution: CNMC / BOE
    title: Resolución 3-Oct-2024 adapting P.O.14.4 to ISP15 (BOE-A-2024-20995)
    source_date: 2024-10-14 publication; effective 2024-12-01, subject to later P.O.14.4 amendments
    url: https://www.boe.es/eli/es/res/2024/10/03/(1)
    location: P.O.14.4 §3.2
    accessed_at: 2026-08-18
    applicability_2025: confirmed for the 2024-20995 version; day-level replacement remains ES05-Q01
    interpretation: The aFRR storage BRP exception narrows the general storage BRP choice.
    confidence: confirmed-version-specific
  - claim_id: ES05-MEAS-001
    rule_fact: 储能连接的进入/流出分别计量并分配UP；storage边界记录active saliente/entrante。
    source_id: S-CNMC-2024-MP; S-MITECO-2025-ISP
    institution: CNMC / BOE; Secretaría de Estado de Energía / MITECO
    title: Resolución 25-Apr-2024, Condiciones aplicables a los servicios de balance (BOE-A-2024-11535); Resolución 28-Mar-2025 implementing P.O.10.x (BOE-A-2025-6693)
    source_date: 2024-06-06 publication; conditions effective 2024-07-06; 2025-04-02 publication; measurement effective 2025-05-01
    url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf ; https://www.boe.es/eli/es/res/2025/03/28/(2)
    location: Art.16(1)-(2), BOE §§757-760; P.O.10.5 §4.9 and activity table (HTML §§1351-1358, 1952-1961)
    accessed_at: 2026-08-18
    applicability_2025: confirmed (measurement procedure from 2025-05-01)
    interpretation: Directional metering is not an SOC rule.
    confidence: confirmed
  - claim_id: ES05-METER-002
    rule_fact: P.O.10.5 permits real-time active-power telemetering integration only where its applicable interface and no qualified 15-minute meter conditions are met; other missing data follows the procedure's estimate/interpolation rules.
    source_id: S-MITECO-2025-ISP
    institution: Secretaría de Estado de Energía / MITECO
    title: Resolución 28-Mar-2025 implementing P.O.10.x (BOE-A-2025-6693)
    source_date: 2025-04-02 publication; effective 2025-05-01
    url: https://www.boe.es/eli/es/res/2025/03/28/(2)
    location: P.O.10.5 §§4.5, 4.9 and storage activity table
    accessed_at: 2026-08-18
    applicability_2025: confirmed from 2025-05-01, subject to the interface-specific conditions
    interpretation: This does not mean every balancing UP automatically uses telemetry integration.
    confidence: confirmed-with-scope
  - claim_id: ES05-ISP-001
    rule_fact: 西班牙ISP为15分钟；ISP15 P.O.14.1/14.4 effective 2024-12-01; measurement P.O.10.x effective 2025-05-01。
    source_id: S-CNMC-2024-ISP15; S-MITECO-2025-ISP
    institution: CNMC / BOE; Secretaría de Estado de Energía / MITECO
    title: Resolución 3-Oct-2024 adapting P.O.14.1/14.4 to ISP15 (BOE-A-2024-20995); Resolución 28-Mar-2025 implementing P.O.10.x (BOE-A-2025-6693)
    source_date: 2024-10-14 publication/effective 2024-12-01; 2025-04-02/effective 2025-05-01
    url: https://www.boe.es/eli/es/res/2024/10/03/(1) ; https://www.boe.es/eli/es/res/2025/03/28/(2)
    location: BOE-A-2024-20995 Resuelve/§§229-234 and P.O.14.4 §2.3 (CET/CEST); BOE-A-2025-5342 P.O.3.1 §3 (CET/CEST) and BOE-A-2025-6693 Resuelve Segundo/§§63-70, 105-108
    accessed_at: 2026-08-18
    applicability_2025: confirmed
    interpretation: ISP15 and meter rollout have different effective dates.
    confidence: confirmed
  - claim_id: ES05-SIGN-001
    rule_fact: P.O.14.4 defines generation/import as positive, consumption/export as negative, with up/down regulation signs and MWh/MW/EUR units at quarter-hour granularity.
    source_id: S-CNMC-2025-QH
    institution: CNMC / BOE
    title: Resolución 6-Mar-2025 adapting P.O.3.1/P.O.14.4 to quarter-hourly trading (BOE-A-2025-5342)
    source_date: 2025-03-17 publication; effective at the OMIE MTU15 production date
    url: https://www.boe.es/eli/es/res/2025/03/06/(12)
    location: P.O.14.4 §§3.1–3.2
    accessed_at: 2026-08-18
    applicability_2025: confirmed with version-slice caveat
    interpretation: Sign conventions are settlement signs, not battery SOC signs.
    confidence: confirmed
  - claim_id: ES05-TIME-001
    rule_fact: Each ISP has a BRP imbalance settlement entry containing imbalance energy, direction, price and amount; CET/CEST is the applicable time basis.
    source_id: S-CNMC-2024-ISP15; S-CNMC-2025-QH
    institution: CNMC / BOE
    title: Resolución 3-Oct-2024 adapting P.O.14.4 (BOE-A-2024-20995); Resolución 6-Mar-2025 adapting P.O.3.1/P.O.14.4 (BOE-A-2025-5342)
    source_date: 2024-10-14/2024-12-01; 2025-03-17/effective at OMIE MTU15 production date
    url: https://www.boe.es/eli/es/res/2024/10/03/(1) ; https://www.boe.es/eli/es/res/2025/03/06/(12)
    location: 2024-20995 P.O.14.4 §2.3; 2025-5342 P.O.3.1 §3 and P.O.14.4 §12
    accessed_at: 2026-08-18
    applicability_2025: confirmed with version-slice caveat
    interpretation: Store local time and period boundaries separately from API publication timestamps.
    confidence: confirmed
  - claim_id: ES05-DESV-001
    rule_fact: DESV=MEDBC−(POSFIN+AJUDSV); positive=up/greater generation or lower consumption; negative=down。
    source_id: S-CNMC-2025-QH
    institution: CNMC / BOE
    title: Resolución 6-Mar-2025 adapting P.O.3.1/P.O.14.4 to quarter-hourly trading (BOE-A-2025-5342)
    source_date: 2025-03-17 publication; effective at OMIE MTU15 production date
    url: https://www.boe.es/eli/es/res/2025/03/06/(12)
    location: P.O.14.4 §§12-13, BOE HTML §§2154-2212
    accessed_at: 2026-08-18
    applicability_2025: confirmed with version-slice caveat
    interpretation: Activation included in AJUDSV must not be counted again as unexplained imbalance.
    confidence: confirmed
  - claim_id: ES05-PRICE-001
    rule_fact: 默认单价；FRR双向激活且少数方向≥多数方向2%时双价；单价/双价公式及avoided activation值如§14。
    source_id: S-CNMC-2025-QH
    institution: CNMC / BOE
    title: Resolución 6-Mar-2025 adapting P.O.3.1/P.O.14.4 to quarter-hourly trading (BOE-A-2025-5342)
    source_date: 2025-03-17 publication; effective at OMIE MTU15 production date
    url: https://www.boe.es/eli/es/res/2025/03/06/(12)
    location: P.O.14.4 §§14.1-14.4, BOE HTML §§2214-2286
    accessed_at: 2026-08-18
    applicability_2025: confirmed with version-slice caveat
    interpretation: PDESVS uses PBALBAJ in dual mode; PDESVB uses PBALSUB.
    confidence: confirmed
  - claim_id: ES05-NONDEL-001
    rule_fact: aFRR OFF/response inadequacy/insufficient reserve and RR/tertiary non-delivery create separate payment obligations; formulas and coefficients are in §§7.3, 8 and 17.3.
    source_id: S-CNMC-2025-QH; S-CNMC-2024-MP
    institution: CNMC / BOE
    title: Resolución 6-Mar-2025 adapting P.O.14.4 (BOE-A-2025-5342); Resolución 25-Apr-2024, Condiciones de balance (BOE-A-2024-11535)
    source_date: 2025-03-17 publication; effective at OMIE MTU15 production date; 2024-06-06 publication; conditions effective 2024-07-06
    url: https://www.boe.es/eli/es/res/2025/03/06/(12) ; https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf
    location: P.O.14.4 §§7.3, 8, 17.3 (HTML §§1940-2000, 2002-2058, 2391-2453); Art.14 (BOE §§736-749)
    accessed_at: 2026-08-18
    applicability_2025: confirmed with product/version caveat
    interpretation: Non-delivery payments are not the BRP imbalance price.
    confidence: confirmed
  - claim_id: ES05-QUAL-001
    rule_fact: OS may reassess BSP qualification at least every five years and may suspend after notice and a remediation/force-majeure period; BRP payment or guarantee failures may also trigger temporary suspension without cancelling accrued obligations.
    source_id: S-CNMC-2024-MP
    institution: CNMC / BOE
    title: Resolución 25-Apr-2024, Condiciones aplicables a los servicios de balance (BOE-A-2024-11535)
    source_date: 2024-06-06 publication; conditions effective 2024-07-06
    url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf
    location: Art.14, Art.24 and P.O.14.2 §3.4; BOE §§736–749 and related payment-suspension provisions
    accessed_at: 2026-08-18
    applicability_2025: confirmed, subject to later P.O.14.4 amendments for payment formulas
    interpretation: Qualification suspension and BRP payment suspension are separate processes.
    confidence: confirmed
  - claim_id: ES05-PLAN-001
    rule_fact: BRP final programs and permitted plan changes are governed by the P.O.3.1 process; post-cutoff internal balancing changes require the specified conditions and OS notification.
    source_id: S-CNMC-2024-MP; S-CNMC-2025-QH; S-CNMC-2025-VOLTAGE-13076
    institution: CNMC / BOE
    title: Resolución 25-Apr-2024, Condiciones de balance (BOE-A-2024-11535); Resolución 6-Mar-2025 and Resolución 12-Jun-2025 amending P.O.3.1/P.O.14.4 (BOE-A-2025-5342; BOE-A-2025-13076)
    source_date: 2024-06-06 publication; conditions effective 2024-07-06; 2025-03-17 publication; effective at OMIE MTU15 production date; 2025-06-26 publication; amended procedures effective from publication except deferred elements under Resuelve Segundo
    url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf ; https://www.boe.es/eli/es/res/2025/03/06/(12) ; https://www.boe.es/eli/es/res/2025/06/12/(1)
    location: Art.20 (BOE §§789–796); P.O.3.1; 2025-13076 Resuelve and P.O.3.1/P.O.14.4 amendments
    accessed_at: 2026-08-18
    applicability_2025: confirmed with version-slice caveat
    interpretation: This records the balancing-program interface and does not describe OMIE spot-market rules.
    confidence: confirmed-interface
  - claim_id: ES05-CORR-001
    rule_fact: BRP may challenge imbalance calculation; measurement corrections and final closure follow P.O.10.5 (≤24h best value, M+11 final closure, 120-day post-close correction window).
    source_id: S-CNMC-2024-MP; S-MITECO-2025-ISP
    institution: CNMC / BOE; Secretaría de Estado de Energía / MITECO
    title: Resolución 25-Apr-2024, Condiciones de balance (BOE-A-2024-11535); Resolución 28-Mar-2025 implementing P.O.10.x (BOE-A-2025-6693)
    source_date: 2024-06-06 publication; conditions effective 2024-07-06; 2025-04-02 publication; measurement effective 2025-05-01
    url: https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf ; https://www.boe.es/eli/es/res/2025/03/28/(2)
    location: Art.21(10), BOE §§797-827; P.O.10.5 §§4.6, 8.11-8.14, HTML §§1933-1950, 2420-2457
    accessed_at: 2026-08-18
    applicability_2025: confirmed
    interpretation: Real-time data and final settlement data must be stored separately.
    confidence: confirmed
```

## 11. 未解决问题（与 ES-04 对齐）

| ID | 问题 | 影响 | 状态 |
|---|---|---|---|
| ES05-Q01 | P.O.14.4（2024-20995、2025-5342、2025-13076）在 2025 每个日期的精确替代日及 OMIE MTU15 触发边界？ | 结算回测版本切片 | `open` |
| ES05-Q02 | REE/eSIOS 不平衡价格、MEDBC、AJUDSV、激活量公开字段的 API 名、时区、发布延迟、revisionNumber 和历史覆盖？ | 数据目录/可复现性 | `open-critical`（ES-06） |
| ES05-Q03 | 计量异常估计与结算更正后，BSP未交付和BRP偏差是否触发联动重算、由谁发起？ | 更正流程 | `open` |
| ES05-Q04 | 储能 SOC、持续时长、补能、可用率是否作为产品资格/未交付豁免条件？ | 履约风险和建模约束 | `open-critical`（ES04-U04/U05） |
| ES05-Q05 | 独立储能 FCR/SRAD 资格和 2026 RR 替代机制是否存在专门结算条款？ | 产品范围和2026延续性 | `open-critical`（ES04-U01/U06/U08） |
| ES05-Q06 | aFRR 储能 BRP 特殊委托规则在 2025 各 P.O.14.4 版本中的逐日适用边界？ | aFRR BSP 储能的 BRP 委托特例已在 2024-20995 P.O.14.4 §3.2 定位；后续版本替代日仍需切片 | `open`（版本核对） |

## 12. 官方来源登记（本模块使用）

```yaml
source_id: S-CNMC-2024-ISP15
institution: CNMC
title: Resolución de 3 de octubre de 2024, adaptación de P.O.14.1/14.4 al ISP cuarto-horario (BOE-A-2024-20995)
document_type: CNMC resolution / P.O.14.1 and P.O.14.4
publication_date: 2024-10-14
effective_from: 2024-12-01
effective_to: replaced by 2025-5342 at MTU15 production date
url: https://www.boe.es/eli/es/res/2024/10/03/(1)
accessed_at: 2026-08-18
language: Spanish
relevant_pages: BOE HTML §§95-108, 145-152, 226-234; P.O.14.4 §§12-15
relevant_sections: ISP15 transition; CET/CEST; QH imbalance formula and price references
notes: Governing ISP15 version at start of 2025; exact replacement date must be sliced by OMIE MTU15 production notice.
historical_2025: yes
version_relation: replaced/modified by S-CNMC-2025-QH and later 2025-13076
evidence_status: confirmed
```

Existing source IDs used without duplication: `S-CNMC-2024-MP`, `S-CNMC-2025-QH`, `S-MITECO-2025-ISP`, `S-REE-DATA-BAL-2026`, `S-eSIOS-PRICES-2026`, `S-EBGL-2017`.

## 13. 交付检查

- [x] BRP/BSP/储能责任、计划/实际/激活/偏差分层。
- [x] ISP15、CET/CEST、计量方向、单位和版本切片记录。
- [x] 单价/双价、2%阈值、PBALSUB/PBALBAJ、avoided activation 和方向公式有 P.O. 定位。
- [x] 未交付、响应不足、报价义务、资格暂停和支付义务与 BRP 偏差价格分开。
- [x] 储能 SOC、持续时长、补能、可用率、FCR/SRAD、2026 RR 替代仍标为未决。
- [x] 未修改 model/、src/、tests/、outputs/、data/raw/；未进入现货策略或MILP。
