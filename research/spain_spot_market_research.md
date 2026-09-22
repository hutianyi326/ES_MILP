# 西班牙独立储能现货与自动恢复备用（aFRR）市场研究

> 研究对象：西班牙半岛竞价区的独立非水电化学储能。  
> 历史研究期：2025-01-01—2025-12-31。  
> 规则基准日：2026-08-11。  
> 本报告把日前、日内、aFRR（Automatic Frequency Restoration Reserve；西班牙制度文件对应的 Sistema de Regulación Secundaria，自动恢复备用）和不平衡结算放在一条运行链中解释；不提出报价策略、收益、MILP、代码、回测或预测。

## 1. 先给结论：储能实际面对的是一条链

最容易误读西班牙市场的方式，是把“现货成交”“备用容量”“备用能量”和“电池功率”当成同一个数字。它们其实处在不同层次：

1. OMIE（Operador del Mercado Ibérico de Energía，伊比利亚电力市场运营方）先运行日前和日内经济市场；REE（Red Eléctrica de España，西班牙电网公司）作为 OS（Operador del Sistema，系统运营方）再把成交与其他调整拼成最终计划。
2. 最终计划是储能的基准位置，叫 `PTR`（Programa en Tiempo Real / Real-Time Program，实时计划）时，指的是 aFRR 供应商聚合后的即时功率基准；`PTR` 不是实际功率，也不是电池 `SOC`（State of Charge，荷电状态）。
3. aFRR 容量市场按每个 15 分钟时段、`Up`/`Down`（aFRR upward/downward，向上/向下）两个方向分别采购，价格单位是 €/MW；aFRR 能量按激活的 MW·时间结算，价格单位是 €/MWh。两者不是同一笔报价。
4. 激活后，OS 的 SRS（Sistema de Regulación Secundaria / Secondary Regulation System，二次调频系统）通过 AGC（Automatic Generation Control / control automático de generación，自动发电控制）用 `Pout`、`PGC`、上下限和剩余 offer 重新计算当前可用备用，并核验遥测、跟踪和交付。
5. 对独立储能，系统层面允许储能持有人成为 BSP（Balancing Service Provider / Proveedor de Servicios de Balance，平衡服务提供者），但项目级 UP（Unidad de Programación，计划单元）/UF（Unidad Física，物理单元）、控制中心、双向计量、产品资格以及 SOC/持续时长/补能/恢复仍不能由公开规则自动补齐。

图中的计划代码也先给出中文功能释义：`PDBC`（日前市场出清基础计划）、`PDBF`（日前基础运行计划）、`PDVP`（临时可行计划）、`PDVD`（最终可行计划）、`PHF`（最终时段计划）、`PHFC`（连续日内最终时段计划）。这些是 OMIE/REE 官方计划标识；功能释义不替代对应版本的西语 P.O. 和文件格式定义。

图中其余符号的首次含义是：`BRP`（Balance Responsible Party / Sujeto Responsable del Balance，平衡责任主体）；`PaFRRset`（aFRR setpoint / consigna aFRR，aFRR 设定值）；`Pout`（provider output power，供应商输出功率）；`PGC`（potencia generada bajo control，受控发电功率）；`POSFIN`（posición final，最终位置）；`AJUDSV`（ajustes de servicios de balance，平衡服务调整项）。

```text
OMIE 日前/日内成交
        ↓
PDBC/PDBF → PDVP/PDVD → PHF/PHFC（现货与系统最终计划）
        ↓                         ↘
现货买/卖位置、BRP基准                 BSP 的aFRR容量/能量接口
                                          ↓
                             SRS/AGC → PaFRRset 激活指令
                                          ↓
                             Pout、PGC、限值、遥测、履约核验
                                          ↓
                     BSP结算 + POSFIN/AJUDSV → BRP不平衡结算
```

**F｜规则事实**：P.O.7.2（Procedimiento de Operación 7.2，运行规程7.2）明确二次调频服务同时包括 reserve market 和 energy market；容量按上下方向分别采购，aFRR 能量自动激活，SRS 按供应商聚合并以实时计划和实际功率核验。[S-CNMC-2024-MP][S-CNMC-2024-11535-PO]

**I｜研究解释**：同一储能装置可能只有一个逆变器和一个并网点，但它的市场账户、计划、备用和结算记录可以分属不同系统层。账户分开不等于物理功率和电池能量约束分开。

**A｜建模假设**：本报告不新增效率、SOC、持续时长、补能、恢复、可用率或费用假设。

**U｜待确认**：项目级资格、UP/BSP/BRP crosswalk、实时限值生成方式和所有储能产品的能量要求仍为 `open-critical`；不因下文的规则公式而关闭这些问题。

## 2. 先把缩写和符号分清

| 写法 | 本报告含义 | 最常见的混淆 |
|---|---|---|
| `UP` | `Unidad de Programación`，计划单元 | 不是英文方向 `Up` |
| `Up` / `Down` | aFRR 上调/下调方向；法规西语常写 `a subir`/`a bajar` | `Up` 不等于 `UP` |
| `UO` | `Unidad de Oferta`，OMIE 报价单元 | 不等于 REE 的计划单元 |
| `UF` | `Unidad Física`，物理单元 | 不等于市场成交记录 |
| `PTR` | 供应商按历史市场/系统计划形成的实时基准功率 | 不等于 `PGC` 或 SOC |
| `PGC` | provider-level 的 AGC 控制发电功率，采用发电符号 | 可为负，负值表示净消费方向的发电符号 |
| `Pout` | 用于 aFRR 交付/响应核验的总交付功率 | 不是所有电表能量的最终结算值 |
| capacity | 备用容量，€/MW | 不是激活能量的 €/MWh |
| energy | 被激活并认可的平衡能量，€/MWh | 不是已中标容量本身 |

**同屏警示**：`UP`≠`Up`；`PTR`≠`PGC`；capacity（€/MW）≠ energy（€/MWh）。储能“充电/放电”到 Up/Down 的映射只是研究解释，不能代替项目的 UP 类型、消费模式资格、功率限值和预认证。

