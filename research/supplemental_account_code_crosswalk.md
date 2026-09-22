# 西班牙独立储能项目级账户与代码映射（SUP-04）

> 研究对象：西班牙大陆竞价区（peninsular bidding zone）的独立非水电化学储能。  
> 历史期：2025-01-01—2025-12-31；规则基准日：2026-08-11。  
> 本文件只做账户、主体和代码的证据化 crosswalk，不做报价策略、收益测算、MILP、代码、回测或预测。2026-08-11 之后的页面只用于说明当前操作入口或版本边界，不能倒填为2025规则。

## 0. 先给结论：一个“项目”不是一个市场代码

### F｜规则事实

西班牙的独立储能项目至少会同时出现在四个层次：

1. **行政/并网与计量层**：设施、并网边界、计量点和（如适用）CUPS、CIL/RAIPRE等登记信息；REE的SIMEL和计量责任链处理边界点数据。[S-REE-ADMISSION-GUIDE-2024][S-REE-SIMEL-FAQ-STORAGE-2026][S-REE-PF-CIL-2015]
2. **系统运行层**：UP（Unidad de Programación）是能量计划的基本单元，UP可由一个或多个UF（Unidad Física）组成。每个UP和UF都要有EIC，EIC由西班牙本地EIC办公室按ENTSO-E编码体系办理。[S-SP-PO31-2024-STORAGE][S-REE-PARTICIPANT-2026][S-REE-EIC-2026][S-ENTSOE-EIC-2026]
3. **现货/NEMO层**：OMIE以UO（Unidad de Oferta）接受报价和发布成交/计划文件；UO注册与UP存在关联，但仅间接代表可在一个UO聚合多个被代表主体的程序，直接代表受到单一被代表程序的限制。UO是OMIE市场侧代码，不能直接等同于UP、UF或EIC。[S-SP-BOE-2025-RULES][S-SP-OMIE-PUBFILES-2025]
4. **平衡、偏差和结算层**：PM可以提供平衡服务并成为BSP；BRP对其平衡组偏差承担财务责任；结算文件还会按UP、BRP、调节区或结算单元使用标识。详细BRP结算文件通过REE的受限入口提供，不等于公共数据。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES][S-REE-LIQ-ACCESS-2026]

### I｜研究解释

因此，项目级数据整合应把“项目/设施—UF—UP（送出和吸收）—UO（卖出和买入）—报价/成交ID—计划—计量—BRP偏差—结算”看作一条**有层次的身份链**。公开资料可以确认各层代码的制度目的和部分转换规则，但不能仅凭公开网页推导出某一真实项目的全部代码。

已审公开资料确认 CUPS/CIL 在特定计量或发电登记流程中出现，但尚未确认纯独立 BESS 的普遍适用路径；因此不能把 CUPS/CIL 直接当作所有独立储能项目的统一市场代码。[S-REE-ADMISSION-GUIDE-2024][S-REE-SIMEL-FAQ-STORAGE-2026][S-REE-PF-CIL-2015]

### U｜必须保留的边界

截至本任务检索范围，没有找到公开的、可直接输入项目名称就返回“CUPS/CIL—UF/EIC—UP/EIC—OMIE UO—BSP/BRP—mRID”的官方总表。项目实际接入前，必须从REE、OMIE、计量责任方、代表和BRP/BSP合同中取得项目级文件；在取得前，相关字段均为 `U/open` 或 `U/open-critical`（详见第8节和 `spot_open_questions.md`）。

## 1. 身份链：从设施到结算

### 1.1 项目级流程图（技术流程，不是收益流程）

