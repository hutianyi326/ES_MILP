"""Monthly settled net-spot prices and capacity/activation metrics; no re-solve."""
import argparse
from collections import defaultdict
import csv
from datetime import datetime
import hashlib
import json
from pathlib import Path
from zoneinfo import ZoneInfo

from build_es_result_presentation import _iter_json_array, _read_rows

TZ=ZoneInfo('Europe/Madrid')
MARKER='### 基础场景月度充放电及aFRR运营指标'
KEYS=('DA','ID','cap_up','cap_down','act_up','act_down')


def ratio(n,d):
    return n/d if abs(d)>1e-9 else None


def file_hash(path):
    with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def derive(v):
    out=dict(v)
    out['net_charge_price_eur_per_mwh']=ratio(v.get('net_charge_cost_eur',0),v.get('net_charge_mwh',0))
    out['net_discharge_price_eur_per_mwh']=ratio(v.get('net_discharge_income_eur',0),v.get('net_discharge_mwh',0))
    for d in ('up','down'):
        hours=v.get(d+'_reserve_mw_h',0)
        out[d+'_capacity_market_price_eur_per_mw_h']=ratio(v.get(d+'_capacity_raw_cash_eur',0),hours)
        out[d+'_capacity_effective_price_eur_per_mw_h']=ratio(v.get(d+'_capacity_cash_eur',0),hours)
        out[d+'_award_rate_proxy_pct']=ratio(100*v.get(d+'_award_proxy_mw_h',0),hours)
        energy=v.get(d+'_activation_mwh',0)
        out[d+'_activation_market_price_eur_per_mwh']=ratio((1 if d=='up' else -1)*v.get(d+'_activation_cash_eur',0),energy)
        out[d+'_activation_100mw_equivalent_hours']=energy/100
    return out


