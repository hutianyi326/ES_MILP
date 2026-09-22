# 西班牙现货—调频耦合报告重写任务

## 前置审核结论

`project/review_ES_SP_BASELINE_FULL_2026-09-04.md` 首轮完整审核结论为 CONDITIONAL（P0=0、P1=2、P2=3）。现有基线结构基本正确，但必须补齐 regulator-side aFRR 计算链、PTR 版本切片和术语解释后复审。

## 目标文件与权限

主文件：`countries/ES/spain_spot_market_research.md`。  
必要时同步：`countries/ES/spot_frequency_coupling.md`、`countries/ES/sources.md`、`countries/ES/spot_open_questions.md`。  
不得修改 `model/`、`src/`、`tests/`、`outputs/`、`data/raw/` 或 `project/country_status.yaml` 的建模门禁字段。你不是唯一修改者，请保留其他代理和主线程的改动，不要回滚。

## 写作对象与风格

- 面向具备电力基础知识、但不熟悉西班牙缩写的读者；
- 语言采用引用对话的“先给结论—再拆层次—用小例子解释—最后说明边界”风格；
- 每个缩写第一次出现时给出中文和西班牙语/英文全称；`UP`（Unidad de Programación）与 `Up`（a subir）必须显式区分；
- 保留必要的专业性、公式和单位，但避免连续堆叠缩写；每个公式旁边解释变量含义和适用层级；
- 规则事实（F）、研究解释（I）、建模假设（A）、待确认（U）必须分开，不能把例子或推断写成法规。

## 必须补入和核验的内容

1. **现货→调频运行链**：日前/日内成交和最终计划形成 PTR（基准计划），BSP/调度侧形成 PGC（AGC 控制中的实际聚合功率），aFRR capacity（每 QH、Up/Down 独立）与 aFRR energy（€/MWh）分层，激活后进入实时限值、遥测和结算。说明容量 €/MW 与能量 €/MWh 不同。
2. **aFRR capacity 报价**：2025 历史期按 15 分钟周期；同一 QH 可分别报 Up/Down，不要求对称；每方向/每 QH 最多 25 个 volume-price blocks，最多一个不可分块；容量按方向独立边际容量价格结算。明确“25 段是报价曲线表达能力，不是 25 个不同结算价格”，并与能量报价的 25 段分开。
3. **负消费遥测规则**：按 P.O.7.2 Annex III §8.1 写清：在 aFRR 交付/响应的 `Pout` 计算中，负的储能遥测（充电/消费模式）只有在对应消费模式 UP 已取得相应服务资格时才纳入；这不是“所有负电量都不结算”，也不证明纯独立 BESS 已获 aFRR 资格。
4. **实时 reserve 公式**：核验并解释：

   ```text
   RESAUP_b(t) = PGCSUP_b(t) - PGC_b(t)
   RESADW_b(t) = PGC_b(t) - PGCINF_b(t)
   ```

   说明 `LIMSUP/LIMINF` 是 BSP/provider 发送的上下限，`CLIMSUP/CLIMINF` 是系统侧计算限值，`PGCSUP/PGCINF` 是经过一致性处理后用于 RESA 的限值；不要把 `LIMINF` 直接写成 SOC 公式。
5. **激活后剩余 offer**：核验并给出 `REOFUP/REOFDW`、`REMOFUP/REMOFDW` 的分段逻辑，以及最终 `min(RESA, REMOF)` 的含义。用一个小表解释正负 `PaFRR` 激活如何消耗一方向、释放/转移另一方向的剩余 offer。明确这是 OS/regulator-side margin，不是项目可自由新增订单。
6. **150 MW 算术示例**：用 `PGC=+50 MW`、`PGCINF=-100 MW` 展示 `RESADW=150 MW`，并醒目标注这是 provider-level 的符号算术示例，不是单个电池 150 MW 充电功率或已获 150 MW 资格。SOC=100% 时只能通过项目实时可达限值、消费模式 UP 资格、能量/功率约束和 OS 验证确定 `PGCINF/LIMINF`；没有统一公开 SOC→LIMINF 公式。
7. **三层上限**：区分 (a) capacity market 的 habilitated/awarded reserve commitment；(b) 实时物理 `RESAUP/RESADW`；(c) 扣除已激活后的 `REMOF` 和最终可继续激活的 `min(RESA, REMOF)`。100 MW 条件若出现，必须注明来源和是 BSP/产品门槛还是单站功率，不得混淆。
8. **PTR 版本切片**：在 `sources.md` 新增并在主报告时间线引用 BOE-A-2025-21198、BOE-A-2025-23407、BOE-A-2025-27212、BOE-A-2026-1377；说明 2025-10 至 2026-01 临时 PTR 跟踪措施及 2026-01-19/20 终止/扩展边界。已有 `S-SP-BOE-2026-17285` 继续标为 2026-08-07 发布、实际 application date open，不能回填 2025。
9. **术语表和流程图**：新增同屏警示：`UP`≠`Up`，`PTR`≠`PGC`，capacity（€/MW）≠ energy（€/MWh），充电/放电到 Up/Down 的映射是解释层，SOC/持续时长/补能/恢复/资格仍是 U/open-critical。
10. **报告边界**：可以详细解释运行逻辑和算术例子，但不得新增项目级策略、收益预测、MILP、代码、回测或预测；不得因公式存在而关闭 FCR/SRAD、SOC 或项目级代码未决项。

## 证据与版本要求

- 优先 CNMC/BOE、REE、OMIE、ENTSO-E、ACER、MITECO 第一方来源；每条关键规则记录 `S-*` source ID、条款/页码/HTML 定位、发布日期/生效关系和 2025 适用性。
- `S-CNMC-2024-11535-PO` source block 必须列出 P.O.7.2 Annex I §§1.1–1.2、Annex II §§1–5、Annex III §§8.1–8.2、9.1–9.3 的精确定位；不得写“公式在另一个文件”而不提供链接。
- 2025 历史期、2026-08-11 规则基准日及之后的 2026 规则/计划必须分层；未来版本不能倒填历史。

## 交付与检查

- 重写后先由主线程检查章节结构、公式、source ID、版本边界、F/I/A/U 和范围门禁；
- 主线程检查通过后提交 review agent 二轮审核；P0/P1/P2 未清零则继续修订，直到 PASS；
- 仅在 review agent PASS 后才关闭本更新任务，`modeling_approved=false` 继续保持。

## 完成记录（2026-09-04）

- 首轮基线完整审查：CONDITIONAL（P0=0、P1=2、P2=3），整改项已全部纳入重写。
- `market_researcher` 以 `gpt-5.6-sol` / high 推理完成主报告重写，并同步耦合支撑文件和来源登记。
- 重写首轮 review：CONDITIONAL（P0=0、P1=0、P2=1）；已修正 P.O.7.2 实时履约分类的章节定位（正文 §9.3.1–9.3.4 与 Annex III §9.3 分离）。
- 二次独立 review：PASS（P0=0、P1=0、P2=0）。审查记录：`project/review_ES_SP_COUPLING_REWRITE_SECOND_FINAL_2026-09-04.md`。
- 任务关闭；未修改模型、代码、测试、输出或原始数据，`modeling_approved=false` 保持。
