"""50 MW charging / 100 MW discharging / 200 MWh, 80% DA; reuse verified per-MW aFRR exposures."""
import argparse
from collections import defaultdict
import csv
import hashlib
import json
import math
from pathlib import Path

from project.calculate_simple_entsoe_day import da_search, linear_percentile
from project.calculate_simple_market_period import MONEY_KEYS, sha, write_csv


def run(source, basis, output):
    output.mkdir(parents=True, exist_ok=False)
    original = json.loads((basis/'results.json').read_text(encoding='utf-8'))
    market = source/'processed/market_prices_15min.csv'
    assert sha(market) == original['provenance']['source_files'][market.name]
    assert original['configuration']['capacity_bid_up']==original['configuration']['capacity_bid_down']==1
    assert original['configuration']['activation_up_spread']==200 and original['configuration']['activation_down_spread']==0
    assert original['configuration']['efficiency_one_way']==.92
    daily_basis={r['date']:r for r in original['daily_inputs']}
    groups=defaultdict(list)
    with market.open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            groups[row['start_europe_madrid'][:10]].append(row)
    daily=[];schedule=[]
    validation=dict(days=0,slots=0,max_energy_balance_error=0.,max_da_cash_error=0.)
    for date,rows in groups.items():
        old=daily_basis[date]
        prices=[float(r['da_eur_mwh']) for r in rows]
        da=da_search(prices,40,160,.92,discharge_power=80)
        charge,discharge=da['charge_mwh_ac'],da['discharge_mwh_ac']
        cost=-math.fsum(p*c for p,c in zip(prices,charge))
        sales=math.fsum(p*d for p,d in zip(prices,discharge))
        p25,p75=linear_percentile(prices,.25),linear_percentile(prices,.75)
        assert abs(p25-old['da_p25'])<1e-9 and abs(p75-old['da_p75'])<1e-9
        up_mwh=20*old['up_energy_per_mw'];dn_mwh=10*old['down_energy_per_mw']
        result=dict(date=date,month=date[:7],da_charge_power_mw=40,da_discharge_power_mw=80,
            da_energy_mwh=160,afrr_up_mw=20,afrr_down_mw=10,
            da_buy_mwh=math.fsum(charge),da_sell_mwh=math.fsum(discharge),
            da_purchases_eur=cost,da_sales_eur=sales,da_net_eur=cost+sales,
            da_depth=da['depth'],da_p25=p25,da_p75=p75,
            charge_start=rows[da['charge_start_index']]['start_europe_madrid'] if da['depth'] else '',
            discharge_start=rows[da['discharge_start_index']]['start_europe_madrid'] if da['depth'] else '',
            capacity_up_eur=20*old['capacity_up_per_mw'],capacity_down_eur=10*old['capacity_down_per_mw'],
            activation_up_cash_eur=20*old['up_cash_per_mw'],activation_down_cash_eur=10*old['down_cash_per_mw'],
            up_energy_mwh=up_mwh,down_energy_mwh=dn_mwh,
            down_resale_value_eur=dn_mwh*.92**2*p75,
            up_replenishment_cost_eur=-up_mwh/.92**2*p25,
            expected_points=old['expected_points'],up_valid_points=old['up_valid_points'],down_valid_points=old['down_valid_points'])
        result['capacity_total_eur']=result['capacity_up_eur']+result['capacity_down_eur']
        result['activation_cash_eur']=result['activation_up_cash_eur']+result['activation_down_cash_eur']
        result['activation_net_with_value_eur']=math.fsum(result[k] for k in
            ['activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur'])
        result['total_cash_eur']=math.fsum(result[k] for k in ['da_net_eur','capacity_total_eur','activation_cash_eur'])
        result['total_with_value_eur']=math.fsum(result[k] for k in
            ['total_cash_eur','down_resale_value_eur','up_replenishment_cost_eur'])
        # Independent physical/cash checks of the newly selected DA schedule.
        state=0.;ch_indexes=[];dis_indexes=[]
        for i,(row,ch,dis) in enumerate(zip(rows,charge,discharge)):
            state+=ch*.92-dis/.92
            assert ch<=40*.25+1e-9 and dis<=80*.25+1e-9
            assert -1e-7<=state<=160+1e-7 and not(ch>0 and dis>0)
            if ch>0:ch_indexes.append(i)
            if dis>0:dis_indexes.append(i)
            schedule.append(dict(start_utc=row['start_utc'],start_europe_madrid=row['start_europe_madrid'],
                da_price_eur_mwh=prices[i],charge_mwh_ac=ch,discharge_mwh_ac=dis,dc_soc_mwh=state,
                da_native_resolution=row['da_native_resolution']))
        if ch_indexes:
            assert ch_indexes[-1]<dis_indexes[0]
            assert len(ch_indexes)==ch_indexes[-1]-ch_indexes[0]+1
            assert len(dis_indexes)==dis_indexes[-1]-dis_indexes[0]+1
        assert abs(state)<1e-7
        error=abs(result['da_net_eur']-da['profit_eur']);assert error<1e-6
        validation['days']+=1;validation['slots']+=len(rows)
        validation['max_energy_balance_error']=max(validation['max_energy_balance_error'],abs(state))
        validation['max_da_cash_error']=max(validation['max_da_cash_error'],error)
        # aFRR Up is unchanged from previous 80%-DA case, Dn is halved, independently of new DA dispatch.
        previous=next(r for r in original['daily_scenarios'] if r['date']==date and r['da_share']==.8)
        for key in ['capacity_up_eur','activation_up_cash_eur','up_replenishment_cost_eur']:
            assert abs(result[key]-previous[key])<1e-6
        for key in ['capacity_down_eur','activation_down_cash_eur','down_resale_value_eur']:
            assert abs(result[key]-previous[key]/2)<1e-6
        daily.append(result)
    assert validation['days']==518 and validation['slots']==49732
    monthly=[]
    for month in sorted({r['month'] for r in daily}):
        part=[r for r in daily if r['month']==month]
        item=dict(month=month,days=len(part),**{k:math.fsum(r[k] for r in part) for k in MONEY_KEYS})
        for key in ['expected_points','up_valid_points','down_valid_points']:
            item[key]=sum(r[key] for r in part)
        item['up_price_coverage']=item['up_valid_points']/item['expected_points']
        item['down_price_coverage']=item['down_valid_points']/item['expected_points']
        monthly.append(item)
    totals={k:math.fsum(r[k] for r in daily) for k in MONEY_KEYS}
    previous=original['totals'][2]
    comparison={k:dict(previous=previous[k],current=totals[k],difference=totals[k]-previous[k]) for k in MONEY_KEYS}
    write_csv(output/'daily_results.csv',daily);write_csv(output/'monthly_results.csv',monthly)
    write_csv(output/'da_schedule_15min.csv',schedule)
    payload=dict(configuration=dict(charge_power_mw=50,discharge_power_mw=100,dc_energy_mwh=200,da_share=.8,
        da_charge_power_mw=40,da_discharge_power_mw=80,da_energy_mwh=160,
        afrr_up_power_mw=20,afrr_down_power_mw=10,efficiency_one_way=.92,
        capacity_bid_up=1,capacity_bid_down=1,activation_up_spread=200,activation_down_spread=0),
        period=original['period'],daily=daily,monthly=monthly,totals=totals,comparison_to_symmetric_80pct=comparison,
        assumptions=original['assumptions']+[
          'Charge/discharge AC powers are independent physical limits. 80% allocated directionally: DA 40/80 MW, 160 MWh; aFRR Up 20 MW, Dn 10 MW.',
          'New DA windows and 1%-grid depth are searched afresh per day using asymmetric powers, not scaled from the previous symmetric schedule.',
          'Verified native-4s per-MW aFRR price exposures are reused because bids, thresholds, same-quarter DA prices and efficiency are unchanged.'
        ],validation=validation,
        provenance=dict(source_dataset=str(source),prior_calculation=str(basis),
          market_sha256=sha(market),exposure_results_sha256=sha(basis/'results.json'),
          calculator_sha256=sha(Path(__file__)),da_search_sha256=sha(Path(__file__).with_name('calculate_simple_entsoe_day.py'))))
    (output/'results.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(totals=totals,validation=validation,comparison=comparison),ensure_ascii=False,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--source',type=Path,required=True)
    p.add_argument('--basis',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();run(a.source,a.basis,a.output)