## 3. 现货层：日前、日内和最终计划

### 3.1 市场主体和平台

**F｜规则事实**

- OMIE 负责日前、IDA（日内拍卖，Intraday Auctions）和 SIDC（Single Intraday Coupling，连续日内耦合）经济市场；SDAC（Single Day-Ahead Coupling，单一日前耦合）和 SIDC 的跨区订单/容量由欧洲 NEMO/TSO 机制衔接。[S-SP-BOE-2025-RULES][S-SP-OMIE-NEMO-2026]
- REE 接收计划、进行系统约束和实时系统运行；市场参与者通过 `UP` 参加生产计划，可直接或通过代表参加。[S-SP-PO31-2024-STORAGE][S-SP-REE-ROLE-2026]
- 规则把储能设施持有人列为市场参与者类别，但“可以成为市场主体”不等于项目已经完成 UP/UF、并网、BRP、双向计量或 aFRR 预认证。[S-CNMC-2024-MP][S-SP-OMIE-AGENT-2026]

### 3.2 计划链：成交不是物理执行

```text
日前成交 → PDBC
          + 双边合同/系统信息 → PDBF
          + 技术约束处理      → PDVP / PDVD
          + IDA成交            → PIBCI / PIBCA → PHF
          + SIDC连续成交       → PIBCIC / PIBCAC → PHFC
          + 平衡/实时调整       → PTR、激活、计量、结算
```

**F**：OMIE 市场规则和 P.O.3.1/3.1 修订形成上述计划交接；UO 与 UP 不一一等同，必要时需要按 UP/UF 分解。日内成交仍要进入 REE 最终计划，不能只保留在 OMIE 的成交表里。[S-SP-BOE-2025-RULES][S-SP-PO31-2024-STORAGE]

**I**：对储能，日前/日内成交描述“想在什么时段买或卖”，最终计划描述“系统接受并用于运行的基准位置”。aFRR 的 PTR 又把这条基准位置细化成实时 ramped power；因此不能用日前成交量替代 PTR、实际计量或 SOC。

### 3.3 2025 年现货粒度边界

| 期间 | 规则/运行事实 | 研究处理 |
|---|---|---|
| 2025-01-01—03-17 | 使用上一版市场规则和小时型历史片段 | 不把全年回填成季度小时 |
| 2025-03-18 起 | 日内 QH（Quarter-Hour，15 分钟时段）运行切换，首个交付日 2025-03-19 | 日内成交、计划、数据保留版本标签 |
| 2025-03-18—09-30 | 修订规则已开始适用，但日前 MTU 仍按小时运行 | 不把日前 15 分钟回填到该期间 |
| 2025-10-01 起 | 日前 MTU15 上线，正常日 96 个季度小时 | 夏令/冬令切换日仍按实际时段核对 |

来源：`S-SP-BOE-2024-RULES`、`S-SP-BOE-2025-RULES`、`S-SP-OMIE-QH-ID-2025`、`S-SP-OMIE-MTU15-DA-2025`。

## 4. 从现货到 aFRR：两种价格、两种承诺

### 4.1 运行链中的角色

**F｜规则事实**

1. 现货交易和系统调整形成前置计划；aFRR 服务提供者由一个或多个已 habilitada（获 OS 授权/资格）的 UP 组成。[S-CNMC-2024-MP]
2. aFRR reserve 在 D-1 每日采购、按供应时段的每个 QH 处理，Up 和 Down 独立采购；容量中标后，供应商至少要提交相应数量的 aFRR 能量支持报价。[S-CNMC-2024-MP][S-CNMC-2024-11535-PO]
3. aFRR energy 自动激活；SRS 结合 ACE（Area Control Error / error de control de área，区域控制误差）、PICASSO（Platform for the International Coordination of Automated Frequency Restoration and Stable System Operation，aFRR 国际协调平台）/IGCC（International Grid Control Cooperation，国际电网控制合作）修正信号和能量报价排序，向供应商发送 `PaFRRset`。2025 年 6 月后 PICASSO 是 aFRR 跨区能量的主要平台路径；平台故障时可按 P.O.7.2 使用本地后备。[S-CNMC-2024-11535-PO][S-REE-PLATFORMS-2026]

**I｜小例子**：同一 QH，储能可能有 50 MW 现货放电基准；如果它另有 20 MW Up 容量中标，这 20 MW 是“在基准之上可被自动调用的承诺”，不是把现货 50 MW 改写成 70 MW，也不是自动保证电池有足够 MWh。

### 4.2 容量报价：每方向、每 QH 最多 25 段

**F｜规则事实（P.O.7.2 Annex I §§1.1–1.2）**

- reserve product 的有效期为 15 分钟，方向为 Up 或 Down，最小数量和粒度为 1 MW；价格精度为 0.01 €/MW，除技术字段外没有统一数值价格上限。[S-CNMC-2024-11535-PO]
- 报价由 `volume-price blocks`（数量—价格段）组成，并标明方向和 divisible/indivisible（可分/不可分）。每个方向、每个 QH 最多 25 段，其中最多 1 段可以是不可分块。[S-CNMC-2024-11535-PO]
- Up 与 Down 是两个独立市场方向，规则不要求容量报价对称；“同一 QH 最多 25 段”是报价曲线的表达能力，不是 25 个不同的结算价格。[S-CNMC-2024-MP][S-CNMC-2024-11535-PO]
- 容量由 OS 按边际机制分配；每个方向、每个 QH 的容量结算价格是为覆盖该方向系统需求而被全部或部分接受的最后一档 reserve offer 价格。[S-CNMC-2024-11535-PO]

因此，**容量 25 段**只回答“怎样表达容量供给曲线”；它不回答“能否被激活多少次”，也不等同于**能量报价 25 段**。

### 4.3 能量报价：也是 25 段，但不是容量 25 段