```text
行政登记/并网边界/计量点
          │
          ▼
   UF（设施/技术运行单元，EIC）
          │  P.O.3.1：独立非水电储能按送出/吸收拆分UP
          ├───────────────┐
          ▼               ▼
  UP-venta/送出UP      UP-compra/吸收UP
   （BRP+PM维度，EIC）   （BRP+PM维度，EIC）
          │               │
          └───────┬───────┘
                  ▼
       OMIE UO-venta / UO-compra
        （OMIE市场代码；卖/买方向）
                  │
                  ▼
      报价：agent/IdRemitente + IdOferta + IdUnidad(UO)
                  │
                  ▼
    出清/连续成交/最终计划：PDBC/PDBF/PDVP/PDVD/
       PIBCI/PIBCA/PHF/PIBCIC/PIBCAC/PHFC等
                  │
                  ▼
     PM向REE按UP报计划，并在需要时分解至UF
                  │
                  ▼
       REE系统校核 →（如发生）平衡激活/再调度
                   → 实时计划与指令
                  │
                  ▼
       SIMEL边界计量：送出/吸收有功及质量信息
                  │
                  ▼
      BRP最终位置 + 计量 + 平衡能量/再调度
                  │
                  ▼
   不平衡与结算：BRP/UP/调节区/公式代码/结算期
```

**图中哪些箭头是硬规则：**

- `UF → UP`：UP是计划基本单元，UP由一个或多个UF组成；独立非水电储能原则上设送出UP和吸收UP，并按BRP+PM组织，同一设施对应相应UF。[S-SP-PO31-2024-STORAGE]
- `UP ↔ EIC`、`UF ↔ EIC`：P.O.3.1要求每个UP/UF有EIC，EIC作为系统登记和REMIT等报告的唯一键。[S-SP-PO31-2024-STORAGE]
- `UP → UO`：OMIE规则要求UO注册与UP注册关联，且UO代码由OMIE建立；仅间接代表可在一个UO聚合多个被代表程序，直接代表受到单一被代表程序限制，不能把它理解为设施的一对一代码。[S-SP-BOE-2025-RULES]
- `报价 → 市场结果/计划`：OMIE文件格式和市场规则使用报价人/代理代码、报价ID、UO代码，并发布相应计划和结果文件。[S-SP-BOE-2025-RULES][S-SP-OMIE-PUBFILES-2025]
- `最终位置 + 计量 → BRP偏差`：P.O.14.4将BRP偏差建立在计量、最终位置以及平衡能量/实时再调度调整之上；结算标识和详细文件由REE结算系统处理。[S-SP-BOE-2025-RULES][S-REE-LIQ-GUIDE-2024]

**图中尚不能公开锁定的箭头：**

- 平衡平台激活消息中的具体西班牙项目代码与UO/UP/UF的字段级对应；
- 计量点（CUPS、CIL、边界点代码）与独立储能UF/UP的逐字段对应；
- ENTSO-E/CIM交换层的 `mRID` 与西班牙PM/BSP、UP/UF/EIC及REE结算文件的逐笔对应；
- 某一项目的控制中心、调节区、组合代码、BRP结算单元和私有结算文件名。

这些内容不能用“通常做法”补齐，均保留为U/open-critical。

### 1.2 一条交易/运行记录至少要保留哪些键

| 环节 | 关键键（公开资料能确认的范围） | 谁持有/生成 | 状态 |
|---|---|---|---|
| 主体注册 | 法人NIF；OMIE agent code；ACER/REMIT code；PM/代表/BRP关系 | OMIE、REE、主体/代表 | F：主体需要注册资料；项目实际值U |
| 系统结构 | UP EIC、UF EIC；送出UP/吸收UP；BRP+PM维度 | REE/西班牙EIC办公室 | F：结构规则；项目实际值U |
| OMIE报价 | `IdRemitente`、`IdOferta`、`IdUnidad`（`tipo=UO`）及日期/时段/市场 | OMIE/市场主体 | F：字段存在；具体接口版本按文件日期核对 |
| 市场计划 | PDBC、PDBF、PDVP、PDVD、PHF，以及连续市场的PIBCI/PIBCA、PIBCIC/PIBCAC/PHFC | OMIE/REE | F：文件角色和名称；跨系统逐笔桥接U |
| 送REE计划 | UO/UP/UF分解、时段、功率/能量、程序状态 | PM、REE | F：PM需按UP提交并可分解UF；项目接口字段U |
| 平衡激活 | BSP/资源/报价/激活消息ID；可能存在平台 `mRID` | REE/欧洲平台/BSP | U/open-critical：未找到公开西班牙项目级crosswalk |
| 计量 | 边界点、计量责任方、送出/吸收有功、时间戳、质量位 | SIMEL、计量责任方、REE | F：SIMEL受限、双向计量概念；字段crosswalk U |
| 偏差 | BRP、结算UP/调节区、最终位置、计量、调整能量、公式代码 | REE结算系统 | F：概念和部分字段；项目值/私有文件U |

