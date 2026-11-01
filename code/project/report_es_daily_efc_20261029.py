"""Independently audit daily execution and report the three Jan-Aug 2026 runs."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime, timedelta
import hashlib
import json
import mmap
from pathlib import Path
from zoneinfo import ZoneInfo

from build_es_result_presentation import _read_rows, _top_level_scalars
from compare_es_asymmetric_20261029 import FIELDS
from run_es_daily_efc_20261029 import SCENARIOS

TZ=ZoneInfo('Europe/Madrid')
KEYS=('DA','ID','cap_up','cap_down','act_up','act_down')
LABELS=('日前DA','日内ID','aFRR容量上调','aFRR容量下调','aFRR激活上调','aFRR激活下调')
NAMES={'baseline_100_100':'充100／放100 MW；aFRR上／下调各100 MW',
       'asymmetric_cap100':'充50／放100 MW；aFRR上／下调各100 MW',
       'asymmetric_cap150':'充50／放100 MW；aFRR上／下调各150 MW（理论）'}


def read_array(path,key):
    """Stream one known top-level array without loading the large whole JSON."""
    marker=('"'+key+'": [').encode()
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        at=data.find(marker)
        if at<0:raise ValueError(f'missing {key}')
    with path.open('r',encoding='utf-8') as f:
        # Seek using byte offset; the ASCII array marker ends on a UTF-8 boundary.
        f.seek(at+len(marker))
        decoder=json.JSONDecoder();buffer=''
        while True:
            buffer=buffer.lstrip(' \n\r\t,')
            if buffer.startswith(']'):return
            try:
                obj,end=decoder.raw_decode(buffer)
            except json.JSONDecodeError:
                chunk=f.read(1024*1024)
                if not chunk:raise
                buffer+=chunk
                continue
            yield obj
            buffer=buffer[end:]


def digest(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def brief_description(monthly_base):
    """Append the requested base-case assumptions and signed monthly shares."""
    lines=['## 测算简要说明','',
        '本节基础场景为：充电50 MW、放电100 MW，aFRR上调和下调申报上限各100 MW。以下金额及占比均对应这一基础场景。','',
        '### 重要边界假设','',
        '- **电池与并网边界：** 电池总容量200 MWh，SOC范围5%–95%（10–190 MWh），充、放电效率各92%；并网进口／出口上限分别为50／100 MW。aFRR实际可申报量还受基准出力、功率和SOC约束，并非每个时段都能上下调各申报100 MW。',
        '- **循环额度与起止状态：** 每个马德里自然日最多2次EFC，替代年度额度，未用额度不结转；EFC按电池侧充放电吞吐量合计除以360 MWh计算。2026年1月独立起算，期初和8月末SOC均为10 MWh，不承接2025年订单；起点前已关闭的交易按零初始承诺处理。',
        '- **时间与决策边界：** 统计2026年1—8月，按马德里时区及15分钟数据测算，采用事后已知价格和激活数据、两天规划逐日执行。9月1日仅用于前瞻，不计入收入。共同有效时段覆盖率86.88%，缺失时段不补收益，按零功率衔接SOC。本结果为条件测算，不代表真实事前可执行收益或全期联合最优值。',
        '- **aFRR容量中标方法（建模假设）：** 按每个15分钟时段、每个方向，以“系统实际已分配容量A ÷ 系统总报价容量O”计算代理系数，并以1封顶，即p=min(1,A/O)。容量收入按“申报MW × 对应时段容量价 × p”计入目标函数后重新优化；缺失或无有效分配的方向不新增容量申报。p是历史系统分配比例代理，不是本站经验证的中标概率；模型不模拟随机中标，物理备用承诺仍按完整申报MW保留。',
        '- **aFRR激活方法（建模假设）：** 分方向用历史系统激活电量除以“系统已分配容量 × 0.25小时”得到激活比例α，本站激活电量按“本站申报MW × α × 0.25小时”计算，并使用对应激活价格计现金流。激活电量和收入不再乘容量代理系数p。每个时段按先下调、后上调、剩余时间保持基准出力的简化路径推演SOC与EFC，不模拟实际逐秒AGC信号，也不构成连续满额激活履约证明。',
        '- **收益边界与来源：** 总收入为日前、日内、aFRR容量上下调及激活上下调六项有符号市场现金流之和，已体现购电支出，但未扣除退化现金、交易费、税费、投资和运维费用，未年化。官方数据沿用REE/eSIOS和OMIE归档；上述中标代理、激活路径及日循环额度属于建模假设，官方规则和待确认事项见本报告前文及[研究来源记录](../../research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)。','',
        '### 基础场景月度收入及市场收益占比','',
        '总收入单位为欧元；每MW收入单位为K欧元／MW（1 K欧元=1,000欧元），统一以100 MW放电功率为分母，即每MW收入=总收入÷100÷1,000。各市场占比=该市场当月有符号净现金流÷当月总收入×100%；负占比表示净支出，其他项可能超过100%。占比不取绝对值，显示值因四舍五入可能不恰好合计100%。合计行按全期金额计算占比，不对月度占比取平均。','',
        '| 月份 | 总收入（欧元） | 每MW收入（K欧元／MW，分母100 MW） | 日前DA占比（%） | 日内ID占比（%） | aFRR容量上调占比（%） | aFRR容量下调占比（%） | aFRR激活上调占比（%） | aFRR激活下调占比（%） |',
        '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    totals={k:sum(v['cash'][k] for v in monthly_base.values()) for k in KEYS}
    entries=[(m,monthly_base[m]['cash']) for m in sorted(monthly_base)]+[('2026年1—8月合计',totals)]
    for month,cash in entries:
        total=sum(cash[k] for k in KEYS)
        shares=[f'{cash[k]/total*100:.2f}%' if total else '不适用' for k in KEYS]
        lines.append(f'| {month} | {total:,.2f} | {total/100000:.2f} | '+' | '.join(shares)+' |')
    return lines+['']


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--input',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--baseline-run',type=Path,help='audited continuation directory for the symmetric baseline')
    args=p.parse_args();out=args.output
    if out.exists():raise FileExistsError(out)
    stats={};daily={};monthly={};evidence={};valid_sets={}
    expected_dates=[(datetime(2026,1,1)+timedelta(days=i)).date().isoformat() for i in range(243)]
    for name,(charge,reserve) in SCENARIOS.items():
        folder=args.baseline_run if name=='baseline_100_100' and args.baseline_run else args.input/name
        s=json.loads((folder/'summary.json').read_text(encoding='utf-8'))
        m=json.loads((folder/'manifest.json').read_text(encoding='utf-8'))
        code_root=Path(__file__).resolve().parents[1]
        for rel,expected_hash in m['code_hashes'].items():
            assert digest(code_root/rel)==expected_hash, f'model source changed: {rel}'
        retry_history=[];provenance=[];visited=set();ancestor=folder.resolve()
        while ancestor not in visited:
            visited.add(ancestor)
            retry_file=ancestor/'retry_events.jsonl'
            if retry_file.exists():
                retry_history += [dict(run_directory=str(ancestor),**json.loads(line)) for line in retry_file.read_text(encoding='utf-8').splitlines() if line]
            prov_file=ancestor/'resume_provenance.json'
            if not prov_file.exists():break
            prov=json.loads(prov_file.read_text(encoding='utf-8'));provenance.append(prov)
            ancestor=Path(prov['source'])
            if not ancestor.is_absolute():ancestor=Path(__file__).resolve().parents[2]/ancestor
            ancestor=ancestor.resolve()
        cfg=_top_level_scalars(folder/'solver_input.json',FIELDS)
        assert s['success'] and not s['failure'] and s['quality']['blocked_qh']==0
        assert s['cycle_policy']['mode']=='daily_only' and s['cycle_policy']['daily_efc_limit']==2
        assert not s['cycle_policy']['annual_efc_enforced'] and all(v is None for v in s['annual_budget'].values())
        assert m['capacity_award_mode']=='optimize'
        assert datetime.fromisoformat(m['formal_start']).astimezone(TZ)==datetime(2026,1,1,tzinfo=TZ)
        assert datetime.fromisoformat(m['formal_end']).astimezone(TZ)==datetime(2026,9,1,tzinfo=TZ)
        assert (cfg['charge_mw'],cfg['grid_import_mw'],cfg['discharge_mw'],cfg['grid_export_mw'])==(charge,charge,100,100)
        assert (cfg['reserve_limit_up_mw'],cfg['reserve_limit_down_mw'])==(reserve,reserve)
        assert (cfg['e_min_mwh'],cfg['e_max_mwh'],cfg['e_initial_mwh'],cfg['e_terminal_mwh'])==(10,190,10,10)
        assert (cfg['eta_charge'],cfg['eta_discharge'])==(.92,.92)
        rows=_read_rows(folder/'result.json')
        assert len(rows)==23324 and len({r['qh_id'] for r in rows})==23324
        d=defaultdict(lambda:dict(efc=0.,cash_eur=0.,valid_qh=0,total_qh=0))
        mon=defaultdict(lambda:dict(efc=0.,cash={k:0. for k in KEYS},valid_qh=0))
        valid_sets[name]={r['qh_id'] for r in rows if r['cash'] is not None}
        for r in rows:
            date=datetime.fromisoformat(r['time']).astimezone(TZ).date().isoformat()
            x=d[date];mth=mon[date[:7]]
            assert r['efc'] is not None
            x['efc']+=r['efc'];mth['efc']+=r['efc'];x['total_qh']+=1
            if r['cash'] is not None:
                x['valid_qh']+=1;mth['valid_qh']+=1
                x['cash_eur']+=sum(r['cash'].values())
                for k in KEYS:mth['cash'][k]+=r['cash'][k]
        assert sorted(d)==expected_dates
        assert max(v['efc'] for v in d.values())<=2+1e-5
        assert d['2026-03-29']['total_qh']==92
        assert abs(sum(v['efc'] for v in d.values())-s['annual_used']['2026'])<1e-5
        for date,v in d.items():assert abs(v['efc']-s['daily_efc_used'][date])<1e-5
        for month,v in mon.items():
            assert v['valid_qh']==s['months'][month]['valid_qh']
            for k in KEYS:assert abs(v['cash'][k]-s['months'][month]['cash_eur'][k])<1e-5
        windows=0;optimal=0;prior_soc=10.;physical_daily=defaultdict(float);max_efc_error=0.;max_soc_error=0.
        for w in read_array(folder/'result.json','windows'):
            date=datetime.fromisoformat(w['start_utc']).astimezone(TZ).date().isoformat()
            assert date==expected_dates[windows]
            assert abs(w['start_soc_mwh']-prior_soc)<1e-5
            assert abs(w['execution_cash_eur']-d[date]['cash_eur'])<1e-4
            e=w['start_soc_mwh']
            for op in w['operation']:
                assert datetime.fromisoformat(op['qh_id']).astimezone(TZ).date().isoformat()==date
                power=op['power_mw'];h=op['hours']
                assert -charge-1e-5<=power<=100+1e-5
                dc_ch=max(-power,0)*.92*h;dc_dis=max(power,0)*h/.92
                efc=(dc_ch+dc_dis)/360
                physical_daily[date]+=efc
                max_efc_error=max(max_efc_error,abs(efc-op['efc']))
                max_soc_error=max(max_soc_error,abs(e-op['start_soc_mwh']))
                e+=dc_ch-dc_dis
                max_soc_error=max(max_soc_error,abs(e-op['end_soc_mwh']))
                assert 10-1e-5<=e<=190+1e-5
            assert abs(e-w['end_execution_soc_mwh'])<1e-5
            assert w['audit']['model'].get('daily_efc_violation_max',0)<=1e-5
            assert abs(physical_daily[date]-d[date]['efc'])<1e-5
            assert abs(physical_daily[date]-w['audit']['daily_efc_used'][date])<1e-5
            windows+=1;optimal+=int(w['proven_optimal']);prior_soc=e
        assert windows==243 and abs(prior_soc-10)<1e-5
        assert max_efc_error<1e-5 and max_soc_error<1e-5
        total=sum(v['cash_eur'] for v in d.values())
        stats[name]=dict(total_cash_eur=total,total_keur_per_mw=total/100000,
            efc=sum(v['efc'] for v in d.values()),max_daily_efc=max(v['efc'] for v in d.values()),
            days_at_limit=sum(v['efc']>=2-1e-5 for v in d.values()),days_with_activity=sum(v['efc']>1e-5 for v in d.values()),
            valid_qh=len(valid_sets[name]),total_qh=len(rows),windows=windows,proven_optimal=optimal,
            retries=len(retry_history),final_soc_mwh=prior_soc,physical_efc_error_max=max_efc_error,
            physical_soc_error_max=max_soc_error)
        daily[name]=d;monthly[name]=mon
        evidence[name]=dict(configuration=cfg,input_evidence_sha256=digest(folder/'input_evidence.json'),
            solver_input_sha256=digest(folder/'solver_input.json'),summary_sha256=digest(folder/'summary.json'),
            result_sha256=digest(folder/'result.json'),award_source=m['award_rate_source'],
            retry_history=retry_history,resume_provenance=provenance,
            source_code_hashes=m['code_hashes'],run_directory=str(folder.resolve()),stats=stats[name])
    assert len({v['input_evidence_sha256'] for v in evidence.values()})==1
    assert len({v['award_source']['sha256'] for v in evidence.values()})==1
    common=set.intersection(*valid_sets.values())
    assert all(v==common for v in valid_sets.values())
    out.mkdir(parents=True)
    with (out/'daily_efc.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['date_Europe_Madrid','scenario','efc_cycles','daily_limit_cycles','valid_qh_count','total_qh_count','cash_eur'])
        for date in expected_dates:
            for n in SCENARIOS:
                v=daily[n][date];writer.writerow([date,n,v['efc'],2,v['valid_qh'],v['total_qh'],v['cash_eur']])
    with (out/'monthly_results.csv').open('x',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['month','scenario','valid_qh_count','efc_cycles',*(k+'_keur_per_mw' for k in KEYS),'total_keur_per_mw','total_cash_eur'])
        for month in sorted(monthly['baseline_100_100']):
            for n in SCENARIOS:
                v=monthly[n][month];values=[v['cash'][k]/100000 for k in KEYS]
                writer.writerow([month,n,v['valid_qh'],v['efc'],*values,sum(values),sum(v['cash'].values())])
    (out/'validation_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    overview='## MILP怎样计算（简要说明）\n\nMILP可以理解为“在电池和交易规则允许的范围内，寻找收益最高的充放电与交易安排”。模型联合选择日前、日内买卖电量，以及aFRR上下调申报容量；充电与放电状态用开关变量控制，避免同时充放电。\n\n**计算方式。** 每次规划未来两天，实际执行第一天，再更新电量和已成交订单，向前滚动一天。已经锁定的订单不能随意修改。正式统计2026年1—8月；使用事后已知的价格和激活数据，因此结果是这些假设下的历史条件收益，不代表真实预测交易收益，也不是整个8个月一次性求得的全局最优。\n\n**收益目标：**\n\n> 最大化：日前净收入＋日内净收入＋aFRR容量收入＋aFRR激活净收入＋规划期末剩余电量的估值。\n\n买电支出计为负现金流。期末电量估值用于避免短期规划无故把电池放空，不计入报告中的实际市场收益；报告收入也未扣除退化、交易费、税费、投资和运维费用。\n\n**aFRR的两项简化计算：**\n\n> 容量收入＝申报容量 × 对应15分钟容量价格 × 中标率代理p；p＝系统已分配容量÷系统总报价容量，最高取1。\n>\n> 激活电量＝申报容量 × 历史激活比例α × 0.25小时；激活现金流再按对应价格及上下调收支方向计算。\n\np是系统分配比例代理，不是本站真实中标概率；模型将它加入收益目标后重新优化，但物理备用承诺和激活仍按完整申报容量计算，不再乘p。α由历史系统激活电量与已分配容量推算；每个15分钟时段按先下调、后上调、剩余时间保持基准出力的简化路径计算电池状态。\n\n**电池与功率约束：**\n\n> 下一时刻电量＝当前电量＋0.92 × 实际充电功率 × 时长－实际放电功率 × 时长÷0.92。\n>\n> 上调申报容量 ≤ 出口功率上限－基准净出力；下调申报容量 ≤ 进口功率上限＋基准净出力。\n\n功率单位为MW，时长为小时，电量为MWh；基准净出力以向电网送电为正。总容量200 MWh，可用电量始终保持10–190 MWh（SOC 5%–95%），期初与正式期末均为10 MWh。三个场景分别采用100／100或50／100 MW充放电及并网功率，aFRR上下调申报上限各100或各150 MW，并同时满足上述功率余量约束。\n\n**每日循环约束：**\n\n> 当日EFC＝当日电池侧充入与放出电量之和÷360 MWh ≤ 2次。\n\n360 MWh＝2×(190－10) MWh，即在可用电量范围内完整充放一次计1次EFC。额度按马德里自然日重置、不结转，替代原年度额度。缺失时段不补收益，按零功率衔接电量。以上中标代理、激活路径和循环额度均为建模假设，官方数据来源及其他限制在后文说明。\n\n'
    report=['# 西班牙储能每日最多2次EFC：2026年1—8月测算对比','',
        overview.rstrip(), '', '## 统计口径与单位','',
        f'正式区间为马德里当地2026-01-01至2026-08-31，共243个自然日、23,324个15分钟时段；三个场景共同有效{len(common):,}个时段，覆盖率{len(common)/23324:.2%}。缺失数据未补算。',
        '收益为这8个月有效时段累计市场现金毛收益，未年化；千欧元／MW统一按100 MW放电额定功率折算。1千欧元／MW对应整站10万欧元；负现金流表示该市场项净支出。',
        'EFC单位为等效完整循环次数；每日最多2次，相当于电池侧充入与放出电量合计不超过720 MWh。MW是功率，MWh是电量或容量。','',
        '## 三场景结果','',
        '| 场景 | 8个月收益（千欧元／MW） | 整站收益（万欧元） | 较100／100 MW场景（%） | 累计EFC（次） | 日上限用满天数（天） |',
        '|---|---:|---:|---:|---:|---:|']
    reference=stats['baseline_100_100']['total_cash_eur']
    for n,v in stats.items():
        report.append(f"| {NAMES[n]} | {v['total_keur_per_mw']:.2f} | {v['total_cash_eur']/10000:,.2f} | {(v['total_cash_eur']/reference-1)*100:+.2f}% | {v['efc']:.3f} | {v['days_at_limit']} |")
    sensitivity_delta=stats['asymmetric_cap150']['total_keur_per_mw']-stats['asymmetric_cap100']['total_keur_per_mw']
    report+=['',f"在同一50／100 MW配置下，aFRR上／下调申报上限各150 MW相对各100 MW，8个月累计收益差额为{sensitivity_delta:+.2f}千欧元／MW（整站{sensitivity_delta*10:+.2f}万欧元）。这仍是两日滚动策略结果，不能保证所有情景放宽约束后全期收益都单调提高。",
        '', '日上限用满天数按当日EFC≥2−0.00001次统计。243天的逐日上限合计为486次，但未用额度不能跨日转移，不要求每天用满。原方案2026年统计期总额度约345.992次；本次同时改变额度总量上限与使用节奏，不能视为只把原额度平均分摊。','',
        '## 六项市场现金流','',
        '单位：千欧元／MW，均为2026年1—8月共同有效时段累计。容量项已累计为金额，不是容量报价。','',
        '| 市场 | 充100／放100、申报100 MW（千欧元／MW） | 充50／放100、申报100 MW（千欧元／MW） | 充50／放100、申报150 MW（千欧元／MW） |',
        '|---|---:|---:|---:|']
    for k,label in zip(KEYS,LABELS):
        values=[sum(v['cash'][k] for v in monthly[n].values())/100000 for n in SCENARIOS]
        report.append('| '+label+' | '+' | '.join(f'{v:.2f}' for v in values)+' |')
    report+=['','## 月度收益与循环使用','',
        '收益列单位：千欧元／MW，当月累计、未年化；EFC列单位：次。月份按Europe/Madrid划分。','',
        '| 月份 | 有效15分钟时段（个） | 100／100收益（千欧元／MW） | 100／100 EFC（次） | 50／100申报100收益（千欧元／MW） | 50／100申报100 EFC（次） | 50／100申报150收益（千欧元／MW） | 50／100申报150 EFC（次） |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for month in sorted(monthly['baseline_100_100']):
        values=[]
        for n in SCENARIOS:
            v=monthly[n][month];values += [f"{sum(v['cash'].values())/100000:.2f}",f"{v['efc']:.3f}"]
        report.append(f"| {month} | {monthly['baseline_100_100'][month]['valid_qh']} | "+' | '.join(values)+' |')
    report+=['','## 已确认假设与模型解释','',
        '- 新约束来自用户确认的情景假设：每日最多2次EFC，取代旧年度总额度；每日未用额度不结转，也不向其他日期借额度。夏令时23小时日及部分缺失日仍使用2次上限。',
        '- 三场景电池总容量200 MWh，SOC边界10–190 MWh（5%–95%），初始和正式期末均为10 MWh；充放效率各92%。EFC=电池侧充放电吞吐量÷360 MWh。',
        '- aFRR采用“容量收入引入代理系数后重新优化”；代理系数仅折减容量收入，完整申报的物理承诺及激活口径沿用既有模型。150 MW是理论敏感性申报上限，并非可同时满额上下调或已通过项目资格认证。',
        '- 事后已知价格和激活、两天规划逐日执行。每日约束同时施加于规划窗口的两天，并独立审计当日执行；它消除了旧年度额度提前耗尽的机制，但不能证明全期全局最优或真实可执行收益。',
        '- 本次从2026年1月独立起算，无2025年遗留订单或SOC；初始时点之前已关闭的交易按现有规则置零。2026年9月1日只用于前瞻，不计入收益和EFC；正式8月31日期末SOC单独限制为10 MWh。',
        '- 原20个月运行中的2026年结果含跨年状态和订单，与本次起点不同，不可将两者差额全部归因于额度变化。',
        '- 原始输入文件保留旧annual_efc_budget字段用于兼容，但本场景不使用它作为约束；结果annual_budget为null，cycle_policy为daily_only，annual_used仅是累计使用量。',
        '- 不含退化现金、交易费、税费、投资或运维费用；缺失数据沿用零功率/SOC衔接、收益空值处理。','',
        '## 验证结果','',
        '| 场景 | 完成日窗口（个） | 达求解gap标准窗口（个） | 数值重试（次） | 最大日EFC（次） | 正式期末SOC（MWh） |',
        '|---|---:|---:|---:|---:|---:|']
    for n,v in stats.items():
        report.append(f"| {NAMES[n]} | {v['windows']} | {v['proven_optimal']} | {v['retries']} | {v['max_daily_efc']:.6f} | {v['final_soc_mwh']:.6f} |")
    report+=['','逐日从物理功率及持续时间独立重算EFC，核对报告、每日上限、月度与全期汇总；复核SOC递推、功率边界、窗口连续性、期初期末SOC、现金汇总和三场景输入证据一致，均通过。',
        '100／100 MW场景在4月21日冻结订单边界遇到数值不可行；保留原失败结果后恢复。重试仅将HiGHS的可行性容差设为既有独立验收容差1e-5；未改约束值、订单、日额度或独立验收阈值。该日物理执行EFC约1.826次，恢复后再次逐日验收。表中重试次数包含原运行和恢复运行的记录，完整信息见验证证据。',
        '代码验收记录：58项每日额度及旧核心相关测试通过；补充激活吞吐量测试后，每日额度专项7项全部通过。三个场景四天试算成功。求解gap默认1e-4；窗口最优标记仅指该窗口达到求解标准。',
        '','## 官方来源、未解决问题与文件','',
        '规则事实和官方数据沿用REE/eSIOS及OMIE既有归档，详见[已确认研究及官方来源记录](../../research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)。本次没有新增官方规则；每日2次EFC为用户指定建模假设。访问及获取日期沿用原归档，未重新下载原始数据。',
        '仍待确认：150 MW跨零调节资格与设备能力、历史容量机制切换日期、报价与分配容量地域匹配、连续满额激活履约能力。上述限制不因本次循环额度修改而消失。','',
        '- [逐日EFC与现金明细](daily_efc.csv)：日期、场景、EFC次数、2次日上限、有效时段数及欧元现金。',
        '- [月度六项收益和EFC](monthly_results.csv)：收益列单位已写入字段名keur_per_mw，整站金额为cash_eur。',
        '- [输入哈希与验证证据](validation_evidence.json)：场景配置、数据及代码哈希、原始结果目录和核验统计。',
        '- [已确认测算边界及数学约束](../../code/project/每日EFC额度边界_20261029.md)。','']
    report+=['## 本次变更文件','',
        '- 模型：[核心约束与独立审计](../../code/src/es_synthetic_market/_baseline_core.py)、[求解入口](../../code/src/es_synthetic_market/core.py)、[每日滚动执行及报告](../../code/src/es_synthetic_market/perfect.py)、[执行年度检查开关](../../code/src/es_synthetic_market/rolling.py)。',
        '- 运行：[参数与输入留档](../../code/project/run_es_perfect_v1.py)、[恢复及数值重试](../../code/project/resume_es_capacity_award_rate.py)、[三场景批量入口](../../code/project/run_es_daily_efc_20261029.py)。',
        '- 验证与文档：[每日EFC测试](../../code/tests/test_es_daily_efc.py)、[独立验证和报告生成](../../code/project/report_es_daily_efc_20261029.py)、[项目说明](../../README.md)、上述边界文件、本报告及三份数据/证据附件。',
        '- 原始输入未修改；大体量运行明细保留在本地output目录，不纳入Git。各场景精确目录及哈希见validation_evidence.json；原失败输出未覆盖。','']
    report+=brief_description(monthly['asymmetric_cap100'])
    from es_monthly_operating_metrics_20261101 import export as export_operating_metrics
    operating_lines,_=export_operating_metrics(args.input/'asymmetric_cap100',out)
    report+=operating_lines
    (out/'测算对比报告.md').write_text('\n'.join(report),encoding='utf-8')
    print(json.dumps(stats,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