**F｜规则事实（P.O.7.2 Annex I §§2.1–2.2）**：aFRR 能量报价为自动激活，FAT（Full Activation Time，完全激活时间）5 分钟，交付/有效期 15 分钟，最小报价 1 MW，价格精度 0.01 €/MWh，每个方向最多 25 段。[S-CNMC-2024-11535-PO]

**I｜为什么要分开**：容量报价产生 €/MW 的可用备用承诺；能量报价产生 €/MWh 的激活曲线。一个 QH 可能有容量中标却没有能量激活，也可能有有效能量 offer 但某些段没有被调用。不能把两个市场各自的“25 段”相加或合并成一张 50 段曲线。

## 5. PTR、Pout 和负消费遥测：激活后系统到底看什么

### 5.1 `PTR` 是基准计划，不是实时实测

**F｜规则事实（P.O.7.2 Annex II §§1–5）**：PTR 是供应商在实时的即时有功计划，按 provider 聚合此前市场和系统计划并进行功率 profile/ramp。其来源包括日前/日内计划、BRP 间日内连续交易后的变更、日前和实时技术约束 redespacho、RR（Replacement Reserves，替代恢复备用）/tertiary 计划、已申报不可用和偏差等。OS 与 provider 均可计算 PTR，OS 选择实际用于跟踪的信号。[S-CNMC-2024-11535-PO]

**F**：在供应商有有效 aFRR 能量 offer 且参与服务的 QH，PTR 跟踪是履约的一部分；aFRR 交付功率是实际功率与 PTR 的差异，方向由 `PaFRRset` 的正负符号决定。[S-CNMC-2024-11535-PO]

### 5.2 `Pout` 的负消费限定

**F｜规则事实（P.O.7.2 Annex III §8.1）**：aFRR 交付/响应核验中的 `Pout` 使用 provider 所属物理单元的有功遥测，并按发电符号计量（注入为正）。该条明确规定：**储能处于消费模式时的负遥测，不纳入计算，除非它属于已在消费模式取得相应服务资格的 UP**。同时，OS 可在 provider 发送的聚合值和 OS 计算值之间选择，并在 provider level 计算、在 UF level 保持可观测性。[S-CNMC-2024-11535-PO]

这句话的边界很重要：

- 它是 `Pout` 的 aFRR 响应计算规则，不是“所有负电量都不结算”；
- 它不证明纯独立 BESS 已经获得消费模式 UP 或 aFRR 资格；
- 它不把负消费遥测自动变成 SOC、可用 MWh 或 `LIMINF`。

**I｜方向解释（不是统一规则公式）**：在现货放电基准下，Up 往往表现为增加注入，Down 往往表现为减少注入或转向取电；在现货充电基准下，Up 可能表现为减少取电或转向送出，Down 可能表现为增加取电。实际映射必须由 UP 活动类型、服务资格、控制配置、功率上下限和 OS 验证共同决定。

## 6. 实时 reserve 公式：三组上下限如何串起来

### 6.1 先分变量，再看公式

| 变量 | 规则含义 | 谁提供/计算 |
|---|---|---|
| `PGC_b(t)` | provider `b` 在 AGC 控制下的聚合发电功率（potencia generada bajo control，受控发电功率），发电符号 | provider/OS 实时信号 |
| `LIMSUP_b(t)` / `LIMINF_b(t)` | provider 发送给 OS 的上、下限（límite superior/inferior，上/下限） | BSP/provider |
| `CLIMSUP_b(t)` / `CLIMINF_b(t)` | SRS 根据受控物理单元计算的上、下限（calculated upper/lower limit，计算上/下限） | OS/SRS |
| `PGCSUP_b(t)` / `PGCINF_b(t)` | 将 provider 限值和 SRS 限值选取、再做一致性修正后的最终限值（controlled-power upper/lower bound，受控功率最终上/下界） | SRS，供 `RESA` 使用 |
| `RESAUP_b(t)` / `RESADW_b(t)` | 当前实时可用的 Up/Down reserve（reserva disponible a subir/a bajar，可用上/下备用） | 由最终限值与 `PGC` 计算 |

### 6.2 规则计算顺序

**F｜规则事实（P.O.7.2 Annex III §9.1）**：SRS 先在 provider 限值与系统计算限值之间选取更严格者，再确保 `PGC` 位于最终上下限之间。可用备用的核心公式为：

```text
RESAUP_b(t) = PGCSUP_b(t) − PGC_b(t)
RESADW_b(t) = PGC_b(t) − PGCINF_b(t)
```

这里 `RESAUP` 是从当前 `PGC` 向上走到最终上限的距离；`RESADW` 是从当前 `PGC` 向下走到最终下限的距离。**`LIMINF` 不是 SOC 公式，`PGCINF` 也不是由一个统一 SOC 百分比直接生成的值。**[S-CNMC-2024-11535-PO]

P.O.7.2 的候选选择逻辑可压缩写成：

```text
若 CLIMSUP > LIMSUP，则候选 PGCSUP' = LIMSUP，否则 PGCSUP' = CLIMSUP
若 CLIMINF < LIMINF，则候选 PGCINF' = LIMINF，否则 PGCINF' = CLIMINF

若 PGC > PGCSUP'，把 PGCSUP 修正为 PGC；
若 PGCINF' > PGC，把 PGCINF 修正为 PGC；
否则使用候选上下限。
```

公式旁的实务含义是：provider 可以发送一个保守边界，SRS 也可以根据 AGC/系统计算得出更严格边界；最终用于 `RESA` 的是经过系统选取和一致性处理的 `PGCSUP/PGCINF`，不是直接把 provider 的 `LIMSUP/LIMINF` 当成物理真值。[S-CNMC-2024-11535-PO]

### 6.3 150 MW 算术例子：只说明 provider-level 符号

假设某个 provider 聚合后的瞬时值为：

```text
PGC      = +50 MW
PGCINF   = −100 MW

RESADW   = PGC − PGCINF
         = 50 − (−100)
         = 150 MW
```