## 2. 主体和角色：谁对什么负责

### F｜规则事实

| 角色 | 简单理解 | 与独立储能的关系 |
|---|---|---|
| PM（Participante en el Mercado） | 在一个或多个电力市场发出买卖/管理指令的市场参与主体 | 储能持有人或其代表可以作为PM；PM是市场及平衡服务入口的主体概念。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES] |
| 市场代理/代表（representante） | 代表储能持有人进行市场交易、付款和收费 | 直接代表以持有人名义和账户行事；间接代表以自己名义、为持有人账户行事。两者的付款、保证金和结算主体不同。[S-SP-BOE-2025-RULES][S-SP-PO31-2024-STORAGE] |
| BSP（Balancing Service Provider） | 提供平衡能量和/或平衡备用的PM | BSP是“服务提供”角色，不自动等于BRP，也不自动等于代表；储能需满足相应REE预认证和技术接口。[S-SP-BOE-2025-RULES][S-REE-BAL-PART-2026] |
| BRP（Balance Responsible Party） | 对平衡组偏差承担财务责任的主体 | PM可自行承担，也可合同委托给其他BRP；项目合同必须明确偏差和保证金责任。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES] |
| 结算主体（Sujeto de Liquidación） | 负责向REE收付款、提供结算保证金的BRP/代表 | 直接代表下通常为持有人；间接代表下为代表。不能仅凭“代表”二字确定结算责任。[S-SP-BOE-2025-RULES] |
| 计量责任方（Encargado de la Lectura） | 对边界点计量读取负责的实体 | 与PM/BRP可以是不同主体；SIMEL数据权限按计量参与者/其代理开放。[S-SP-BOE-2025-RULES][S-REE-SIMEL-FAQ-STORAGE-2026] |
| 控制中心/CCGD | 接收和发送实时运行、调节或控制信息的系统接口 | 具体控制中心、备用控制中心、调节区和项目归属需以REE项目文件确认，不能由UO/EIC推定。[S-SP-BOE-2025-RULES][S-CNMC-2023-8113-PO92] |

### I｜最容易混淆的三组关系

1. **PM ≠ BSP**：PM是市场参与者，BSP是实际提供平衡服务的PM。一个PM可以不提供平衡服务；成为BSP还要走REE的服务资格/预认证流程。
2. **BSP ≠ BRP**：BSP负责可用平衡服务和激活履约，BRP负责平衡组的最终财务偏差。两者可能由同一法人承担，也可能由合同安排成不同主体；公开规则没有给某个项目默认组合。
3. **代表 ≠ 代码层级**：代表可以改变OMIE UO聚合方式和结算主体，但不会把UO变成EIC，也不会自动消除储能的UP/UF结构。直接/间接代表的法律和付款责任必须在合同中核验。

### F｜直接代表和间接代表的代码/责任差异

| 项目 | 直接代表（direct） | 间接代表（indirect） |
|---|---|---|
| 行事名义 | 以被代表持有人名义、为其账户 | 以代表自身名义、为持有人账户 |
| 结算主体 | 规则定义下通常由被代表持有人承担收付款/保证金 | 规则定义下由代表承担收付款/保证金 |
| UP使用 | 规则文本要求使用持有人UP | 对大于1 MW的情形，可使用代表UP或持有人UP；单一聚合UF的代表应使用代表UP |
| OMIE UO | 只能对应一个被代表程序的直接代表限制 | 可聚合多个被代表程序，但不代表设施层UF被合并 |
| 项目待核对 | 合同、保证金、BRP责任、UP/EIC | 合同、保证金、BRP责任、代表UP/EIC、UO聚合边界 |

上述表格的前三行是规则事实；最后一行是项目实施时必须索取的资料，不是默认答案。[S-SP-PO31-2024-STORAGE][S-SP-BOE-2025-RULES]

## 3. UO、UP、UF：三个“单元”分别干什么

