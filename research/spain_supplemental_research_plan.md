# 西班牙独立储能补充研究计划

## 目的

对现货与辅助服务基线中仍为 `open/open-critical` 的事项进行证据闭合。每一步必须由主线程检查后提交独立 review agent；若不通过，先修订并复审，不得进入下一步。

## 研究对象与基准

- 对象：西班牙大陆竞价区独立非水电化学储能；
- 历史期：2025-01-01—2025-12-31；
- 规则基准日：2026-08-11；
- 只使用 CNMC/BOE、REE、OMIE、MITECO、ENTSO-E、ACER 等第一方资料；
- 继续禁止策略、收益测算、MILP、代码、回测和预测模拟；`modeling_approved=false`。

## 顺序步骤

| 步骤 | 主题 | 主要问题 | 交付物 |
|---|---|---|---|
| SUP-01 | FCR/SRAD 资格与预认证 | 独立储能是否可参加、入口、产品、容量、测试、计量和现货接口 | `supplemental_fcr_srad_eligibility.md`（已 PASS） |
| SUP-02 | SOC、持续时长、补能与恢复 | 产品级能量要求、激活后补能/恢复、可用率和归责 | `supplemental_storage_energy_requirements.md`（已 PASS） |
| SUP-03 | 2026 RR 替代与 96 轮日内修订 | TERRE 后 RR 路径、96 轮连续日内 application date、历史适用性 | `supplemental_rr_2026_transition.md`（已 PASS） |
| SUP-04 | 项目级账户和代码映射 | UO/UP/UF、BSP/BRP/PM、EIC/mRID、计量点 crosswalk | `supplemental_account_code_crosswalk.md`（已 PASS） |
| SUP-05 | 数据接口补充核验 | API 指标、字段、DST、历史覆盖、修订和权限 | `supplemental_data_interface_validation.md`（已 PASS） |

## 阶段门禁

每一步必须：

1. 逐项区分规则事实、研究解释、建模假设和待确认事项；
2. 为关键 claim 记录机构、标题、发布日期/生效、URL、访问日和条款/页码/API 定位；
3. 更新 `countries/ES/sources.md` 与 `spot_open_questions.md`；
4. 由主线程做范围和证据检查；
5. 经 review agent PASS 后才启动下一步。

## 汇总报告门禁

SUP-01 至 SUP-05 全部 PASS 后，主线程形成 `countries/ES/spain_supplemental_research_report.md`，逐项复核来源、版本边界、F/I/A/U 分层和未决事项，再由独立 review agent 进行报告级终审。报告级终审已 PASS，本补充研究链关闭；`modeling_approved=false` 不因本报告自动改变。