**醒目标注**：150 MW 是 provider-level 的符号算术示例，不是单个电池的 150 MW 充电功率，也不是已经取得 150 MW aFRR 资格。它表示从 `+50 MW` 的聚合发电位置走到 `−100 MW` 的最终下限，数值跨度为 150 MW。

当 SOC=100% 时，公开规则没有一条统一的 `SOC → LIMINF` 公式。项目能否把 `PGCINF/LIMINF` 设到某个负值，必须结合项目实时可达上下限、消费模式 UP 是否取得相应服务资格、并网/逆变器功率、能量和安全约束，以及 OS 对数据和测试的验证确定。SOC=100% 本身不自动证明可以提供 Down，也不自动把 `RESA` 变成 150 MW。

## 7. 激活后的剩余 offer：REOF、REMOF 和最终可用量

### 7.1 先算有效 offer，再扣已激活方向

**F｜规则事实（P.O.7.2 Annex III §§9.2–9.3）**：SRS 先对每个 provider、每个 QH 统计有效能量报价块，得到：

```text
REOFUP_b,q = 有效的 aFRR Up 能量报价量（规则变量，表示有效上调能量报价量）
REOFDW_b,q = 有效的 aFRR Down 能量报价量（规则变量，表示有效下调能量报价量）
```

如果 provider 处于 `OFF` 或 `OFF REE`，`REOFUP` 和 `REOFDW` 均按 0 处理。`REOF` 是有效能量 offer 的总量，不是容量市场的中标量。[S-CNMC-2024-11535-PO]

然后，SRS 按当前已激活的 `PaFRR_b(t)` 计算剩余 offer：正值代表 Up 激活，负值代表 Down 激活。

```text
若 −REOFDW_b,q < PaFRR_b(t) < REOFUP_b,q：
    REMOFUP_b(t) = REOFUP_b,q − PaFRR_b(t)
    REMOFDW_b(t) = REOFDW_b,q + PaFRR_b(t)

若 PaFRR_b(t) > REOFUP_b,q：
    REMOFUP_b(t) = 0
    REMOFDW_b(t) = REOFUP_b,q + REOFDW_b,q

若 PaFRR_b(t) < −REOFDW_b,q：
    REMOFUP_b(t) = REOFUP_b,q + REOFDW_b,q
    REMOFDW_b(t) = 0
```

最后，系统把物理实时 reserve 与扣除激活后的 offer margin 取最小值：

```text
REMOFDUP_b(t) = min(RESAUP_b(t), REMOFUP_b(t))
REMOFDDW_b(t) = min(RESADW_b(t), REMOFDW_b(t))
```

`REMOF` 是 OS/SRS 侧的“当前还能分配的 offer margin”，不是项目可以自由新增的订单，也不是 SOC 的替代变量。[S-CNMC-2024-11535-PO]

### 7.2 一个小表：激活如何消耗或转移方向

以下假设一个 QH 有 `REOFUP=100 MW`、`REOFDW=80 MW`，只用于读懂分段公式：

| 当前 `PaFRR` | `REMOFUP` | `REMOFDW` | 解释 |
|---:|---:|---:|---|
| 0 MW | 100 | 80 | 尚未激活 |
| +30 MW | 70 | 110 | Up 已消耗 30；公式把同一激活量转入 Down 侧可用 margin |
| −20 MW | 120 | 60 | Down 已消耗 20；公式把同一激活量转入 Up 侧可用 margin |
| +130 MW | 0 | 180 | 已超过原 Up offer；Up 剩余为 0，另一侧保留两方向 offer 的总量 |

**I｜边界**：表格只展示 SRS 的符号和 offer-margin 算术；它不意味着电池真的可以在激活瞬间无损切换方向，也不包含 SOC、斜率、并网限制或恢复要求。

## 8. 三层 reserve 上限：不能把三个“最大值”混成一个

| 层次 | 代表量 | 它回答什么 | 不应推出什么 |
|---|---|---|---|
| 1. 产品/资格层 | aFRR provider 的 habilitated / awarded reserve commitment | 供应商是否有资格、容量市场承诺多少 | 不等于某一电池此刻一定能输出同样 MW |
| 2. 实时物理层 | `RESAUP` / `RESADW` | 当前 `PGC` 到 OS/SRS 最终上下限还有多远 | 不等于已提交或可继续激活的 offer |
| 3. 激活后 offer 层 | `REMOFUP` / `REMOFDW`，再取 `min(RESA, REMOF)` | 在当前已激活状态下，系统还有多少可分配 margin | 不等于项目可以自行创建的新订单 |

**F｜100 MW 的正确位置**：`S-CNMC-2024-MP` Art.7(5) 要求每个二次调频 provider 的已 habilitada reserve 按 Up+Down 两方向合计至少为 100 MW。它是 provider/service-level 的资格门槛，不是单站功率、单个电池容量、每方向 100 MW，也不是说每个项目都自动获得 100 MW。[S-CNMC-2024-MP]

**U｜项目边界**：公开规则没有把某个独立 BESS 的装机 MW、SOC、`LIMINF`、`RESA` 和 100 MW provider 门槛做成一张项目级换算表。项目是否能以独立单站或聚合 provider 满足条件，仍需 OS/REE 的注册、测试、控制中心、UP/UF 和资格文件。

## 9. 结算、未履约和 BRP 不平衡

### 9.1 aFRR 的结算分层

**F｜规则事实**：P.O.7.2 §9 将二次调频结算拆成四类：reserve allocation、reserve-market non-compliance、accepted aFRR energy、real-time response non-compliance。容量分配按每 QH、每方向的边际容量价格结算；被认可的 aFRR 能量按激活周期的能量价格结算。[S-CNMC-2024-11535-PO]

| 层次 | 单位/基础 | 典型结果 |
|---|---|---|
| 容量分配 | €/MW × 该方向中标 MW | capacity payment；Up/Down 分开 |
| aFRR 能量 | €/MWh × 被认可的激活能量 | 与 `PaFRR`、`Pout`/PTR 和激活价格有关 |
| 容量/能量 offer 未履行 | 按 P.O.14.4 的支付义务 | 未提交等量能量支持、未保持承诺备用等 |
| 实时响应未履行 | `OFF`、响应不当、实时备用不足等 | P.O.7.2 §9.3.1–9.3.4 定义分类、优先级和罚价接口 |