def compute(run):
    from report_es_daily_efc_20261029 import read_array
    summary=json.loads((run/'summary.json').read_text(encoding='utf-8'))
    assert summary['success'] and summary['cycle_policy']['daily_efc_limit']==2
    inp=json.loads((run/'solver_input.json').read_text(encoding='utf-8'))
    assert (inp['charge_mw'],inp['discharge_mw'],inp['reserve_limit_up_mw'],inp['reserve_limit_down_mw'])==(50,100,100,100)
    qmap={q['qh_id']:q for q in inp['qhs']}
    del inp
    result_rows=_read_rows(run/'result.json')
    valid={r['qh_id'] for r in result_rows if r['cash'] is not None}
    cash_qh={r['qh_id']:r['cash'] for r in result_rows if r['cash'] is not None}
    pos=defaultdict(lambda:defaultdict(float));seen=set();ledger_count=0
    for e in _iter_json_array(run/'cash_ledger.json'):
        ledger_count+=1
        key=tuple(e['key'])
        assert key not in seen,'duplicate ledger entry'
        seen.add(key)
        typ=e['settlement_type'];direction=e['direction']
        qid=json.loads(e['object_id'])[1] if typ in ('DA_energy','IDA_energy') else e['object_id']
        if qid not in valid:
            assert abs(e['cash_eur'])<1e-5 and abs(e['quantity'])<1e-5
            continue
        assert datetime.fromisoformat(qid).astimezone(TZ).date().isoformat()==e['execution_day']
        a=pos[qid]
        if typ in ('DA_energy','IDA_energy'):
            a['spot_net_mwh']+=(1 if direction=='sell' else -1)*e['quantity']*e['hours']
            a['spot_cash_eur']+=e['cash_eur']
            a['DA' if typ=='DA_energy' else 'ID']+=e['cash_eur']
        elif typ=='aFRR_capacity':
            a[direction+'_reserve_mw']+=e['quantity']
            a['cap_'+direction]+=e['cash_eur']
        elif typ=='aFRR_activation':
            a[direction+'_activation_mwh']+=e['quantity']
            a['act_'+direction]+=e['cash_eur']
        else:raise ValueError(typ)
    del seen
    monthly=defaultdict(lambda:defaultdict(float));cash_error=0.;activation_error=0.
    for qid in sorted(valid):
        q=qmap[qid];a=pos[qid];month=datetime.fromisoformat(qid).astimezone(TZ).strftime('%Y-%m');v=monthly[month]
        v['valid_qh_count']+=1
        for k in KEYS:
            error=abs(a[k]-cash_qh[qid][k]);cash_error=max(cash_error,error)
            assert error<1e-5,(qid,k,error)
            v[k+'_cash_eur']+=a[k]
        net=a['spot_net_mwh'];cash=a['spot_cash_eur']
        # Sign classification uses the final QH position, not gross trade volume.
        if net < -1e-7:
            v['net_charge_mwh']-=net;v['net_charge_cost_eur']-=cash
        elif net > 1e-7:
            v['net_discharge_mwh']+=net;v['net_discharge_income_eur']+=cash
        else:
            v['zero_net_spot_cash_eur']+=cash;v['zero_net_spot_qh_count']+=1
        for d in ('up','down'):
            r=a[d+'_reserve_mw'];rate=q['afrr_award_rate_'+d]
            assert -1e-7<=r<=100+1e-7
            raw=q['afrr_capacity_price_'+d+'_eur_per_mw_qh']
            assert r<1e-7 or rate is not None
            assert abs(a['cap_'+d]-r*raw*(rate or 0))<1e-5
            expected=r*q['alpha_'+d]*.25
            activation_error=max(activation_error,abs(expected-a[d+'_activation_mwh']))
            assert activation_error<1e-5
            assert abs(a['act_'+d]-expected*q['afrr_activation_price_'+d+'_eur_per_mwh'])<1e-5
            v[d+'_reserve_mw_h']+=r*.25
            v[d+'_award_proxy_mw_h']+=r*.25*(rate or 0)
            v[d+'_capacity_raw_cash_eur']+=r*raw
            v[d+'_capacity_cash_eur']+=a['cap_'+d]
            v[d+'_activation_mwh']+=expected
            v[d+'_activation_hours']+=q['alpha_'+d]*.25 if r>1e-7 else 0
            v[d+'_activation_cash_eur']+=a['act_'+d]
    # Independently rebuild baseline and activation duration from executed phases.
    phase_totals=defaultdict(lambda:defaultdict(float));power_error=0.;windows=0
    for w in read_array(run/'result.json','windows'):
        windows+=1
        for op in w['operation']:
            qid=op['qh_id']
            if qid not in valid:
                assert abs(op['power_mw'])<1e-5
                continue
            a=pos[qid];phase=op['phase'];b=a['spot_net_mwh']/.25
            expected=b+(a['up_reserve_mw'] if phase=='up' else -a['down_reserve_mw'] if phase=='down' else 0)
            power_error=max(power_error,abs(expected-op['power_mw']))
            assert power_error<1e-5
            v=phase_totals[datetime.fromisoformat(qid).astimezone(TZ).strftime('%Y-%m')]
            p=op['power_mw'];h=op['hours']
            v['actual_charge_mwh']+=max(-p,0)*h;v['actual_discharge_mwh']+=max(p,0)*h
            if phase in ('up','down') and a[phase+'_reserve_mw']>1e-7:
                v[phase+'_activation_hours']+=h
                v[phase+'_activation_mwh']+=a[phase+'_reserve_mw']*h
    assert windows==243 and len(valid)==20263 and len(monthly)==8
    for month,v in monthly.items():
        for d in ('up','down'):
            for suffix in ('_activation_hours','_activation_mwh'):
                assert abs(v[d+suffix]-phase_totals[month][d+suffix])<1e-5
        for k in KEYS:assert abs(v[k+'_cash_eur']-summary['months'][month]['cash_eur'][k])<1e-5
        expected_spot=v['net_discharge_income_eur']-v['net_charge_cost_eur']+v['zero_net_spot_cash_eur']
        assert abs(expected_spot-v['DA_cash_eur']-v['ID_cash_eur'])<1e-5
        physical=phase_totals[month]
        assert abs((physical['actual_discharge_mwh']-physical['actual_charge_mwh'])-(v['net_discharge_mwh']-v['net_charge_mwh']+v['up_activation_mwh']-v['down_activation_mwh']))<1e-5
        v.update({k:physical[k] for k in ('actual_charge_mwh','actual_discharge_mwh')})
    total=defaultdict(float)
    for v in monthly.values():
        for k,value in v.items():total[k]+=value
    metrics={m:derive(v) for m,v in sorted(monthly.items())}
    metrics['TOTAL']=derive(total)
    evidence=dict(scenario='asymmetric_cap100',run_directory=str(run.resolve()),
        charge_discharge_price_policy='DA_ID_final_QH_net_position_excluding_aFRR',
        capacity_weighting='submitted_MW_times_0.25h; award_rate_is_proxy_not_actual_station_award',
        activation_price_weighting='activation_MWh; down_market_price_is_negative_of_ledger_cash_price',
        activation_hours='sum(alpha*0.25h) over positive reserve; also provide MWh/100MW equivalent hours',
        net_energy_zero_tolerance_mwh=1e-7,monthly_qh_counts={m:int(v['valid_qh_count']) for m,v in monthly.items()},
        ledger_entries=ledger_count,executed_days=windows,maximum_qh_cash_reconciliation_error_eur=cash_error,
        maximum_activation_energy_error_mwh=activation_error,maximum_baseline_power_error_mw=power_error,
        checks='cash, capacity proxy, activation energy/prices/durations, executed baseline and physical net energy all reconciled',
        source_sha256={n:file_hash(run/n) for n in ('solver_input.json','cash_ledger.json','result.json','summary.json')},metrics=metrics)
    return metrics,evidence


