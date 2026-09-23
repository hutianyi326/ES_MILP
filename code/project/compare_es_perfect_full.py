"""Compare the current full P0 run to the archived original-model result."""
import csv
import json
import mmap
from collections import defaultdict
from datetime import datetime
from zoneinfo import ZoneInfo
from pathlib import Path
from html import escape

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'output/perfect_v1_full_completed_retry'
OUT=ROOT/'reports/perfect_v1_vs_v0'
SERIES={'DA':'DA','ID':'IDA','cap_up':'aFRR_capacity_up','cap_down':'aFRR_capacity_down',
        'act_up':'aFRR_activation_up','act_down':'aFRR_activation_down'}
LABELS=['DA','ID','aFRR容量上调','aFRR容量下调','aFRR激活上调','aFRR激活下调']

def common_coverage():
    from build_es_full_result_analysis_20260921 import RESULT
    def iter_pretty_array(mm,marker):
        marker_pos=mm.find(marker.encode());assert marker_pos>=0
        cursor=mm.find(b'[',marker_pos)+1
        while True:
            while mm[cursor:cursor+1] in (b' ',b'\n',b'\r',b'\t',b','):cursor+=1
            if mm[cursor:cursor+1]==b']':return
            assert mm[cursor:cursor+1]==b'{'
            indent=mm[mm.rfind(b'\n',0,cursor)+1:cursor]
            ending=b'\n'+indent+b'}';end=mm.find(ending,cursor)+len(ending)
            assert end>cursor
            yield json.loads(mm[cursor:end]);cursor=end
    old=defaultdict(lambda:{k:0. for k in SERIES})
    with RESULT.open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        for r in iter_pretty_array(mm,'"cash_ledger"'):
            typ=r['settlement_type'];energy=typ in ('DA_energy','IDA_energy')
            qid=json.loads(r['object_id'])[1] if energy else r['object_id']
            key=('DA' if typ=='DA_energy' else 'ID') if energy else ('cap_' if typ=='aFRR_capacity' else 'act_')+r['direction']
            old[qid][key]+=r['cash_eur']
    rows=[];totals=defaultdict(lambda:{'qh':0,'V0':0.,'V1':0.});efc=defaultdict(float);count=0;cash=0.
    monthly_efc=defaultdict(float);budget_hits={}
    s=json.loads((RUN/'summary.json').read_text(encoding='utf-8'))
    with (RUN/'result.json').open('rb') as f, mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as mm:
        for r in iter_pretty_array(mm,'"rows"'):
            count+=1;last=r
            year=datetime.fromisoformat(r['time']).astimezone(ZoneInfo('Europe/Madrid')).year
            efc[str(year)]+=r['efc'] or 0.
            local=datetime.fromisoformat(r['time']).astimezone(ZoneInfo('Europe/Madrid'))
            monthly_efc[local.strftime('%Y-%m')]+=r['efc'] or 0.
            threshold=s['annual_budget'][str(year)]-(180/(.92*360) if year==2026 else 0)-1e-6
            if efc[str(year)]>=threshold-1e-7 and str(year) not in budget_hits:budget_hits[str(year)]=local.isoformat()
            cash+=sum(r['cash'].values()) if r['cash'] is not None else 0.
            if r['cash'] is None or r['qh_id'] not in old:continue
            month=datetime.fromisoformat(r['time']).astimezone(ZoneInfo('Europe/Madrid')).strftime('%Y-%m')
            t=totals[month];t['qh']+=1;t['V0']+=sum(old[r['qh_id']].values())/100000;t['V1']+=sum(r['cash'].values())/100000
    for m,t in sorted(totals.items()):rows.append(dict(month=m,common_qh=t['qh'],V0_kEUR_per_MW=t['V0'],V1_kEUR_per_MW=t['V1'],delta_kEUR_per_MW=t['V1']-t['V0']))
    write_csv('common_qh_monthly.csv',rows)
    write_csv('monthly_efc.csv',[dict(month=k,executed_efc=v) for k,v in sorted(monthly_efc.items())])
    s=json.loads((RUN/'summary.json').read_text(encoding='utf-8'))
    assert count==58364 and abs(last['soc']-10)<1e-5
    for y,v in s['annual_used'].items():
        assert abs(efc[y]-v)<1e-5 and v<=s['annual_budget'][y]+1e-5
    assert abs(cash-sum(sum(m['cash_eur'].values()) for m in s['months'].values()))<1e-4
    logs=[]
    all_logs='\n'.join((ROOT/'reports'/name).read_text(encoding='utf-8-sig') for name in ('perfect_v1_full_run.log','perfect_v1_full_resumed.log'))
    for line in all_logs.splitlines():
        if line.startswith('{'):
            obj=json.loads(line)
            if 'window' in obj:logs.append(obj)
    assert len(logs)==608 and logs[-1]['window']==608
    assert abs(sum(r['solver_seconds'] for r in logs)-s['solver_seconds'])<1e-6
    start=json.loads((RUN/'process_start.json').read_text(encoding='utf-8-sig'))
    wall=(RUN/'summary.json').stat().st_mtime-datetime.fromisoformat(start['start_utc']).timestamp()
    first=ROOT/'output/perfect_v1_full_20260922'
    first_start=json.loads((first/'process_start.json').read_text(encoding='utf-8-sig'))
    wall+=(first/'summary.json').stat().st_mtime-datetime.fromisoformat(first_start['start_utc']).timestamp()
    checks=dict(formal_qh=count,windows=len(logs),final_soc_mwh=last['soc'],annual_efc_from_operations=dict(efc),
        first_operating_efc_limit_reached_local=budget_hits,
        pure_solver_seconds=s['solver_seconds'],process_to_summary_saved_seconds=wall,
        checks='PASS: endpoint, budget, cash, monthly totals and solver timings')
    (OUT/'validation.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    return dict(common_qh=sum(t['qh'] for t in totals.values()),V0=sum(t['V0'] for t in totals.values()),V1=sum(t['V1'] for t in totals.values()))

def write_csv(name,rows):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def chart(name,title,months,old,new):
    width=1400;height=520;top=65;bottom=425;left=80
    hi=max(0,*old,*new)*1.12;lo=min(0,*old,*new)*1.12
    if hi==lo:hi=lo+1
    y=lambda v:bottom-(v-lo)/(hi-lo)*(bottom-top)
    parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
      '<rect width="100%" height="100%" fill="white"/>',
      '<style>text{font-family:Microsoft YaHei,Arial;fill:#263238;font-size:12px}</style>',
      f'<text x="80" y="28" style="font-size:21px">{escape(title)}（k€/MW）</text>',
      '<text x="950" y="28" fill="#64748b">V0 灰色</text><text x="1100" y="28" fill="#2563eb">V1 蓝色</text>']
    for i in range(6):
        v=lo+(hi-lo)*i/5; yy=y(v)
        parts +=[f'<path d="M80 {yy} H1370" stroke="#e2e8f0"/>',f'<text x="5" y="{yy+4}">{v:.2f}</text>']
    step=1290/len(months)
    for i,m in enumerate(months):
        x=left+i*step+step*.12
        for j,(vals,col) in enumerate(((old,'#64748b'),(new,'#2563eb'))):
            yy=y(vals[i]);zero=y(0)
            parts.append(f'<rect x="{x+j*step*.35}" y="{min(yy,zero)}" width="{step*.30}" height="{max(.1,abs(yy-zero))}" fill="{col}"><title>{m}: {vals[i]:.6f}</title></rect>')
        parts.append(f'<text transform="translate({x+8},445) rotate(45)">{m}</text>')
    parts.append('</svg>');(OUT/name).write_text('\n'.join(parts),encoding='utf-8')