**F**：P.O.7.2 §9.3.1–9.3.4 列出三类实时履约问题：provider 持续处于 OFF、响应不当、实时 reserve 不足；同一控制周期同时发生时，OFF 优先，其次响应不当，最后是备用不足。具体支付由 P.O.14.4 接口承接，不能把所有未履约合并成一个统一罚价。[S-CNMC-2024-11535-PO]

### 9.2 BRP 不平衡：不要重复扣一遍激活

**F｜规则事实**：P.O.14.4 使用：

```text
DESV = MEDBC − (POSFIN + AJUDSV)
```

其中 `MEDBC` 是 BRP 的计量位置，`POSFIN` 是最终计划/位置项，`AJUDSV` 是适用的平衡及其他调整项。已经通过 `AJUDSV` 计入的 aFRR 等平衡激活，不能再把同一调整当成未经解释的 BRP 偏差重复计算。[S-CNMC-2025-QH][S-SP-BOE-2025-RULES]

**I**：BSP 的 aFRR 能量结算和 BRP 的不平衡结算是两条相关但不同的账单链。市场成交量、PTR、Pout、边界计量和内部 SOC 各自有不同的时间、单位和责任主体。

## 10. 独立储能准入：已确认什么，不能确认什么

### 10.1 已确认的系统级入口

**F**：平衡条件允许储能持有人作为 BSP；每个服务都需要 OS 的对应 habilitación，实时信息交换、结构化数据和服务特定测试；一般 UP 服务 offer 下限为 1 MW；aFRR provider 另有 100 MW 合计 habilitated reserve 要求。[S-CNMC-2024-MP][S-REE-BAL-PART-2026]

**F**：P.O.3.8/相关测试和 P.O.7.2 Annex III 要求控制中心、AGC、实时通信、4 秒遥测/信号链、UP/UF 结构和响应核验。P.O.7.2 Annex II 的 PTR 组成还要求把现货、系统 redespacho 和适用平衡计划正确拼接。[S-CNMC-2024-11535-PO]

### 10.2 仍必须标为 U/open-critical

- 纯独立化学储能项目实际使用的送出 UP、取电 UP、UF、UO、PM（Market Participant / Participante del Mercado，市场参与者）、BSP、BRP 和 EIC（Energy Identification Code，能源识别码）/mRID（master Resource Identifier，资源主标识）crosswalk；
- 负消费遥测对应的消费模式 UP 资格、双向计量和项目控制中心配置；
- SOC 最低/最高带、可用 MWh、持续时长、补能窗口、恢复目标、跨产品冲突和故障免责；
- FCR（Frequency Containment Reserve / reserva de contención de frecuencia，一次调频/频率遏制备用）、SRAD（Servicio de Respuesta Activa de la Demanda / Active Demand Response Service，需求主动响应服务）对独立储能的资格、预认证、容量与结算；
- 2025-12-30 TERRE/LIBRA 停止后的 RR（Replacement Reserves，替代恢复备用）替代产品、平台、fallback、资格和数据字段；
- `PGCINF/LIMINF` 与项目 SOC、温度、功率或并网保护之间的项目级公式。

## 11. 2025 PTR 临时措施：按日期切片，不能回填

2025 年秋季至 2026 年 1 月出现了一条临时 PTR 跟踪措施链。它影响的是 P.O.7.2 Annex II §5 的跟踪义务及相关计划/系统约束，不是独立储能 SOC 规则。

| 日期 | F｜官方版本事件 | 研究含义 |
|---|---|---|
| 2025-10-20 / 10-21 | CNMC 决议签署/BOE 发布 `BOE-A-2025-21198`；正式 effects 从 2025-10-22 开始，初始 30 天，可按 15 天延长，总期限最多 3 个月 | 临时规则起点：有有效 aFRR 能量 offer 的时段必须跟踪 PTR；无 offer 时通常可选，但 OS 可出于安全要求临时要求跟踪 |
| 2025-11-18 / 11-19 | `BOE-A-2025-23407` 首次延长；文件确认初始期限到 2025-11-20，延长从其后起算 15 天 | 第一段延长约为 2025-11-21—12-05；保留文件日期和起止日期 |
| 2025-12-01、12-18 | 后续 15 天延长（在 `S-SP-BOE-2025-27212` 的官方 chronology 中记录） | 第二、三段分别覆盖 2025-12-06—12-20、12-21—2026-01-04 |
| 2025-12-29 / 12-31 | `BOE-A-2025-27212` 第四次延长，从第三次期限结束后再延长 15 天 | 临时链最后一段为 2026-01-05—01-19；不是 2025 规则永久化 |
| 2026-01-19 / 01-20 | `BOE-A-2026-1377` 签署/发布并从发布日生效 | 2026-01-20 起替换被修改段落：PTR 跟踪改为所有编程时段强制；有有效 aFRR offer 的时段还必须 4 秒跟踪/发送 consigna；BRP 偏差以季度小时能量对比 ramped PTR 积分 |

**F｜版本边界结论**：2025-10—2026-01-19 的临时措施不能写成 2025 全年规则；2026-01-20 的新版本不能回填 2025。`S-SP-BOE-2026-17285`（2026-08-07 发布）与 `S-SP-BOE-2026-17570`（2026-08-11 发布）又是 96 轮连续日内的后续版本，实际 application/go-live 需另按 OMIE 公告切片，不能倒填历史。

## 12. mFRR、RR 和 FCR/SRAD 的边界