def render(metrics):
    def f(v):return '不适用' if v is None else f'{v:,.2f}'
    def table(headers,fields):
        lines=['| '+' | '.join(headers)+' |','|---|'+'---:|'*len(fields)]
        for month,v in metrics.items():
            label='全期加权／累计' if month=='TOTAL' else month
            lines.append('| '+label+' | '+' | '.join(f(v.get(k,0.)) for k in fields)+' |')
        return lines+['']
    lines=[MARKER,'',
        '以下仍采用充50／放100 MW、aFRR上／下调申报上限各100 MW的基础场景，统计2026年1—8月已有测算结果。均价按实际对应电量或申报容量加权，不是各时段价格的简单算术平均；全期行从全期分子、分母重新计算。无对应电量／申报容量时标为“不适用”。','',
        '#### 1. 最终充电、放电单价','',
        '按用户确认口径，先将同一15分钟交付时段的日前＋日内交易合并为最终净头寸。净购电时段的合计净支出÷净购电量，得到最终充电单价；净售电时段的合计净收入÷净售电量，得到最终放电单价。该单价包含这些净购／净售时段中的日前与日内调整价差，并非原始市场报价。电量均在交流并网侧计量，不含aFRR激活电量和现金流，也不含容量收入，不能直接当作含激活后的电池实际充放电综合成本。',
        '最终净头寸为零的时段仍可能因日前／日内交易价差产生现金流；其金额单列，避免把零电量现金流分摊到充／放电单价。核对关系为：日前＋日内现金流＝净售电量×放电单价−净购电量×充电单价＋零净头寸现金流。负充电单价表示该组净购电时段整体获得现金流入。','']
    lines+=table(['月份','最终净购电量（MWh）','最终充电单价（欧元/MWh）','最终净售电量（MWh）','最终放电单价（欧元/MWh）','零净头寸价差现金（欧元）'],
        ['net_charge_mwh','net_charge_price_eur_per_mwh','net_discharge_mwh','net_discharge_price_eur_per_mwh','zero_net_spot_cash_eur'])
    lines+=['#### 2. aFRR容量单价及中标率代理','',
        '分方向以本站申报容量×时长（R×0.25小时）为权重。容量市场均价＝Σ(R×模型输入的每15分钟容量价)÷Σ(R×0.25小时)，统一折算为欧元/(MW·h)；中标率代理＝Σ(R×p×0.25小时)÷Σ(R×0.25小时)，其中p=min(1,系统已分配容量/系统总报价容量)。无申报时段不参与加权。',
        '表中的“中标率”仍是历史系统比例代理，并非本站真实投标成功率。另列代理后有效容量均价＝容量收入÷Σ(R×0.25小时)，便于与报告收入核对；由于价格与p共同变化，不能用“市场均价×平均代理中标率”替代逐时段计算。','']
    lines+=table(['月份','Up容量市场均价（欧元/(MW·h)）','Down容量市场均价（欧元/(MW·h)）','Up中标率代理（%）','Down中标率代理（%）','Up代理后有效均价（欧元/(MW·h)）','Down代理后有效均价（欧元/(MW·h)）'],
        ['up_capacity_market_price_eur_per_mw_h','down_capacity_market_price_eur_per_mw_h','up_award_rate_proxy_pct','down_award_rate_proxy_pct','up_capacity_effective_price_eur_per_mw_h','down_capacity_effective_price_eur_per_mw_h'])
    lines+=['#### 3. aFRR激活电量、时长和价格','',
        '激活电量按Σ(R×α×0.25小时)累计，是相对于基准出力的调节电量，并不等同于电池实际放电量或充电量。模型激活时长按有申报容量时Σ(α×0.25小时)累计，是简化激活路径的小时数，不是实测AGC持续时间；同时列示按100 MW折算的等效满功率小时数＝激活电量÷100 MW。所有时长均为当月累计，不是单次激活平均持续时间。',
        '激活价格按激活MWh加权，表中恢复原市场报价符号（Down价格为账本带符号现金单价的相反数）：上调现金流＝上调电量×Up价格；下调现金流＝−下调电量×Down价格。因此Down价格为负时，下调激活形成正收入。两方向激活电量和现金流均未再乘容量中标率代理p。','',
        '**aFRR Up（上调）**','']
    lines+=table(['月份','Up激活电量（MWh）','Up模型激活时长（h）','Up按100 MW等效小时（h）','Up激活均价（欧元/MWh）'],
        ['up_activation_mwh','up_activation_hours','up_activation_100mw_equivalent_hours','up_activation_market_price_eur_per_mwh'])
    lines+=['**aFRR Down（下调）**','']
    lines+=table(['月份','Down激活电量（MWh）','Down模型激活时长（h）','Down按100 MW等效小时（h）','Down激活均价（欧元/MWh）'],
        ['down_activation_mwh','down_activation_hours','down_activation_100mw_equivalent_hours','down_activation_market_price_eur_per_mwh'])
    lines+=['上述指标仅对已完成结果作账本统计，未重新求解或改动模型假设；官方数据继续沿用本报告所列REE/eSIOS、OMIE归档。已逐时段核对现金、容量系数、激活电量及价格，并从243天实际执行相位独立重构净头寸和激活时长；8个月合计与原报告对应市场现金流一致。原有地域匹配、历史规则切换及持续激活履约等待确认事项仍保留。','',
        '明细见[月度运营指标CSV](monthly_operating_metrics.csv)及[统计口径与核验证据](monthly_operating_metrics_evidence.json)。CSV另保留价格和比率的原始分子、分母及实际物理充放电量，便于复算。','']
    return lines