def main():
    OUT.mkdir(exist_ok=True)
    s=json.loads((RUN/'summary.json').read_text(encoding='utf-8'))
    if not s['success']:raise RuntimeError('Incomplete run: '+str(s['failure']))
    old=json.loads((ROOT/'output/full_range/final_report.json').read_text(encoding='utf-8'))
    with (ROOT/'reports/monthly_revenue_breakdown.csv').open(encoding='utf-8-sig') as f:base={r['month']:r for r in csv.DictReader(f)}
    months=sorted(s['months']);assert months==sorted(base) and len(months)==20
    monthly=[];detail=[];tot0={k:0. for k in SERIES};tot1=dict(tot0)
    for m in months:
        a=base[m];b=s['months'][m];v=b['cash_keur_per_mw']
        if v is None:raise RuntimeError('No solved cash in '+m)
        x=sum(float(a[col+'_kEUR_per_MW']) for col in SERIES.values());z=sum(v.values())
        assert abs(x-float(a['gross_kEUR_per_MW']))<1e-7
        monthly.append(dict(month=m,V0_kEUR_per_MW=x,V1_kEUR_per_MW=z,delta_kEUR_per_MW=z-x,
            change_pct=(z/x-1)*100 if x else None,V0_valid_qh=int(a['covered_qh']),V1_valid_qh=b['valid_qh'],nominal_qh=b['total_qh']))
        for k,col in SERIES.items():
            av=float(a[col+'_kEUR_per_MW']);bv=v[k];tot0[k]+=av;tot1[k]+=bv
            detail.append(dict(month=m,market=k,V0_kEUR_per_MW=av,V1_kEUR_per_MW=bv,delta_kEUR_per_MW=bv-av,
                V0_share_pct=100*av/x if x else None,V1_share_pct=100*bv/z if z else None))
    a=sum(tot0.values());b=sum(tot1.values());assert abs(a-old['gross_eur']/100000)<1e-7
    assert s['quality']['blocked_qh']==0
    write_csv('monthly_total.csv',monthly);write_csv('monthly_market.csv',detail)
    total=[dict(market=k,V0_kEUR_per_MW=tot0[k],V1_kEUR_per_MW=tot1[k],delta_kEUR_per_MW=tot1[k]-tot0[k]) for k in SERIES]
    total.append(dict(market='total',V0_kEUR_per_MW=a,V1_kEUR_per_MW=b,delta_kEUR_per_MW=b-a))
    write_csv('total_market.csv',total)
    common=common_coverage()
    checks=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
    chart('monthly_total.svg','月度总收益对比',months,[r['V0_kEUR_per_MW'] for r in monthly],[r['V1_kEUR_per_MW'] for r in monthly])
    lines=['# 西班牙100 MW / 200 MWh：完美预测V1与V0全量对比','',
        '正式区间：马德里当地2025-01-01至2026-08-31，共20个月。V1另加载2026-09-01观察日，观察日现金不计入正式收益。',
        '观察日2026-09-01的本地归档价格与激活字段全部缺失，96个QH以空值留证并禁用交易，不构成经济上有效的前瞻；正式终点SOC=10 MWh仍强制执行。',
        'V0指优化前原模型的成功全量归档（历史执行文件名为v5，v1–v4为失败尝试编号），不是另一个未经确认的基准。V1在当前“完美预测模型优化V1”分支运行。','',
        '## 配置与比较口径','',
        '额定功率100 MW、额定容量200 MWh；可用SOC 10–190 MWh，初始及正式终点10 MWh，充放电效率各92%。两日规划、逐日执行，ts_start / cap_old / D（先下后上），MIP gap=1e-4、30秒/窗、presolve=False。',
        f"正式年度EFC预算与原结果一致：{s['annual_budget']}；V1实际消耗：{s['annual_used']}。",
        f"V1首次达到常规可用EFC上限的当地时段：{checks['first_operating_efc_limit_reached_local']}。2025口径为年度预算减数值余量；2026口径另扣正式终点预留0.543478 EFC，终点窗口释放。月度消耗见monthly_efc.csv。",
        '使用既有REE/eSIOS及OMIE本地原始归档，没有新增下载或市场规则核验。价格及激活系数为事后已知，全额成交、GCT起检查备用余量及空闲桥接属于建模假设；cap_old历史时表仍待核实。收益为不扣手续费和退化现金的条件毛收益，不等于可实现收益，也不是全年联合优化的严格上界。',
        'V1保留连续时间轴并对缺失时段空闲桥接，V0按有效片段重置状态；冻结、GCT余量与终点约束也存在差异。下列为各自完整运行结果对比，不把覆盖差异或约束变化全部归因为性能优化。缺失结算留空，不作为观测到的零收益。','',
        f"补充共同结算时段比较：{common['common_qh']}个QH，V0 {common['V0']:.6f}、V1 {common['V1']:.6f} k€/MW，差额{common['V1']-common['V0']:+.6f} k€/MW。此为各自原调度结果在交集上的现金筛选，并非在共同输入上重新优化；月度见common_qh_monthly.csv。",'',
        '## 总收益与用时','',
        '| 指标 | V0 | V1 | 差异 |','|---|---:|---:|---:|',
        f'| 总收益（k€/MW） | {a:.6f} | {b:.6f} | {b-a:+.6f}（{(b/a-1)*100:+.2f}%） |',
        f"| 有效结算QH | {old['coverage']['common_valid_qh']} | {sum(m['valid_qh'] for m in s['months'].values())} | |",
        f"| 覆盖率 | {old['coverage']['coverage_percent']:.3f}% | {s['coverage']*100:.3f}% | |",
        f"| 纯求解器时间（秒） | {old['solver']['pure_solver_seconds']:.3f} | {s['solver_seconds']:.3f} | |",
        f"| 执行墙钟时间（秒） | {old['solver']['economic_trial_wall_seconds']:.3f} | {s['execution_wall_seconds']:.3f} | |",
        f"| 入口记录总时间（秒） | {old['solver']['total_wall_seconds']:.3f} | {s['total_wall_seconds']:.3f} | |",'',
        f"V1首轮生产运行与成功续跑的进程耗时合计约{checks['process_to_summary_saved_seconds']:.3f}秒（含最终文件写出，由两段进程启动记录和文件修改时间计算；不含中间诊断、首次续跑入口失败及人工处理间隔）。",'',
        f"V1数值重试共{s['retry_count']}次：默认presolve=False，仅当求解器报告不可行时以presolve=True重试，数学约束、预算和冻结订单不变。首轮在2025-11-22停止，恢复前325个已验收窗口继续。诊断放宽预算试验未用于正式结果。",
        'V0计时来自原运行，并非本次同步基准测试。V1求解计时为首轮325个成功窗口加恢复运行全部求解尝试；首轮失败调用的求解时间未单独保存，诊断重放不计入，因此不是所有尝试总CPU时间。执行墙钟为首轮与续跑相加，包含审计、首轮每60窗检查点及报告物化。入口总时间在最终结果序列化前采样。',
        '所有收益单位均为k€/MW；对100 MW项目，对应项目收益（千欧元）为表内数值乘100。','',
        '| 市场 | V0 | V1 | V1−V0 |','|---|---:|---:|---:|']
    for (k,_),label in zip(SERIES.items(),LABELS):lines.append(f'| {label} | {tot0[k]:.6f} | {tot1[k]:.6f} | {tot1[k]-tot0[k]:+.6f} |')
    lines+=['','## 月度总收益','','![月度收益](monthly_total.svg)','','| 月份 | V0 | V1 | 差额 | 变化 | V0/V1有效QH |','|---|---:|---:|---:|---:|---:|']
    for r in monthly:lines.append(f"| {r['month']} | {r['V0_kEUR_per_MW']:.4f} | {r['V1_kEUR_per_MW']:.4f} | {r['delta_kEUR_per_MW']:+.4f} | {r['change_pct']:+.2f}% | {r['V0_valid_qh']}/{r['V1_valid_qh']} |")
    lines+=['','收益下降集中在2025年12月与2026年8月；V1在此之前已用尽大部分常规EFC额度，后期物理充放电受到预算限制。两日滚动并不预留全年最高价月份的用量，因此完美价格信息不等于全年最优调度。该解释与EFC记录一致，但本次没有逐项关闭约束进行因果归因。',
        f"DA与ID合计变化为{tot1['DA']+tot1['ID']-tot0['DA']-tot0['ID']:+.6f} k€/MW；应合并观察现货收益，不能仅凭DA单项上升判断收益提升。"]
    lines+=['','## 月度分项收益','']
    for (k,_),label in zip(SERIES.items(),LABELS):
        rows=[r for r in detail if r['market']==k];chart(k+'.svg',label,months,[r['V0_kEUR_per_MW'] for r in rows],[r['V1_kEUR_per_MW'] for r in rows])
        lines +=[f'### {label}','',f'![{label}]({k}.svg)','','| 月份 | V0 | V1 | 差额 | V0收益占比 | V1收益占比 |','|---|---:|---:|---:|---:|---:|']
        for r in rows:lines.append(f"| {r['month']} | {r['V0_kEUR_per_MW']:.4f} | {r['V1_kEUR_per_MW']:.4f} | {r['delta_kEUR_per_MW']:+.4f} | {r['V0_share_pct']:.2f}% | {r['V1_share_pct']:.2f}% |")
        lines.append('')
    lines+=['## 数据质量与验收','',f"```json\n{json.dumps(s['quality'],ensure_ascii=False,indent=2)}\n```",'',
        '已检查20个月齐全、月度六项加总与总收益一致、V0月度CSV与原总收益一致、V1成功结束且没有未知状态阻断。逐窗物理约束、冻结还原和现金重构由现有独立验收逻辑在提交窗口前检查。本次没有调用任何agent。',
        '完整运行证据见 ../../output/perfect_v1_full_completed_retry/；首轮失败与诊断现场保留在相邻目录；比较数据见本目录CSV文件。']
    (OUT/'结果对比.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    result=dict(V0_kEUR_per_MW=a,V1_kEUR_per_MW=b,delta_kEUR_per_MW=b-a,change_pct=(b/a-1)*100,solver_seconds=s['solver_seconds'],quality=s['quality'])
    (OUT/'comparison_summary.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