**F**：2025 年 mFRR（Manual Frequency Restoration Reserve / reserva de recuperación de frecuencia manual，手动恢复备用）主要是可用备用和能量激活接口，MARI（Manually Activated Reserves Initiative，手动激活恢复备用平台）是主要欧洲路径；RR 通过 TERRE（Trans European Replacement Reserves Exchange，欧洲替代备用平台）的 LIBRA（TERRE 平台采用的公共 IT 解决方案）提供历史能量激活，至 2025-12-30 的最后运行边界停止。已有规则不能据此确认 mFRR 或 2025 RR 存在与 aFRR 相同的独立容量费市场。[S-CNMC-2024-11535-PO][S-CNMC-2025-QH][S-REE-PLATFORMS-2026][S-ENTSOE-TERRE-2026]

**I**：aFRR 的“容量承诺 + 能量支持报价 + 自动激活”链不能直接套到 mFRR/RR；不同产品的 FAT、交付 profile、报价门槛和结算不同。

**U**：截至 2026-08-11，FCR 独立储能预认证/补偿、SRAD 独立储能资格，以及 TERRE 后 RR 替代产品仍是 `open-critical`。特别是公开规则出现 1 MW、100 MW 等数字时，必须写清它是一般 offer 下限、aFRR provider 资格门槛还是某个产品/实时限值，不能称成单站功率要求。

## 13. 价格、成交量、激活量和结算数据从哪里来

| 数据层 | 第一方入口 | 可用于 | 边界 |
|---|---|---|---|
| OMIE 市场结果 | OMIE public file catalogue、日前/IDA/SIDC 价格、成交、曲线和计划文件 | 现货价格、成交量、市场结果和发布时间核验 | 逐笔订单、修订、保留期、项目 UO 可见性需逐项确认 |
| REE/eSIOS | REE/eSIOS 指标 API、archive/download 入口 | 平衡激活、价格、系统指标和公开计划/档案 | indicator ID、单位、时滞、DST、质量码和全年覆盖仍需逐指标验证 |
| ENTSO-E Transparency/EDI | A44、A09、A11 及平衡平台消息/代码表 | 跨区价格、商业交换、物理潮流和平台消息结构 | Spain zone/EIC、REE UP/UF、OMIE code、mRID crosswalk 未闭合 |
| REE/SIMEL/BRP | `reganeu`、`reganecuQH`、`p48cierre`、`rp48preccierre`、A/C 批次及 SIMEL | 事后计量、偏差、BSP/BRP 结算核验 | 很多文件在参与者权限区，不是实时公开决策输入 |

**F**：OMIE 格式文件区分 `Fecha Emisión`、数据日期、交付日期、时段/轮次和版本；REE archive API 也区分数据日期与发布日期。[S-SP-OMIE-PUBFILES-2025][S-REE-ESIOS-ARCHIVE-API-2026]

**I**：可执行决策输入只能使用当时已经发布且可取得的记录；M+1 计量、BRP 闭算/重算、迟延公开的 offer 文件和事后激活结果只能作为事后结算/审计输入。所有时序要保留时区、分辨率、单位、币种、`issued_at`、`data_date`、`retrieved_at` 和 `rule_version`。

## 14. 关键规则证据表（F）

详细 source block 在 [sources.md](sources.md)，下面把本报告最关键的结论、文件日期、生效边界、URL 和原文位置集中列出。本次新增 PTR 版本核查的访问日为 2026-09-04；基础规则 source block 保留其原登记访问日。2025 适用性按版本切片理解。

| Claim | 规则事实 | 官方文件（发布日期；生效/适用） | URL | 原文位置 |
|---|---|---|---|---|
| F-01 | aFRR 容量 Up/Down 独立、D-1、逐 QH、边际分配；中标带来等量能量 offer 义务 | CNMC/BOE `BOE-A-2024-11535`（2024-06-06；MARI/PICASSO 连接后适用，2025 PICASSO 月切片） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | Conditions Arts.7(4)-(5), 10(1)-(4)，HTML §§665-706 |
| F-02 | 容量每方向/每 QH 最多 25 段，最多一段不可分；1 MW 粒度、0.01 €/MW | 同上（2024-06-06；2025 适用） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | P.O.7.2 Annex I §§1.1-1.2，HTML §§2635-2684 |
| F-03 | 能量 aFRR 自动、FAT 5 分钟、15 分钟交付、每方向最多 25 段、€/MWh | 同上（2024-06-06；2025 适用） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | P.O.7.2 Annex I §§2.1-2.2，HTML §§2686-2718 |
| F-04 | PTR 由此前市场/系统计划聚合并 ramp；aFRR 交付是实际功率与 PTR 的差异 | 同上（2024-06-06；2025 适用，按后续 PTR 版本切片） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | P.O.7.2 Annex II §§1-5，HTML §§2719-2820 |
| F-05 | 负储能遥测仅在消费模式 UP 已获相应资格时纳入 Pout | 同上（2024-06-06；2025 适用） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | P.O.7.2 Annex III §8.1，HTML §§3021-3051 |
| F-06 | `RESAUP=PGCSUP-PGC`、`RESADW=PGC-PGCINF`；`REMOF` 分段并与 `RESA` 取最小 | 同上（2024-06-06；2025 适用） | https://www.boe.es/eli/es/res/2024/04/25/(6)/dof/spa/pdf | P.O.7.2 Annex III §§9.1-9.3，HTML §§3174-3287 |
| F-07 | 临时 PTR 规则：正式 effects 2025-10-22，后续延长至 2026-01-19 | CNMC/BOE `BOE-A-2025-21198`（2025-10-21；2025-10-22），`BOE-A-2025-23407`（2025-11-19；从 2025-11-20 后续延长），`BOE-A-2025-27212`（2025-12-31；2026-01-05—01-19） | https://www.boe.es/eli/es/res/2025/10/20/(1)；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-23407；https://www.boe.es/diario_boe/txt.php?id=BOE-A-2025-27212 | 各文件 Resuelve/Acuerda application；21198 HTML §§250-269、318-344；23407 PDF pp.1-3；27212 HTML §§102-131 |
| F-08 | 2026-01-20 起 PTR 跟踪所有时段强制；有效 aFRR offer 时仍需 4 秒跟踪/consigna | CNMC/BOE `BOE-A-2026-1377`（2026-01-20；2026-01-20） | https://www.boe.es/diario_boe/txt.php?id=BOE-A-2026-1377&lang=es | P.O.7.2 Annex II §5，HTML §§394-404；生效 §§210-228、408-416 |