### 3.1 UP：计划和系统运行的基本单元

### F｜规则事实

- UP是能量程序/计划的基本单元，UP可以包含一个或多个UF；UP/UF均需要EIC。[S-SP-PO31-2024-STORAGE]
- 对不与发电或需求设施关联的独立非水电储能，规则要求分别建立**送出（delivery/sale）UP**和**吸收（uptake/purchase）UP**；每一类UP按BRP+PM组织。系统运营安全需要时，REE/DSO可要求按节点增加UP，尤其是大容量或影响系统安全的设施。[S-SP-PO31-2024-STORAGE]
- 每个UP由相应设施的UF组成，设施划分使用行政登记键或法规规定的结构；这个规定并没有给出一个可公开下载的“项目名称—UF代码”总表。[S-SP-PO31-2024-STORAGE]

### I｜对项目数据的含义

对纯独立储能而言，充电和放电不应在数据层强行压成一个单向UP。至少要保存送出UP、吸收UP及各自UF/EIC；若项目由不同BRP或PM管理，UP结构还会随BRP+PM组合变化。混合储能、与发电/需求关联的储能，以及节点安全要求，可能采用不同结构，不能套用本节的纯独立储能简化图。

### 3.2 UF：设施/物理运行单元

### F｜规则事实

UF是组成UP的物理/设施层单元，并且需要独立EIC。P.O.3.1对独立储能提出“每个设施一个UF”的结构方向，但实际行政登记键、并网点、计量边界与UF之间的字段仍由REE结构数据/项目申请确定。[S-SP-PO31-2024-STORAGE][S-REE-PARTICIPANT-2026]

### U｜不要做的推断

不能把“RAIPRE登记号”“CIL”“CUPS”“并网点编码”任选其一当成UF代码。REE的2024准入指南是以RCR发电设施为主要案例，说明了CIL-RAIPRE和代码申请流程，但没有为所有独立BESS公开一个同样完整的CUPS/CIL→UF映射。[S-REE-ADMISSION-GUIDE-2024]

### 3.3 UO：OMIE市场侧报价/计划单元

### F｜规则事实

- UO代码由OMIE在市场注册时分配；市场主体以UO提交/接收市场结果和计划。[S-SP-BOE-2025-RULES]
- OMIE规则要求UO注册与UP注册关联，且在代理人配置下两者需要保持有效关联；西班牙半岛UO只能关联半岛UP。UO的卖出/买入方向决定其市场最终位置方向。[S-SP-BOE-2025-RULES]
- 间接代表可以在UO层聚合多个被代表程序；直接代表受到单一被代表程序的限制。故“注册关联”不应简化为“一个设施只有一个UO”。[S-SP-BOE-2025-RULES]

### I｜对文件归档的要求

每个OMIE文件记录至少要同时保存：市场日、市场/回合、UO、报价人/代理代码、报价ID（如可见）、文件发行时间、数据日期和版本/更正信息。只保留“价格+时段”会失去从报价追到计划、再追到结算的能力。[S-SP-OMIE-PUBFILES-2025]

## 4. EIC、mRID、CUPS、CIL和“技术单元代码”怎么区分

