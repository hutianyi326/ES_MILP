# 西班牙完整期数据采集任务 ES-DATA-02

## 1. 范围

- 交付日期：2025-07-01 至 2026-07-31，含首尾日期，共 13 个自然月。
- 工作目录：`C:\Users\Tianyi\OneDrive\融和元储工作\模型等其他参考资料\Python\Counry_Investigation`。
- 本任务沿用 ES-DATA-01 已审核的数据源、字段和安全门禁。

## 2. 本轮执行

1. 下载并清洗无需凭据的 OMIE DA、IDA1、IDA2、IDA3、IDC。
2. 原始响应保存到 `data/raw/ES/omie/<YYYY-MM>/<retrieval_batch>/`，同名响应不可覆盖。
3. 标准化结果保存到 `data/processed/ES/`，保留交付日、原始 period、本地时间、UTC、offset、DST fold、原始粒度和 EUR/MWh 西班牙区价格。
4. DA 在 2025-10-01 前保留小时粒度，自 2025-10-01 起使用原生 15 分钟；IDA/IDC 在本任务范围内按官方原始 15 分钟 period 处理。
5. 官方空业务文件、HTTP 失败或解析失败只登记，不插值、不补造价格。

## 3. 凭据门禁

- eSIOS 的 aFRR、不平衡、负荷和 P48 数据需要个人 `ESIOS_API_KEY`；缺失时跳过，不能伪造成功。
- ENTSO-E A75 按技术实际出力需要个人 `ENTSOE_API_KEY`；缺失时跳过。
- REData 当前小时级 `estructura-generacion` 已在 ES-DATA-01 验证为 HTTP 400，不用日值推导小时 MW。

## 4. 验收

- 逐来源、产品、月份统计请求数、成功、空业务文件、失败和解析记录数。
- 检查价格空值、UTC 空值、复合键重复、period 范围以及制度断点两侧的粒度。
- 保存质量报告；列出所有缺口和仍需凭据的项目。