## 15. F/I/A/U 总结和开放问题

### F｜规则事实

- 现货由 OMIE 经济出清、REE 计划/系统运行；成交经 PDBC/PDBF/PDVP/PDVD/PHF/PHFC 链条进入最终计划。
- aFRR 容量与能量是两层市场：容量 €/MW、能量 €/MWh；Up/Down 独立，容量和能量各自最多 25 段，不能混为一层。
- `PTR` 是 provider-level 的实时基准计划；`Pout` 是 aFRR 响应核验功率；负储能消费遥测只有在相应消费模式 UP 已获资格时才纳入 `Pout` 计算。
- `LIMSUP/LIMINF` 是 provider 发送边界，`CLIMSUP/CLIMINF` 是 SRS 计算边界，最终 `PGCSUP/PGCINF` 经过选择和一致性处理后才进入 `RESA`。
- `REMOF` 按已激活 `PaFRR` 分段调整，最终继续激活量为 `min(RESA, REMOF)`；它不是项目自由追加的 offer。
- 2025-10—2026-01 的 PTR 临时版本必须按正式 effect、延长协议和 2026-01-20 新版本切片。

### I｜研究解释

- 现货基准、备用承诺、实时物理余量和激活后 offer margin 可能同时约束同一逆变器；账户拆分不能消除物理冲突。
- 150 MW 示例只展示发电符号跨度；不能被解读为单站充电功率、SOC 可行性或资格结论。
- “现货充电/放电对应 Up/Down”的方向翻译用于理解，不是项目级授权或统一调度公式。

### A｜建模假设

本报告没有将规则缺口填成模型参数。未来若需要效率、SOC、持续时长、补能、恢复、可用率、费用或价格预测，必须另行登记建模假设并通过阶段门禁。

### U｜待确认（均不关闭 `open-critical`）

1. 项目级 UO/UP/UF、PM/BSP/BRP、EIC/mRID、计量点、控制中心和送出/取电 crosswalk；
2. 现货 PHF/PHFC 与 aFRR 可用备用、`Pout`、`PGC`、`LIM*` 的消息级校验顺序及冲突处理；
3. SOC、可用 MWh、持续时长、补能、恢复、激活后续承诺和跨 aFRR/mFRR/RR/FCR 的互斥或优先级；
4. FCR、SRAD 的独立储能准入、预认证、计量、补偿和罚则；
5. TERRE 停止后 2026 RR 替代产品、平台、fallback、资格和数据入口；
6. eSIOS indicator ID、单位、时间戳/时滞、质量位、DST 表示以及 2025 全年归档完整性；
7. 2025 市场/平衡/计量/结算文件的逐日修订链和私有 BRP/SIMEL 数据访问范围。

## 16. 研究边界与状态

本文件可以解释公开规则、运行逻辑、公式和算术例子，但不构成报价建议、收益承诺、项目资格证明、联合优化模型或历史回测。`modeling_approved=false` 继续保持；在上述 U 项关闭并经主线程复审前，不得把本报告内容写入国家模型配置或生产代码。

## 附录 A：晚间日前电价与边际技术分析（研究补充）

> 本附录承接“西班牙晚间电价分析”对话。它补充研究口径和可复现的分析方法，不改变本报告的规则基准，也不构成报价策略、收益结论或模型批准。对话中的样本统计来自本地 `data/raw/ES/Spain_Combined_Data.xlsx` 的 `Combined` 工作表；在正式回测前必须按基线任务重新计算并记录版本。

### A.1 结论摘要

**I｜研究解释**

1. 晚间价格上行的第一条可检验链条是“光伏出力快速下降 + 负荷上升”，因此 `Residual Load`（残余负荷）通常比总负荷更接近边际供需紧张程度。研究变量先定义为：

   \[
   RL_{dom,t}=Load_t-Wind_t-Solar_t
   \]

2. “直接价格设定技术（direct setter）”与“成本锚（cost anchor）”必须分开。CCGT 的燃料/碳成本可以作为晚间价格的候选成本锚，但实际触及边际价的卖方单位可能是水电或抽蓄；发电量爬坡本身不能证明某技术是 setter。

3. 跨境交换量占本地负荷的比例小，也不能推出其价格影响小。隐式耦合下，少量跨区交易可能位于边际；拥塞时价格分裂、未拥塞时价格趋同。商业计划交换与物理潮流必须分列。

**F｜官方边界**

- OMIE 2024 年报称，西班牙 2024 年标记最多边际小时的技术依次包括水电、风电、光伏和生物质/热电联产/废物；图 1.13 的统计是“标记价格的小时占比”，不是出力占比。[S-SP-OMIE-ANNUAL-2024]
- OMIE 月报的“Energía por tecnología al 95% del precio marginal”定义为：日前市场中已成交、报价价格不低于边际价 95%（含复杂报价）的能量；报告明确说明该图**不表示**哪种技术标记了边际价格，setter 另见图 1.8。[S-SP-OMIE-MONTHLY-2025]
- OMIE 2025 年 3 月月报明确指出，因 2025-03-18 启用新报价类型，按技术取得 95% 边际指标的数据只到 2025-03-18；新报价类型的首个交付日是 2025-03-19。[S-SP-OMIE-MONTHLY-2025][S-SP-OMIE-INST1-2025]

### A.2 对话样本的探索性统计（待复算）

下表只用于说明变量关系，数值不是官方统计。单位为 GW 和 €/MWh；`NetExport > 0` 统一表示西班牙净出口。若原始 `Combined` 字段正值表示进口，清洗时应先反号。