| 名称 | 所属层次 | 可确认的用途 | 是否可直接代替另一代码 |
|---|---|---|---|
| EIC | ENTSO-E/国家市场与系统参与者编码 | 对UP、UF等实体提供唯一识别；西班牙有本地EIC办公室；用于跨主体系统交换和报告 | 否。EIC不是OMIE UO，也不是CUPS/CIL |
| mRID | ENTSO-E/CIM/消息与模型交换 | 用于交换对象、资源或文档实体的全局标识；具体含义取决于消息/数据模型 | 否。未确认西班牙项目mRID与UP/UF/EIC的官方总表 |
| OMIE agent code | OMIE市场主体层 | 识别OMIE市场代理；报价消息含 `IdRemitente` | 否。不能直接当作UO/EIC |
| UO | OMIE市场报价/计划层 | 市场买卖和市场结果的单元代码 | 否。可能与多个被代表程序的市场处理有关 |
| UP | REE系统计划层 | 能量程序和计划的基本单元；独立储能有送出/吸收UP结构 | 否。需要EIC，且不等于UO |
| UF | REE设施/物理单元层 | 一个或多个UF组成UP；独立储能设施按规则形成UF | 否。具体行政/计量映射待项目核验 |
| CUPS | 计量点/供应点层 | 识别电力供应/计量点；REE当前储能FAQ在特定CIL流程中引用CUPS | 否。对独立储能的普遍适用边界U |
| CIL/RAIPRE | 特定发电登记/设施层 | REE指南说明CIL与CUPS、RAIPRE的关系，主要针对可再生/热电联产/废弃物等发电登记 | 否。纯独立BESS是否需要同一CIL路径必须按项目类型确认 |
| 计量边界/边界点代码 | SIMEL计量层 | 识别结算计量位置、计量责任和送出/吸收方向 | 否。当前公开资料未提供面向纯独立BESS的完整字段表 |
| “技术单元/组合代码” | 项目或平台操作层的可能称呼 | 可能指UF、UP组合、调节区、控制中心或聚合资源，但不同文件可能含义不同 | 不可自行统一；必须以文件字典和项目合同确认 |

### F｜EIC和mRID的证据边界

ENTSO-E的EIC体系由中央办公室和授权本地办公室维护，目的是在内部电力市场中统一识别参与方、资源和区域；REE说明西班牙EIC办公室负责相应编码。EIC是规则和注册层的身份键。[S-ENTSOE-EIC-2026][S-REE-EIC-2026]

ENTSO-E/CIM交换文件另使用 `mRID` 对交换模型中的资源/对象进行全局识别；`mRID`属于消息/模型层。它可能在平台、CIM或数据交换中出现，但本次未找到一份官方文件把某个西班牙项目的 `mRID` 直接映射到其REE UP/UF EIC、OMIE UO或CUPS。因此只能把它作为“平台/消息层候选键”，不能把它当成项目注册代码。[S-ENTSOE-EDI-2024][S-ENTSOE-MRID-2024]

### U｜CUPS/CIL的项目类型限制

REE当前储能FAQ明确了SIMEL边界点申请、计量图纸、设备和授权等材料；其CUPS/CIL步骤又带有特定发电登记条件。2015年旧版CIL指南也将CIL描述为与CUPS拼接/关联的发电识别方式。由于这些公开例子不能证明纯独立化学储能必须、或不必、走同一CIL路径，本报告将“纯独立BESS的CUPS、CIL、RAIPRE和边界点代码”列为 `U/open-critical`。[S-REE-SIMEL-FAQ-STORAGE-2026][S-REE-PF-CIL-2015]

## 5. 报价—成交—激活—计划—计量—偏差—结算的字段链

### 5.1 报价和市场结果

### F｜OMIE层

OMIE的公开文件规范使用分号分隔文件、文件发行日期和数据日期；报价/消息中可以看到发送代理 `IdRemitente`、报价标识 `IdOferta` 和带有 `tipo="UO"` 的单位标识 `IdUnidad`。OMIE还定义了日前、日内和连续市场的结果/计划文件，例如PDBC、PDBF、PDVP、PDVD、PIBCI、PIBCA、PHF、PIBCIC、PIBCAC和PHFC。[S-SP-OMIE-PUBFILES-2025][S-SP-BOE-2025-RULES]

### I｜推荐的交易记录键

项目数据仓库中，OMIE层应采用：

```text
(market, session/round, delivery_date, period,
 OMIE_agent_code/IdRemitente, UO/IdUnidad, offer_id/IdOferta,
 file_issue_datetime, data_date, revision/version)
```

这只是研究解释下的归档最小键，不是新增市场规则；`offer_id`、`revision/version`在不同公开文件/权限层的完整可见性仍需按文件版本抽样确认。

### 5.2 成交后向REE提交计划

### F｜规则事实

市场结果形成后，PM按UP向REE提交/分解程序；当一个UO包含多个UP时，系统运营层需要UP→UF分解以便形成系统计划，REE随后发布PDBF等系统计划文件。双边合同也以UP为基础申报。[S-SP-BOE-2025-RULES][S-SP-PO31-2024-STORAGE]

### I｜跨文件归档