def export(run,out):
    metrics,evidence=compute(run)
    archived=json.loads((out/'validation_evidence.json').read_text(encoding='utf-8'))['asymmetric_cap100']
    for filename,key in (('solver_input.json','solver_input_sha256'),('result.json','result_sha256'),('summary.json','summary_sha256')):
        assert evidence['source_sha256'][filename]==archived[key],filename
    evidence['matches_archived_run_hashes']=True
    fields=sorted(set().union(*(v.keys() for v in metrics.values())))
    with (out/'monthly_operating_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['month',*fields]);writer.writeheader()
        for month,v in metrics.items():writer.writerow(dict(month=month,**v))
    (out/'monthly_operating_metrics_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
    return render(metrics),evidence


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--run',type=Path,required=True);p.add_argument('--report-dir',type=Path,required=True)
    args=p.parse_args()
    lines,evidence=export(args.run,args.report_dir)
    path=args.report_dir/'测算对比报告.md'
    original=path.read_text(encoding='utf-8')
    assert original.count(MARKER)<=1
    prefix=original.split(MARKER)[0].rstrip()
    path.write_text(prefix+'\n\n'+'\n'.join(lines),encoding='utf-8')
    print(json.dumps({k:v for k,v in evidence.items() if k not in ('metrics','source_sha256')},ensure_ascii=True,indent=2))
    print(json.dumps(evidence['metrics']['TOTAL'],ensure_ascii=True,indent=2))


if __name__=='__main__':main()
