# 西班牙两版回测：环境与算术检查

日期2026-09-20。仅为实施前检查，不是完整模型或历史数据验收。

## 环境变化

项目隔离环境 `.venv-es-milp` 原来缺少IANA时区数据库；`ZoneInfo('Europe/Madrid')` 实测失败。普通权限下载因网络权限失败，随后经正常升级审批安装 `tzdata==2026.4` 成功。未修改应用捆绑Python依赖。已记录基础依赖于 `spain_sandbox_requirements_20260920.txt`：Python3.12.14、numpy2.4.6、scipy1.15.3、tzdata2026.4；这不是完整生产依赖清单，正式运行仍须完整manifest/hash。

## 检查结果

|检查|结果|
|---|---|
|既有合成电池＋双顺序诊断|17项测试PASS；不包含完整市场账本|
|ZoneInfo加载Madrid|安装后PASS|
|2025-03-30 / 2025-10-26|UTC实际日长23 / 25小时，PASS|
|2026-03-29 / 2026-10-25|UTC实际日长23 / 25小时，PASS；后者仅时区测试，非纳入收益期|
|2026-08-31|24小时，PASS|
|目标期Madrid 2025-01-01至2026-09-01右开|UTC 2024-12-31 23:00至2026-08-31 22:00，共58,364个15分钟时段|
|600×243/365|399.45205479452056 EFC，PASS|
|600×100/365|164.3835616438356 EFC，算术检查|
|40MWh×0.92×100€/MWh|3,680€窗口估值，PASS；不属于实际现金收入|

回归命令：

```powershell
.venv-es-milp/Scripts/python.exe -B -m unittest -v tests.test_es_order_diagnostic tests.test_es_milp_sandbox
```

DST检查使用Python标准库datetime、zoneinfo和已安装tzdata，从相邻Madrid当地午夜对应的UTC时间戳计算实际小时差；不直接用同一时区的日历timedelta当实际小时差。目标季度数亦从UTC时间戳差除以900计算。

本轮无新增电力市场规则来源。时区和循环算术属于工程检查；设备、预算及末端估值仍是已确认项目假设。真实历史输入、市场事件和现金账本测试尚未运行。