因此，不能用OMIE的UO作为REE计划的唯一主键。至少要保存一份项目维护的映射表：`OMIE UO（买/卖） ↔ REE UP（买/卖） ↔ UF（设施） ↔ EIC`，并记录生效日期。该映射表的具体值不是公开规则可推导内容。

### 5.3 平衡激活

### F｜规则事实

REE的平衡服务由BSP提供，平衡平台和本地规则使用服务、资源、程序、控制中心及实时信息等概念；P.O.9.2历史版本还规定储能实时信息/有功进出、SOC等字段。[S-REE-BAL-PART-2026][S-CNMC-2023-8113-PO92]

### U｜不得伪造字段链

本次公开资料检索没有确认以下等式：

```text
欧洲平台 activation.mRID = 西班牙BSP代码 = REE UP/UF EIC = OMIE UO
```

这些字段可能在不同消息层分别存在，但没有官方西班牙项目级crosswalk就不能将它们合并。应向REE/平台接口和BSP资格文件索取：激活消息样例、资源标识、报价标识、UP/UF/EIC字段、时间戳、取消/替代状态以及激活后计划调整规则。该问题为 `open-critical`。

### 5.4 计量和SIMEL

### F｜规则事实

- REE的SIMEL是受限的计量系统，访问权限授予各计量参与者或其代理；边界点建档需要单线/三线图、设备资料、授权、测试和技术合同等材料。[S-REE-SIMEL-FAQ-STORAGE-2026]
- 2025计量/结算规则要求区分储能的送出和吸收有功等方向；MITECO 2025决议使十五分钟计量程序逐步生效，具体逐点字段和项目文件仍需按版本核验。[S-MITECO-2025-ISP]
- REE结算指南使用SIMEL、`reganeu`/`reganecuQH`、`p48cierre`、A1–A5/C1–C5等文件/字段名称，但指南是非规范性核对材料，详细BRP结算ZIP通过受限入口提供。[S-REE-LIQ-GUIDE-2024][S-REE-LIQ-ACCESS-2026]

### U｜计量字段映射

公开资料不能确认某独立BESS项目下列字段的确切名称和方向：

```text
边界点/计量表ID → CUPS/CIL/计量单元 → Activa Entrante/Saliente
→ UF/UP → BRP/结算单元 → p48/偏差/激活结算
```

因此，不得以“充电一定是Entrante、放电一定是Saliente”替代项目计量定义；应读取该项目SIMEL计量方向说明、边界点协议、计量责任方数据字典和至少一个已结算交付日样例。

### 5.5 偏差和结算

### F｜规则事实

P.O.14.4把BRP偏差建立在指定计量与最终位置之间，并考虑平衡能量和实时再调度等调整；相关结算注释还包含交易日期、计划时段、市场段、权利/义务、公式代码和UP/BRP特定结算单元或调节区代码。[S-SP-BOE-2025-RULES]

### I｜结算追溯

项目级结算追溯至少应能回答四个问题：

1. 哪个BRP对该UP/调节区的偏差负责？
2. 该时段的最终位置来自哪个PDBF/PHF/PHFC或其他正式计划？
3. 计量值来自哪个边界点和哪一版SIMEL数据？
4. 激活/再调度调整引用哪个服务、资源和公式代码？

如果结算ZIP只保留金额而没有这些上游键，它只能用于总额核对，不能用于解释偏差来源。

## 6. 公开可确认 vs 项目必须获取

