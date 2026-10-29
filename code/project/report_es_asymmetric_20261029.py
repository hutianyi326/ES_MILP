"""Render the audited common-QH comparison into a compact Chinese report."""
import csv
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/asymmetric_50_100_20261029'
NAMES=('baseline_100_100','asymmetric_cap100','asymmetric_cap150')
LABELS=('原场景：充100 MW／放100 MW，上下调上限各100 MW',
        '主场景：充50 MW／放100 MW，上下调上限各100 MW',
        '理论敏感性：充50 MW／放100 MW，上下调上限各150 MW')
KEYS=('DA','ID','cap_up','cap_down','act_up','act_down')
ZH=('日前 DA','日内 ID','aFRR 容量上调','aFRR 容量下调','aFRR 激活上调','aFRR 激活下调')

def main():
    e=json.loads((OUT/'comparison_evidence.json').read_text(encoding='utf-8'))
    rows=list(csv.DictReader((OUT/'monthly_common_qh.csv').open(encoding='utf-8-sig',newline='')))
    totals={n:sum(e['common_cash_keur_per_mw'][n].values()) for n in NAMES}
    lines=['# 西班牙储能充电 50 MW／放电 100 MW：全量测算比较',
           '', '## 结论与比较口径', '',
           f"正式交付区间：马德里当地 2025-01-01 至 2026-08-31；三场景共同有效 {e['common_valid_qh']:,} 个 15 分钟时段，数据缺口未补算。",
           '收益按三场景统一的 100 MW 放电额定功率折算。kEUR/MW 表示千欧元／MW，1 kEUR/MW = 1,000 欧元／MW；不是电价单位欧元／MWh。',
           '总收益及六项市场现金流均为上述 20 个月内共同有效时段的累计条件市场现金毛收益；月度表为各月共同有效时段累计值，均未年化。负现金流表示该市场项的净支出。',
           '本报告 MW 表示充电、放电或备用申报功率；MWh 表示电量或电池容量；EFC 表示等效完整循环次数。所有金额币种均为欧元。', '',
           '| 场景 | 全期单位功率收益（千欧元／MW） | 全期电站总收益（万欧元） | 较原场景差额（千欧元／MW） | 较原场景变化（%） |', '|---|---:|---:|---:|---:|']
    for n,label in zip(NAMES,LABELS):
        delta=totals[n]-totals[NAMES[0]]
        lines.append(f'| {label} | {totals[n]:.2f} | {totals[n]*10:,.2f} | {delta:+.2f} | {delta/totals[NAMES[0]]*100:+.2f}% |')
    lines+=['', '电站总收益（万欧元）= 单位功率收益（千欧元／MW）× 100 MW ÷ 10。例如原场景约 593.05 千欧元／MW，对应整站约 5,930.54 万欧元。各列均由未舍入原始值计算后展示。',
            '', '## 年度实际 EFC 使用', '',
            '单位：次（EFC，等效完整循环）。2025 年为 1–12 月累计，2026 年仅为 1–8 月统计期累计，均按有效时段统计。EFC = 电池侧累计充入与放出电量之和 ÷ 360 MWh，其中 360 MWh = 2 × (190 − 10) MWh；在 SOC 10–190 MWh 区间完成一次完整充放电计 1 EFC。', '',
            '| 场景 | 2025 年1–12月使用量（次 EFC） | 2026 年1–8月使用量（次 EFC） |', '|---|---:|---:|']
    for n,label in zip(NAMES,LABELS):
        lines.append(f"| {label} | {e['annual_used'][n]['2025']:.3f} | {e['annual_used'][n]['2026']:.3f} |")
    lines+=['', '理论敏感性场景在 2025-07-27 和 2026-05-05 已分别使用当期年度 EFC 额度的 99%；主场景对应日期为 2025-10-19 和 2026-07-01。该差异与 150 MW 场景后续月收益偏低一致，但这里没有通过单独约束剥离实验证明全部差额的因果来源。两日滚动不是全期联合优化，放宽上限后不能保证实际滚动路径全期收益单调提高。详见 [月度 EFC](monthly_efc.csv) 和 [日期证据](efc_99_percent_dates.json)。']
    lines+=['','## 六项市场现金流','',
            '统计口径：2025-01-01 至 2026-08-31 共同有效时段累计；各列单位为千欧元／MW，分母均为 100 MW 放电额定功率。容量收入也已按时间累计为金额，表中不是容量报价。', '',
            '| 市场 | 原场景（千欧元／MW） | 主场景（千欧元／MW） | 理论敏感性（千欧元／MW） |','|---|---:|---:|---:|']
    for key,label in zip(KEYS,ZH):
        values=[e['common_cash_keur_per_mw'][n][key] for n in NAMES]
        lines.append(f'| {label} | {values[0]:.2f} | {values[1]:.2f} | {values[2]:.2f} |')
    lines+=['','## 月度比较','',
            '收益为各月共同有效时段的六项市场现金流合计，单位为千欧元／MW，未年化。QH 是一个 15 分钟时段；QH 列计数单位为个，不是小时。', '',
            '| 月份 | 共同有效15分钟时段（个） | 原场景（千欧元／MW） | 主场景（千欧元／MW） | 理论敏感性（千欧元／MW） |','|---|---:|---:|---:|---:|']
    for month in sorted({r['month'] for r in rows}):
        part={r['scenario']:r for r in rows if r['month']==month}
        vals=[float(part[n]['total_keur_per_mw']) for n in NAMES]
        lines.append(f"| {month} | {part[NAMES[0]]['valid_qh']} | {vals[0]:.2f} | {vals[1]:.2f} | {vals[2]:.2f} |")
    lines+=['','## 已确认边界与解释','',
            '- 新场景电池总容量 200 MWh，SOC 10–190 MWh；初始和终点 SOC 均为 10 MWh。充放效率均为 92%。',
            '- 新场景并网进口／出口上限 50／100 MW；原场景为 100／100 MW。三场景放电功率均为 100 MW。',
            '- 上／下备用名义上限各为 100 MW 或 150 MW，实际每时段受净基准出力和并网限制；150 MW 跨零调节的项目资格、设备切换和持续响应能力尚未验证。',
            '- 事后已知价格及激活、两日规划逐日执行，ts_start／cap_old／D；仅按逐时段系统分配比例代理折减容量收入，激活收益和完整备用物理承诺沿用原模型。',
            '- EFC 预算分别为 2025 年 548.7661703395 次 EFC、2026 年统计期 345.9916617034 次 EFC，计算分母为 360 MWh；包含循环限额，不包含退化现金、交易费用、税费、投资或运维。',
            '- 历史代理系数并非单站中标率，报价曲线地域匹配及 cap_old 历史切换日期待确认。模型不证明持续满额激活履约，也不证明两日滚动为全时域全局上界。',
            '- REE/eSIOS、OMIE 本地官方数据沿用既有归档；本次没有修改或新增市场规则。规则与建模假设的详细来源见 [研究记录](../../research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)。',
            '', '## 验证与文件', '',
            f"- 三场景原始输入证据 SHA-256 相同：`{e['input_evidence_sha256'][NAMES[0]]}`；有效时段集合是否完全一致：{e['all_valid_sets_equal']}。",
            '- 每个日窗口经过现有独立约束和现金重构审计；数值重试与源检查点保存在运行目录。',
            '- 两个新场景各成功完成 608 个窗口；按运行结果中的求解器标记，各 608 个窗口均达到设定 gap 的最优状态。主场景 1 次、150 MW 场景 2 次采用 presolve 重试，重试保持相同物理约束、预算和审计标准；原失败现场未覆盖。',
            '- 非对称充放电、150 MW 跨零、冻结备用、容量系数和原核心回归共 39 项测试通过；三场景逐月六项现金合计与各自摘要核对通过。',
            '- [月度六市场明细](monthly_common_qh.csv)、[对比证据与配置](comparison_evidence.json)。',
            '- 本次计算使用已有官方数据和规则研究；所有收益均属假设下的事后条件测算。','']
    (OUT/'测算对比报告.md').write_text('\n'.join(lines),encoding='utf-8')
    print(OUT/'测算对比报告.md')

if __name__=='__main__':main()