| 本地小时 | Load | Solar | Wind | `RL_dom` | NetExport | DA price |
|---:|---:|---:|---:|---:|---:|---:|
| 17:00 | 28.8 | 12.7 | 5.8 | 10.2 | 2.70 | 42.9 |
| 18:00 | 29.8 | 10.2 | 6.5 | 13.1 | 2.32 | 61.3 |
| 19:00 | 30.9 | 6.9 | 7.2 | 16.8 | 1.53 | 88.2 |
| 20:00 | 31.9 | 2.9 | 7.6 | 21.4 | -0.12 | 108.5 |
| 21:00 | 32.0 | 0.7 | 7.7 | 23.6 | -1.21 | 115.5 |
| 22:00 | 30.1 | 0.4 | 7.7 | 22.0 | 0.37 | 105.1 |

初步对话统计还报告：全样本 `Corr(Price, Load)≈0.31`、`Corr(Price, RL_dom)≈0.78`；晚间子样本 `Corr(Price, Gas)≈0.76`、`Corr(Price, RL_dom)≈0.74`。这些是描述性相关，不是因果估计；应在统一时区、缺失值和符号清洗后重算。

可选的事后解释变量为：

\[
RL_{adj,t}=RL_{dom,t}+NetExport_t
\]

但在预测任务中，最终已实现的跨境交换是市场耦合结果，可能包含价格信息；只能使用决策时已发布的交换能力、邻区预测负荷/价格或其他可得前置信息，不能把最终实现值直接作为无泄漏的预测输入。

### A.3 直接 setter、成本锚与 near-marginal

**I｜研究解释**

- CCGT 成本锚可用研究假设表达为：

  \[
  MC^{CCGT}_t=\frac{MIBGAS_t}{\eta}+CO2_t\times EF+VOM
  \]

  该式中的效率、排放因子、可变运维费和燃气/碳价格均需另行登记，不能从 OMIE setter 图直接推断。
- `95% near-marginal` 的作用是保留靠近清算价的已成交卖方报价，观察边际堆栈的技术组成，而不是强行寻找唯一最后一台机组。按技术聚合可以把 UO 级报价转换成国家级的 `NM_MW` 和 `NMShare`，但前提是有可追溯的 UO→technology crosswalk。

**A｜首版代理指标（待确认）**

对正边际价 `P_t>0`，首版把西班牙卖方、已成交行的 near-marginal 集合定义为：

\[
NM_{i,t}=1\{0.95P_t\le p_{i,t}\le P_t\}\,q_{i,t}
\]

按技术 `k` 聚合：

\[
NM\_MW_{k,t}=\sum_{i\in k}NM_{i,t},\qquad
NMShare_{k,t}=\frac{NM\_MW_{k,t}}{\sum_jNM\_MW_{j,t}}
\]

这里的上界 `p_i≤P_t` 和 95% 阈值都是研究假设；OMIE 官方 95% 图只规定“已成交能量且报价不低于边际价 95%”，不把该指标定义为 setter。复杂块、SCO、进出口行的价格语义必须先按文件格式核验。零价/负价单独标记，不套用上述乘法窗口。

### A.4 可下载数据与版本断点

**F｜规则/数据事实**

- OMIE 公共文件目录提供日前价格、程序、曲线和报价类别；按 UO 展开的月度曲线文件目录为 `curva_pbc_uof_YYYYMM.zip`，目前目录列出 2025-01、02、03 等月份。[S-SP-OMIE-FILES-2026][S-SP-OMIE-UOF-ARCHIVE-2026]
- OMIE 公共格式文件定义 `CURVA_PBC` 的字段：`Periodo`、`Fecha`、`Pais`（MI/ES/PT）、`Tipo Oferta`（C/V）、`Potencia Compra/Venta`、`Precio Compra/Venta`、`Ofertada(O)/Casada(C)` 和报价类型；同时说明复杂报价、进出口和市场分裂时的价格处理。[S-SP-OMIE-FORMATS-2025]
- OMIE `MARGINALPDBC` 文件按 period 提供 `MarginalPT` 和 `MarginalES`；正式计算应直接使用 `MarginalES` 作为西班牙区清算价。[S-SP-OMIE-FORMATS-2025]

**F｜版本断点**

2025-03-18 的日前新报价类型仍以小时交付，首个新类型交付日为 2025-03-19；同日开始日内 15 分钟交易。2025-10-01 才是日前 MTU15 的另一个独立断点。故 near-marginal 校准区间固定为 2025-01-01—2025-03-18；2025-03-19 以后只允许使用明确命名的 `Near-Marginal Technology Proxy`，不得称为 `Official Marginal Technology`。[S-SP-OMIE-INST1-2025][S-SP-OMIE-MTU15-DA-2025]

### A.5 校准前的研究边界

1. Official setter 必须保留 multi-label；同一小时多个技术同时标记价格时，各技术均为 1，频率加总可超过 100%。OMIE CAM 资料的 08:00—22:00 `horas punta` 只是公开汇总桶，不等于本研究的 19:00—22:00 晚间窗口。[S-SP-OMIE-CAM-2025]
2. 先用 2025-01-01—03-18 的月报 setter 做 ground truth，再用 `curva_pbc_uof` 计算 90%、92.5%、95%、97.5% 和绝对价差窗口，比较 precision、recall、F1、top-1/top-2 命中率与 `NMShare` 阈值敏感性。
3. 只有在样本时间映射、UO→technology crosswalk、复杂订单处理和版本/修订记录通过主线程审核后，才进入 2025-03-19 以后代理指标延伸、Combined 合并和任何模型实现。

### A.6 本附录新增未决问题（U）

- OMIE 月报图表的 `Hora` 标签与交付小时 19:00—22:00 的精确映射；
- `curva_pbc_uof` 中复杂块、SCO、进出口行的“已成交功率”如何与 technology 聚合对应；
- 2025-01—03 曲线压缩包的版本、修订与下载完整性；
- 公开 UO 技术清单及未映射 UO 的处理；
- 事后 `NetExport` 与预测时可用跨区能力/交换预测的分离。