| 项目字段/文件 | 公开官方资料可以确认 | 项目必须获取或核验 | 状态 |
|---|---|---|---|
| 法人/主体 | OMIE市场主体资格、NIF、ACER/REMIT、银行和加入合同类别 | 实际NIF、agent code、ACER code、账户和生效日 | F + U |
| PM/代表/BRP | 角色定义、直接/间接代表法律效果、BRP财务责任 | 代表合同、BRP委托、保证金责任、终止/替换流程 | F + U/open |
| UO | OMIE分配UO、买卖方向、代表模式限制 | UO-买/卖代码、代理聚合边界、生效/停用日期 | F + U/open-critical |
| UP/UF | 独立储能送出/吸收UP结构、UF组成和EIC要求 | UP/UF短码/长码、EIC、设施清单、节点附加UP | F + U/open-critical |
| CUPS/CIL/RAIPRE | 特定计量/发电登记流程和CUPS/CIL概念 | 纯独立BESS的适用路径、CUPS/CIL、RAIPRE/并网登记号 | F + U/open-critical |
| 计量/SIMEL | 边界点准入材料、SIMEL受限访问、双向有功概念 | 边界点ID、计量责任方、主/备用表、方向、质量位、数据接口 | F + U/open-critical |
| OMIE报价/计划 | `IdRemitente`、`IdOferta`、`IdUnidad(UO)`和主要文件名 | 项目实际订单、撤单/替代、版本、私有文件和历史修订 | F + U/open-critical |
| 平衡激活 | BSP、平衡服务、REE/欧洲平台存在 | 资源ID、activation mRID、BSP/UP/UF/EIC/UO字段映射 | F + U/open-critical |
| 结算/偏差 | BRP偏差概念、公式/结算标识类别、REE结算入口 | 每个UP/BRP/调节区结算单元、p48/结算ZIP、修订记录 | F + U/open |
| CCGD/调节区/组合 | 系统运行和调节区概念 | 项目控制中心、备用控制中心、调节区/组合代码及责任 | F + U/open |

## 7. 2025历史期的版本切片

### F｜已确认的时间边界

- 2025-01-01—2025-03-17：应使用上一版适用的OMIE/系统运行程序，不能把2025-03-18修订后的条文回填到更早日期。[S-SP-BOE-2024-RULES][S-SP-BOE-2025-RULES]
- 2025-03-18：CNMC/BOE新的市场规则初始修订生效；具体条文的逐日和项目接口仍需按文件版本核对。[S-SP-BOE-2025-RULES]
- 2025-05-01：MITECO计量程序修订按决议生效条款进入适用边界；十五分钟计量与储能双向有功字段不能回填到更早规则期。[S-MITECO-2025-ISP]
- 2025-10-01：日前市场十五分钟MTU切换边界；OMIE文件和数据归档应保存市场日、文件发行时间和格式版本。[S-SP-OMIE-MTU15-DA-2025][S-SP-OMIE-PUBFILES-2025]
- P.O.3.1的独立储能送出/吸收UP结构已在2024年修订文本中建立，并要求按REE通知的应用日不迟于2024年12月落实；对2025项目实际是否已完成结构注册，仍需项目登记证据，不能仅凭规则文本确认。[S-SP-PO31-2024-STORAGE]

### U｜不可回填事项

当前页面和2026年接口说明不能证明某个代码在2025全年度保持不变。回测或结算复核前应保存：代码生效/停用日期、OMIE格式版本、REE结构版本、计量数据发布日期和更正记录；如果无法取得，数据状态必须是U，而不是“静态主数据”。

## 8. F/I/A/U状态清单

### F｜规则事实

- UP/UF/EIC、独立储能送出/吸收UP、PM/BSP/BRP/代表、OMIE UO和报价字段、REE结算入口等概念与部分流程有官方依据，来源在第9节逐项列出。
- REE和OMIE均有明确的注册、市场文件或参与入口，但操作页面本身不能替代BOE/CNMC规范性规则。

### I｜研究解释

- “身份链”是跨机构数据整理的建议结构；它帮助把市场结果、系统计划、计量和偏差放在同一项目上，但不创造新的市场代码。
- “送出UP/吸收UP分开保存”是对独立储能规则结构的数据库表达；并不意味着每个项目在每个时段都有非零功率或都有相同的UO聚合方式。

### A｜建模假设

本SUP-04文件不引入可供模型使用的新建模假设。任何后续若需将项目级字段简化成一个技术单元、一个BRP或一组静态代码，必须在模型任务中单独登记A，并引用已确认的项目文件；不得把本文件的I层直接写成规则参数。

### U｜open/open-critical清单

