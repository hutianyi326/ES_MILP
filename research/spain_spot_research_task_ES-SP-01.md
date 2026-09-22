# ES-SP-01：西班牙现货市场制度、主体与市场架构

## 1. 任务状态

- 状态：已完成并通过独立 review agent；允许进入 ES-SP-02
- 基线：2025-01-01—2025-12-31；规则基准日 2026-08-11
- 对象：独立电化学储能；市场范围为西班牙日前/日内现货制度和直接接口
- 前置状态：ES-SP-00 范围冻结已完成；辅助服务研究 ES-GF 已通过
- 建模状态：`modeling_approved=false`

## 2. 研究目标

建立 OMIE/MIBEL、CNMC/BOE、REE、NEMO、SDAC、SIDC 及西班牙竞价区的主体、职责、平台关系和规则层级；仅记录与储能计划、BRP 和辅助服务直接相关的接口。

## 3. 明确排除

- 日前/日内具体订单、关门时间和价格参数（ES-SP-02/03）；
- 套利方式、交易策略和联合优化（ES-SP-05/06）；
- MILP、代码、原始数据、回测和预测模拟。

## 4. 交付物与门禁

- `countries/ES/spot_market_structure.md`；
- `countries/ES/spot_open_questions.md`；
- `countries/ES/sources.md` 的现货 source blocks。

完成后主线程先检查，再提交 review agent。二次复审已 PASS（P0=0，P1=0；P2 优化项已处理），允许进入 ES-SP-02。
