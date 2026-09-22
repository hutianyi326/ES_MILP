# 西班牙补充研究 SUP-04 任务说明：项目级账户和代码映射

## 任务状态

- 状态：进行中（2026-09-03）
- 前置门禁：SUP-03 已经独立复审 PASS（P0=0、P1=0、P2=0）
- 研究对象：西班牙大陆竞价区独立非水电化学储能
- 历史期：2025-01-01—2025-12-31
- 规则基准日：2026-08-11；2026-08-11 后信息不得倒填至历史期

## 研究问题

围绕一个独立储能项目从注册、计划、交易、激活到计量/结算的项目级身份链，核验下列对象和映射关系：

1. UO、UP、UF 在西班牙系统运行和市场流程中的定义、层级、职责及适用边界；
2. PM、BSP、BRP（及必要时的代表/市场代理）在独立储能参与现货和辅助服务中的角色边界；
3. EIC、mRID、CUPS/计量点、技术单元/设施代码、控制区域或组合标识的官方定义和 crosswalk；
4. 报价、激活、计划、测量、偏差和结算文件中使用的标识如何连接；
5. 哪些字段/代码可以由公开官方资料确认，哪些需从 REE/OMIE 注册或项目合同获取。

## 来源要求

优先使用 REE、OMIE、CNMC、BOE、ENTSO-E、ACER 的官方规则、接口、数据字典、注册指南和 API 文档。每项关键 claim 必须记录来源机构、标题、发布日期/生效日期、URL、访问日期和条款/页码/API 定位，并在 `countries/ES/sources.md` 建立唯一 `S-*` source ID。

## 交付边界

- 只交付规则事实（F）、研究解释（I）、建模假设（A）和待确认事项（U）的分层研究文件；
- 更新 `countries/ES/spot_open_questions.md`，为未确认的项目级字段保留 open/open-critical 标记；
- 不下载或生成项目数据，不编写策略、收益测算、MILP、代码、回测或预测；
- 不修改 `model/`、`src/`、`tests/`、`outputs/` 或 `data/raw/`；
- 不把注册/接口中可能存在的字段推定为 2025 已适用规则；如适用性无法确认，明确标记为 U。

## 预期交付物

- `countries/ES/supplemental_account_code_crosswalk.md`
- `countries/ES/sources.md`（新增或修订 SUP-04 来源块）
- `countries/ES/spot_open_questions.md`（新增 SUP-04 问题）

完成后由主线程进行范围、证据 ID、版本边界和 F/I/A/U 检查，再提交独立 review agent；未 PASS 前不得启动 SUP-05。