- `U/open-critical`：项目实际PM/agent/UO/UP/UF/EIC；送出/吸收UP是否按节点追加；CUPS/CIL/RAIPRE对纯独立BESS的适用；SIMEL边界点及双向方向；激活资源ID和mRID crosswalk；OMIE报价/计划逐笔连接及版本/修订；2025逐日版本和代码生效日期。
- `U/open`：代表合同和BRP委托的项目对应关系；CCGD/调节区/组合代码；BRP结算单元和私有结算文件；不同代理架构下的UO聚合粒度；平台消息字段在公开层的保留期。

未解决问题已同步写入 `countries/ES/spot_open_questions.md` 的“ES-SUP-04 项目级账户和代码映射”小节；在这些问题关闭前，不得将项目级crosswalk用于收益、策略或模型。

## 9. Claim-to-source ledger

| Claim ID | 关键结论 | 层级 | Source ID |
|---|---|---|---|
| SUP04-F01 | UP是计划基本单元；UP由UF组成；UP/UF需要EIC | F | S-SP-PO31-2024-STORAGE |
| SUP04-F02 | 独立非水电储能原则上分送出UP和吸收UP，按BRP+PM组织 | F | S-SP-PO31-2024-STORAGE |
| SUP04-F03 | PM、BSP、BRP、代表和结算主体的角色边界 | F | S-SP-PO31-2024-STORAGE; S-SP-BOE-2025-RULES |
| SUP04-F04 | OMIE UO代码、与UP关联及代表模式聚合限制 | F | S-SP-BOE-2025-RULES |
| SUP04-F05 | OMIE报价消息字段和市场计划/结果文件名 | F | S-SP-OMIE-PUBFILES-2025; S-SP-BOE-2025-RULES |
| SUP04-F06 | REE准入、EIC办公室、UP/UF申请入口 | F | S-REE-PARTICIPANT-2026; S-REE-EIC-2026; S-REE-ADMISSION-GUIDE-2024 |
| SUP04-F07 | SIMEL边界点资料和权限、CUPS/CIL的限定性使用 | F/U | S-REE-SIMEL-FAQ-STORAGE-2026; S-REE-PF-CIL-2015 |
| SUP04-F08 | BRP偏差与REE结算/私有文件边界 | F | S-SP-BOE-2025-RULES; S-REE-LIQ-ACCESS-2026; S-REE-LIQ-GUIDE-2024 |
| SUP04-F09 | EIC体系与mRID的层次差异；未找到西班牙项目级总表 | F/U | S-ENTSOE-EIC-2026; S-REE-EIC-2026; S-ENTSOE-MRID-2024; S-ENTSOE-EDI-2024 |
| SUP04-I01 | 跨机构身份链和项目级归档最小键 | I | SUP04-F01–F08；S-SP-OMIE-PUBFILES-2025 |
| SUP04-U01 | 纯独立BESS的实际代码、CUPS/CIL、激活mRID和结算字段未公开闭合 | U | S-REE-ADMISSION-GUIDE-2024; S-REE-SIMEL-FAQ-STORAGE-2026; S-ENTSOE-MRID-2024; S-REE-LIQ-ACCESS-2026 |

## 10. 本文件采用的官方资料

完整来源登记见 `countries/ES/sources.md` 中以 `S-*` 标记的来源块。核心来源包括：

- CNMC/BOE，P.O.3.1、P.O.14.1、P.O.14.4及2025市场规则（S-SP-PO31-2024-STORAGE、S-SP-BOE-2025-RULES）；
- REE，参与者准入、EIC办公室、SIMEL储能FAQ和结算访问/核对指南（S-REE-PARTICIPANT-2026、S-REE-EIC-2026、S-REE-ADMISSION-GUIDE-2024、S-REE-SIMEL-FAQ-STORAGE-2026、S-REE-LIQ-ACCESS-2026、S-REE-LIQ-GUIDE-2024）；
- OMIE，市场主体规则及2025-09-30版公共文件格式（S-SP-OMIE-AGENT-2026、S-SP-BOE-2025-RULES、S-SP-OMIE-PUBFILES-2025）；
- ENTSO-E，EIC编码体系、EDI/CIM交换规范及mRID说明（S-ENTSOE-EIC-2026、S-ENTSOE-EDI-2024、S-ENTSOE-MRID-2024）。

访问日期、发布日期/生效日、URL、页码/网页定位和适用性说明均在 `sources.md` 的相应source block中记录。
