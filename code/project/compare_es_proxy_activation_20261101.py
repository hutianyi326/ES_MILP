"""Audit proxy-activation rerun and append a reproducible comparison section."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from es_monthly_operating_metrics_20261101 import compute, file_hash, KEYS
from report_es_daily_efc_20261029 import read_array
from build_es_result_presentation import _read_rows

TZ=ZoneInfo('Europe/Madrid')
MARKER='## 代理折算中标容量激活对照场景'
LABELS=('日前DA','日内ID','aFRR容量Up','aFRR容量Down','aFRR激活Up','aFRR激活Down')


def load(path):return json.loads(path.read_text(encoding='utf-8'))


def audit(run):
    s=load(run/'summary.json');cfg=load(run/'solver_input.json');m=load(run/'manifest.json')
    assert s['success'] and s['failure'] is None
    assert s['cycle_policy']['daily_efc_limit']==2 and not s['cycle_policy']['annual_efc_enforced']
    assert (cfg['charge_mw'],cfg['grid_import_mw'],cfg['discharge_mw'],cfg['grid_export_mw'])==(50,50,100,100)
    assert (cfg['e_min_mwh'],cfg['e_max_mwh'],cfg['e_initial_mwh'],cfg['e_terminal_mwh'])==(10,190,10,10)
    assert (cfg['eta_charge'],cfg['eta_discharge'])==(.92,.92)
    assert (cfg['reserve_limit_up_mw'],cfg['reserve_limit_down_mw'])==(100,100)
    rows=_read_rows(run/'result.json');assert len(rows)==23324
    valid={r['qh_id'] for r in rows if r['cash'] is not None}
    daily=defaultdict(float);monthly=defaultdict(float)
    for r in rows:
        day=datetime.fromisoformat(r['time']).astimezone(TZ).date().isoformat()
        daily[day]+=r['efc'];monthly[day[:7]]+=r['efc']
    assert len(daily)==243 and max(daily.values())<=2+1e-5
    for day,v in daily.items():assert abs(v-s['daily_efc_used'][day])<1e-5
    physical_daily=defaultdict(float);windows=0;optimal=0;prior=10.;maxerr=0.;max_efc_err=0.;headroom=0.
    for w in read_array(run/'result.json','windows'):
        day=datetime.fromisoformat(w['start_utc']).astimezone(TZ).date().isoformat()
        assert abs(w['start_soc_mwh']-prior)<1e-5
        e=w['start_soc_mwh']
        for op in w['operation']:
            assert datetime.fromisoformat(op['qh_id']).astimezone(TZ).date().isoformat()==day
            p=op['power_mw'];h=op['hours'];assert -50-1e-5<=p<=100+1e-5
            dcch=max(-p,0)*.92*h;dcdis=max(p,0)*h/.92
            maxerr=max(maxerr,abs(e-op['start_soc_mwh']))
            e+=dcch-dcdis
            maxerr=max(maxerr,abs(e-op['end_soc_mwh']))
            assert 10-1e-5<=e<=190+1e-5
            efc=(dcch+dcdis)/360
            max_efc_err=max(max_efc_err,abs(efc-op['efc']))
            physical_daily[day]+=efc
        assert abs(e-w['end_execution_soc_mwh'])<1e-5
        assert abs(physical_daily[day]-daily[day])<1e-5
        headroom=max(headroom,w['audit']['model'].get('p0_event_headroom_max',0))
        assert w['audit']['model'].get('daily_efc_violation_max',0)<=1e-5
        windows+=1;optimal+=int(w['proven_optimal']);prior=e
    assert windows==243 and abs(prior-10)<1e-5 and maxerr<1e-5 and max_efc_err<1e-5 and headroom<1e-5
    metrics,evidence=compute(run)
    evidence['manifest_sha256']=file_hash(run/'manifest.json')
    evidence.update(windows=windows,proven_optimal_windows=optimal,final_soc_mwh=prior,
        max_soc_error_mwh=maxerr,max_efc_error=max_efc_err,max_gct_headroom_violation_mw=headroom,
        monthly_efc=dict(monthly),daily_efc=dict(daily),max_daily_efc=max(daily.values()),
        days_at_efc_limit=sum(v>=2-1e-5 for v in daily.values()),total_efc=sum(daily.values()),
        retry_count=s.get('retry_count',0),source_code_hashes=m['code_hashes'])
    return metrics,evidence,valid


def table(headers,rows):
    return ['| '+' | '.join(headers)+' |','|---|'+'---:|'*(len(headers)-1),
        *['| '+' | '.join(str(v) for v in r)+' |' for r in rows],'']


def render(old,new,a,b):
    def f(x,n=2):return '不适用' if x is None else f'{x:,.{n}f}'
    def total(v):return sum(v[k+'_cash_eur'] for k in KEYS)
    ot=old['TOTAL'];nt=new['TOTAL'];oc=total(ot);nc=total(nt)
    lines=[MARKER,'',
        '本节新增2026年1—8月重算，比较相同设备、输入与有效时段下两种激活口径。前文三场景及“基础场景月度运营指标”仍为原有完整申报容量激活结果，本节单独列出新结果。','',
        '### 1. 唯一调整及共同边界','',
        '- **原基础场景：** 激活幅度为完整申报容量R，激活电量为R×α×0.25小时。',
        '- **新对照场景：** 代理折算中标容量Q=p×R；激活幅度改为Q，电量为p×R×α×0.25小时。激活时长α×0.25小时不变，p只乘一次。容量收入在两场景中均按p×R×容量价计算。',
        '- **完整申报功率预留不变：** B+RUp≤100 MW，B−RDn≥−50 MW；上下调R分别不超过100 MW，且二者合计受150 MW功率跨度约束。R仍为整数，Q可为小数。',
        '- **物理路径同步调整：** 依次为下调B−pDnRDn、上调B+pUpRUp、空闲B，跨零后按实际功率正负计算充放电、92%效率损耗、SOC和EFC。仅折算收益而保留旧SOC/EFC的做法未采用。',
        '- **共同边界：** 充50/放100 MW、200 MWh电池，SOC10—190 MWh，期初/末10 MWh；每日最多2 EFC，无年度额度、无结转，分母360 MWh。两天规划逐日执行、冻结已成交订单；9月1日仅前瞻、不计收入。共同有效20,263个15分钟时段，覆盖86.88%；缺失时段零功率衔接。','',
        'p沿用历史系统已分配/报价容量比例代理，并非本站实际中标概率；新激活方法是用户确认的建模假设，不是新增官方规则。模型重新优化日前、日内和aFRR申报，故收益差异包含交易结构与SOC/EFC使用变化，不能把原激活收入简单乘平均p解释为新结果。','',
        '### 2. 全期对比','',
        f'新场景总收入为 **{f(nc)} 欧元**，较原场景变化 **{f(nc-oc)} 欧元（{f((nc/oc-1)*100)}%）**。这里“总收入”仍指六项有符号市场净现金流，已含购电支出，未扣退化、交易费、税费、投资和运维费用，未年化。','']
    pairs=[('总收入（欧元）',oc,nc),('每MW收入（K欧元/MW；分母100 MW）',oc/100000,nc/100000),
        ('累计EFC（次）',a['total_efc'],b['total_efc']),('达到每日2 EFC的天数（天）',a['days_at_efc_limit'],b['days_at_efc_limit']),
        ('Up激活电量（MWh）',ot['up_activation_mwh'],nt['up_activation_mwh']),('Down激活电量（MWh）',ot['down_activation_mwh'],nt['down_activation_mwh']),
        ('实际交流侧充电量（MWh）',ot['actual_charge_mwh'],nt['actual_charge_mwh']),('实际交流侧放电量（MWh）',ot['actual_discharge_mwh'],nt['actual_discharge_mwh'])]
    lines+=table(['指标','原：完整R激活','新：代理pR激活','变化（新−原）'],[(label,f(x),f(y),f(y-x)) for label,x,y in pairs])
    lines+=table(['市场','原收入（欧元）','新收入（欧元）','变化（欧元）'],[(label,f(ot[k+'_cash_eur']),f(nt[k+'_cash_eur']),f(nt[k+'_cash_eur']-ot[k+'_cash_eur'])) for label,k in zip(LABELS,KEYS)])
    group_delta={name:sum(nt[k+'_cash_eur']-ot[k+'_cash_eur'] for k in keys) for name,keys in
        [('spot',('DA','ID')),('capacity',('cap_up','cap_down')),('activation',('act_up','act_down'))]}
    lines+=[f"按现金流分解：日前＋日内变化{f(group_delta['spot'])}欧元，容量收入变化{f(group_delta['capacity'])}欧元，激活现金流变化{f(group_delta['activation'])}欧元，三者合计为总收入差额。容量收入变化来自重新优化后的申报变化，其代理计价公式未改变。",'']
    lines+=['### 3. 月度收入与EFC对比','']
    lines+=table(['月份','原总收入（欧元）','新总收入（欧元）','收入变化（欧元）','新收入（K欧元/MW）','原EFC（次）','新EFC（次）'],
        [(m,f(total(old[m])),f(total(new[m])),f(total(new[m])-total(old[m])),f(total(new[m])/100000),f(a['monthly_efc'][m]),f(b['monthly_efc'][m])) for m in new if m!='TOTAL'])
    lines+=['新场景各市场收益占比如下：各项有符号现金流÷当月总收入，允许出现负值；显示值因四舍五入可能不精确合计100%。','']
    lines+=table(['月份',*[x+'（%）' for x in LABELS]],[(m,*[f(100*v[k+'_cash_eur']/total(v)) for k in KEYS]) for m,v in new.items()])
    lines+=['### 4. 激活电量和容量变化','',
        '下表激活量为相对基准出力的调节MWh，不等同于电池实际充放电MWh。折算后平均中标容量为Σ(pR×0.25小时)÷当月有效小时，包含有效时段中的零申报时段，排除缺失时段。','']
    lines+=table(['月份','原Up激活（MWh）','新Up激活（MWh）','原Down激活（MWh）','新Down激活（MWh）','新平均Up折算中标（MW）','新平均Down折算中标（MW）'],
        [(m,f(old[m]['up_activation_mwh']),f(v['up_activation_mwh']),f(old[m]['down_activation_mwh']),f(v['down_activation_mwh']),f(v['up_award_proxy_mw_h']/(v['valid_qh_count']*.25)),f(v['down_award_proxy_mw_h']/(v['valid_qh_count']*.25))) for m,v in new.items()])
    lines+=['激活幅度降低会改变净功率的跨零情况，并释放部分SOC和循环额度供重新调度，因此整站EFC和总收入的变化不能仅由激活电量降幅推算。激活时长参数虽不变，重新优化后有申报的时段可变化，累计激活时长也可变化。','',
        '### 5. 核验、来源与明细','',
        f'- 两场景输入逐项比较一致（新增激活模式字段除外），有效时段完全一致；旧结果哈希与已归档报告一致。新模型源文件哈希与运行清单一致。新场景243个执行窗口全部通过现金、功率、SOC及每日EFC独立核验，其中求解器在设置容差内报告最优的窗口为{b["proven_optimal_windows"]}个；数值重试{b["retry_count"]}次。',
        f'- 新场景最大每日EFC为{f(b["max_daily_efc"],8)}次，期末SOC为{f(b["final_soc_mwh"])} MWh；最大SOC递推误差{b["max_soc_error_mwh"]:.3g} MWh。65项模型测试及真实数据4天短区间验证通过。',
        '- 官方来源继续使用REE/eSIOS、OMIE原归档及[既有来源索引](../../research/西班牙aFRR容量收益中标率敏感性方案_20260923.md)，没有新下载或新增官方规则。历史地域匹配、规则切换及连续满额激活履约能力等待确认问题保留；本次未新增完整R持续激活的SOC压力约束。',
        '- 这是事后信息下的条件滚动测算，不是实际可执行收益或全期联合最优值。',
        '- [月度对照CSV](proxy_activation_monthly_comparison.csv)：两场景收入、六项市场现金流和占比、EFC及全部月度运营指标；最终充放电均价沿用日前＋日内最终净头寸口径；激活价格另列，Down恢复市场报价符号。',
        '- 本次同步修改核心模型、滚动执行、运行/续算入口与月度统计；新增[激活口径测试](../../code/tests/test_es_proxy_activation.py)及[对照报告生成与独立核验](../../code/project/compare_es_proxy_activation_20261101.py)，并更新README及边界说明。',
        '- [逐日EFC对照](proxy_activation_daily_efc.csv)、[输入/模型/输出哈希及验证证据](proxy_activation_validation_evidence.json)、[已确认边界](../../code/project/代理中标容量激活边界_20261101.md)。大体量新结果独立保存在`output/proxy_activation_20261101/asymmetric_cap100_proxy`，旧结果未覆盖。','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--new',type=Path,required=True);p.add_argument('--report-dir',type=Path,required=True)
    args=p.parse_args();out=args.report_dir
    oldcfg=load(args.base/'solver_input.json');newcfg=load(args.new/'solver_input.json')
    for cfg in (oldcfg,newcfg):
        for q in cfg['qhs']:q.pop('activation_capacity_basis',None)
    assert oldcfg==newcfg,'input changed beyond activation basis'
    assert file_hash(args.base/'input_evidence.json')==file_hash(args.new/'input_evidence.json')
    om=load(args.base/'manifest.json');nm=load(args.new/'manifest.json')
    assert om.get('activation_capacity_basis','full_bid')=='full_bid' and nm['activation_capacity_basis']=='proxy_awarded'
    assert om['award_rate_source']['sha256']==nm['award_rate_source']['sha256']
    for name,sha in nm['code_hashes'].items():assert file_hash(Path(__file__).resolve().parents[1]/name)==sha,name
    archived=load(out/'validation_evidence.json')['asymmetric_cap100']
    for name,key in [('solver_input.json','solver_input_sha256'),('result.json','result_sha256'),('summary.json','summary_sha256')]:
        assert file_hash(args.base/name)==archived[key]
    old,a,av=audit(args.base);print('Base independent audit passed',flush=True)
    new,b,bv=audit(args.new);print('New independent audit passed',flush=True)
    assert av==bv and len(av)==20263
    evidence=dict(input_identical_except_activation_mode=True,valid_periods_identical=True,
        old_output_matches_archived_hashes=True,new_code_matches_run_manifest=True,
        official_sources='unchanged archived REE/eSIOS and OMIE; see existing source index',
        old=a,new=b,smoke=load(args.new.parent/'smoke_4days.json'),tests='65 passed',
        legacy_hash_compatibility=load(args.new.parent/'legacy_hash_compatibility.json'))
    (out/'proxy_activation_validation_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
    records=[]
    for scenario,metrics,ev in [('full_bid',old,a),('proxy_awarded',new,b)]:
        for month,v in metrics.items():
            cash=sum(v[k+'_cash_eur'] for k in KEYS)
            records.append(dict(month=month,scenario=scenario,**v,total_cash_eur=cash,total_keur_per_mw=cash/100000,
                efc_cycles=ev['total_efc'] if month=='TOTAL' else ev['monthly_efc'][month],
                **{k+'_share_pct':100*v[k+'_cash_eur']/cash for k in KEYS}))
    fields=list(dict.fromkeys(k for row in records for k in row))
    with (out/'proxy_activation_monthly_comparison.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(records)
    with (out/'proxy_activation_daily_efc.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.writer(f);writer.writerow(['date_Europe_Madrid','full_bid_efc_cycles','proxy_awarded_efc_cycles','daily_limit_cycles'])
        for day in sorted(a['daily_efc']):writer.writerow([day,a['daily_efc'][day],b['daily_efc'][day],2])
    section=render(old,new,a,b)
    (out/'proxy_activation_comparison_section.md').write_text(section,encoding='utf-8')
    report=out/'测算对比报告.md';text=report.read_text(encoding='utf-8').split(MARKER)[0].rstrip()
    notice='> 2026-11-01新增：文末“代理折算中标容量激活对照场景”按pR计算激活并重新优化；前文原三场景继续采用完整R激活。\n'
    if notice.strip() not in text:
        title,rest=text.split('\n',1);text=title+'\n\n'+notice+rest
    report.write_text(text+'\n\n'+section,encoding='utf-8')
    for label,metrics,ev in [('old',old,a),('new',new,b)]:
        print(json.dumps(dict(scenario=label,total_cash_eur=sum(metrics['TOTAL'][k+'_cash_eur'] for k in KEYS),efc=ev['total_efc'],retries=ev['retry_count']),ensure_ascii=False))


if __name__=='__main__':main()
