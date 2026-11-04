"""Historical simple-model revenue: reusable daily exposures, three DA allocations."""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
from collections import defaultdict

from project.calculate_simple_entsoe_day import da_search, linear_percentile

POWER = 100.0
ENERGY = 200.0
ETA = .92
SCENARIOS = [('100% DA', 1.0), ('50% DA', .5), ('80% DA', .8)]
MONEY_KEYS = ['da_sales_eur', 'da_purchases_eur', 'da_net_eur',
              'capacity_up_eur', 'capacity_down_eur', 'capacity_total_eur',
              'activation_up_cash_eur', 'activation_down_cash_eur', 'activation_cash_eur',
              'down_resale_value_eur', 'up_replenishment_cost_eur',
              'activation_net_with_value_eur', 'total_cash_eur', 'total_with_value_eur']


def exposures(prices, da, capacity, *, up):
    """Per bid MW; capacity >1, Up spread >200 / Dn spread >0, native 4 seconds."""
    valid = [p for p in prices if p is not None]
    eligible = [p for p in valid if capacity > 1 and ((p-da > 200) if up else (da-p > 0))]
    return dict(valid_points=len(valid), active_points=len(eligible),
                energy_per_mw=len(eligible)/900,
                cash_per_mw=math.fsum(eligible)/900*(1 if up else -1))


def daily_case(day, label, share):
    """Scaling is exact: DA power and DC energy both scale by the same allocation."""
    af_power = POWER*(1-share)
    r = dict(scenario=label, da_share=share, date=day['date'], month=day['month'],
             da_power_mw=POWER*share, da_energy_mwh=ENERGY*share, afrr_power_each_mw=af_power)
    r.update(da_sales_eur=day['da_sales_full_eur']*share,
             da_purchases_eur=day['da_purchases_full_eur']*share,
             capacity_up_eur=day['capacity_up_per_mw']*af_power,
             capacity_down_eur=day['capacity_down_per_mw']*af_power,
             activation_up_cash_eur=day['up_cash_per_mw']*af_power,
             activation_down_cash_eur=day['down_cash_per_mw']*af_power,
             up_energy_mwh=day['up_energy_per_mw']*af_power,
             down_energy_mwh=day['down_energy_per_mw']*af_power,
             da_buy_mwh=day['da_buy_full_mwh']*share,
             da_sell_mwh=day['da_sell_full_mwh']*share)
    r['down_resale_value_eur'] = r['down_energy_mwh']*ETA**2*day['da_p75']
    r['up_replenishment_cost_eur'] = -r['up_energy_mwh']/ETA**2*day['da_p25']
    r['da_net_eur'] = r['da_sales_eur']+r['da_purchases_eur']
    r['capacity_total_eur'] = r['capacity_up_eur']+r['capacity_down_eur']
    r['activation_cash_eur'] = r['activation_up_cash_eur']+r['activation_down_cash_eur']
    r['activation_net_with_value_eur'] = math.fsum(r[k] for k in
        ['activation_cash_eur', 'down_resale_value_eur', 'up_replenishment_cost_eur'])
    r['total_cash_eur'] = math.fsum(r[k] for k in ['da_net_eur', 'capacity_total_eur', 'activation_cash_eur'])
    r['total_with_value_eur'] = math.fsum(r[k] for k in
        ['total_cash_eur', 'down_resale_value_eur', 'up_replenishment_cost_eur'])
    for k in ['expected_points', 'up_valid_points', 'down_valid_points', 'up_active_points', 'down_active_points']:
        r[k] = day[k]
    return r


def write_csv(path, rows):
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def run(source, output):
    output.mkdir(parents=True, exist_ok=False)
    qhs = []
    days_qh = defaultdict(list)
    with (source/'processed/market_prices_15min.csv').open(encoding='utf-8-sig', newline='') as f:
        for raw in csv.DictReader(f):
            row = dict(raw)
            for k in ['da_eur_mwh', 'capacity_up_eur_mw_qh', 'capacity_down_eur_mw_qh']:
                row[k] = float(row[k])
                assert math.isfinite(row[k])
            row['date'] = row['start_europe_madrid'][:10]
            row['month'] = row['date'][:7]
            row['up_prices'], row['down_prices'] = [], []
            days_qh[row['date']].append(row)
            qhs.append(row)
    assert len(days_qh) == 518 and len(qhs) == 49732
    daily = []
    for date, rows in days_qh.items():
        prices = [r['da_eur_mwh'] for r in rows]
        result = da_search(prices, POWER, ENERGY, ETA)
        charges, discharges = result['charge_mwh_ac'], result['discharge_mwh_ac']
        d = dict(date=date, month=date[:7], qh_count=len(rows), expected_points=len(rows)*225,
                 da_p25=linear_percentile(prices, .25), da_p75=linear_percentile(prices, .75),
                 da_buy_full_mwh=math.fsum(charges), da_sell_full_mwh=math.fsum(discharges),
                 da_purchases_full_eur=-math.fsum(p*c for p, c in zip(prices, charges)),
                 da_sales_full_eur=math.fsum(p*x for p, x in zip(prices, discharges)),
                 da_cycle_depth=result['depth'],
                 charge_start=rows[result['charge_start_index']]['start_europe_madrid'] if result['depth'] else '',
                 discharge_start=rows[result['discharge_start_index']]['start_europe_madrid'] if result['depth'] else '',
                 capacity_up_per_mw=math.fsum(r['capacity_up_eur_mw_qh'] for r in rows if r['capacity_up_eur_mw_qh']>1),
                 capacity_down_per_mw=math.fsum(r['capacity_down_eur_mw_qh'] for r in rows if r['capacity_down_eur_mw_qh']>1),
                 capacity_up_awarded_qh=sum(r['capacity_up_eur_mw_qh']>1 for r in rows),
                 capacity_down_awarded_qh=sum(r['capacity_down_eur_mw_qh']>1 for r in rows))
        assert abs(d['da_sales_full_eur']+d['da_purchases_full_eur']-result['profit_eur'])<1e-6
        for r, ch, dis in zip(rows, charges, discharges):
            r['da_charge_full_mwh'], r['da_discharge_full_mwh'] = ch, dis
        daily.append(d)
    print(json.dumps(dict(stage='DA complete', days=len(daily)), ensure_ascii=False), flush=True)

    # Prices remain raw in the immutable source package. Aggregate each native 4s point only after screening.
    day_offsets = defaultdict(int)
    files = sorted((source/'processed/prices_4s').glob('*.csv.gz'))
    row_total = 0
    for path in files:
        with gzip.open(path, 'rt', encoding='utf-8-sig', newline='') as f:
            reader = csv.reader(f)
            header = next(reader)
            ix = {key: header.index(key) for key in ['start_utc', 'start_europe_madrid', 'activation_up_eur_mwh', 'activation_down_eur_mwh']}
            for raw in reader:
                date = raw[ix['start_europe_madrid']][:10]
                offset = day_offsets[date]
                q = days_qh[date][offset//225]
                if offset%225 == 0:
                    assert raw[ix['start_utc']] == q['start_utc']
                for direction in ['up', 'down']:
                    value = raw[ix[f'activation_{direction}_eur_mwh']]
                    q[f'{direction}_prices'].append(float(value) if value else None)
                if offset%225 == 224:
                    for direction in ['up', 'down']:
                        a = exposures(q.pop(f'{direction}_prices'), q['da_eur_mwh'],
                                      q[f'capacity_{direction}_eur_mw_qh'], up=direction=='up')
                        assert a['valid_points']*4 == int(q[f'activation_{direction}_valid_seconds'])
                        q.update({f'{direction}_{key}': value for key, value in a.items()})
                day_offsets[date] += 1
                row_total += 1
        print(json.dumps(dict(stage='4s read', month=path.name[:7], cumulative_rows=row_total)), flush=True)
    assert row_total == 11189700

    qh_export = []
    for d in daily:
        rows = days_qh[d['date']]
        assert day_offsets[d['date']] == d['expected_points']
        for r in rows:
            qh_export.append({k: v for k, v in r.items() if k not in
                ['activation_up_mean_eur_mwh','activation_down_mean_eur_mwh']})
        for direction in ['up', 'down']:
            for key in ['valid_points', 'active_points', 'energy_per_mw', 'cash_per_mw']:
                d[f'{direction}_{key}'] = math.fsum(r[f'{direction}_{key}'] for r in rows)
            d[f'{direction}_valid_points'] = int(d[f'{direction}_valid_points'])
            d[f'{direction}_active_points'] = int(d[f'{direction}_active_points'])

    results = [daily_case(d, label, share) for label, share in SCENARIOS for d in daily]
    monthly = []
    totals = []
    for label, share in SCENARIOS:
        group = [r for r in results if r['scenario']==label]
        for month in sorted({r['month'] for r in group}):
            rows = [r for r in group if r['month']==month]
            out = dict(scenario=label, da_share=share, month=month, days=len(rows))
            out.update({k: math.fsum(r[k] for r in rows) for k in MONEY_KEYS})
            for key in ['expected_points', 'up_valid_points', 'down_valid_points']:
                out[key] = sum(r[key] for r in rows)
            out['up_price_coverage'] = out['up_valid_points']/out['expected_points']
            out['down_price_coverage'] = out['down_valid_points']/out['expected_points']
            monthly.append(out)
        totals.append(dict(scenario=label, da_share=share, days=len(group),
            **{k: math.fsum(r[k] for r in group) for k in MONEY_KEYS}))
    jan = next(r for r in results if r['scenario']=='50% DA' and r['date']=='2026-01-01')
    assert abs(jan['total_with_value_eur']-91414.92750724638)<1e-6, jan
    assert all(r[k]==0 for r in results if r['da_share']==1 for k in
        ['capacity_total_eur','activation_cash_eur','down_resale_value_eur','up_replenishment_cost_eur'])
    source_summary = json.loads((source/'summary.json').read_text(encoding='utf-8'))
    for direction in ['up', 'down']:
        name = 'activation_up' if direction=='up' else 'activation_down'
        assert sum(d[f'{direction}_valid_points'] for d in daily) == source_summary['totals'][name]['valid']

    write_csv(output/'daily_inputs.csv', daily)
    write_csv(output/'daily_scenarios.csv', results)
    write_csv(output/'monthly_scenarios.csv', monthly)
    write_csv(output/'quarter_hour_calculation_basis.csv', qh_export)
    payload = dict(configuration=dict(ac_power_mw=POWER, dc_energy_mwh=ENERGY, efficiency_one_way=ETA,
        capacity_bid_up=1, capacity_bid_down=1, activation_up_spread=200, activation_down_spread=0,
        scenarios=[dict(label=s, da_share=v) for s,v in SCENARIOS]),
        period=dict(start='2025-06-01', end_inclusive='2026-10-31', timezone='Europe/Madrid',
                    days=518, qh_rows=len(qhs), rows_4s=row_total),
        daily_inputs=daily, daily_scenarios=results, monthly=monthly, totals=totals,
        assumptions=[
          'Historical perfect-information DA search: at most one contiguous charge then discharge per local day; depth grid 1%; initial/final usable DC energy zero.',
          'DA power and energy scale together; schedule and depth invariant to DA allocation. 100% DA computes zero aFRR without invoking a zero-power DA search.',
          'Capacity >1 EUR/MW/QH: full remaining power awarded independently Up/Dn; no partial award; raw capacity EUR/MW/QH is not multiplied by .25 again.',
          'Native 4s: Up price minus same-quarter DA >200; same-quarter DA minus Dn price >0; trigger power equals awarded MW.',
          'Missing activation prices excluded from known-part sums, never zero-filled or inferred to be dispatch-off; coverage retained.',
          'aFRR has no SOC/exclusivity/restoration chronology limits. Up/Dn screened independently; no actual dispatch commands used.',
          'Dn resale uses daily DA P75 times acquired AC MWh times .92 squared; Up replenishment is minus daily P25 times sold AC MWh divided by .92 squared.',
          'Percentiles use all local-day QH slots and inclusive linear interpolation. Future values are hypothetical marks, no actual subsequent trade.',
          'Early hourly DA repeated only within the original delivery hour, marked PT60M in quarter-hour calculation basis.',
          'No taxes, network/market fees, degradation, investment or operating costs. Totals are gross simulated revenue with hypothetical valuation, not audited profit.'
        ], checks=dict(jan_20260101_50pct_reproduced_eur=jan['total_with_value_eur'],
                       pure_da_afrr_zero=True, source_coverage_reconciled=True),
        provenance=dict(source_package=str(source), source_summary_sha256=sha(source/'summary.json'),
                        source_files={p.name:sha(p) for p in [source/'processed/market_prices_15min.csv', *files]},
                        calculator_sha256=sha(Path(__file__))))
    (output/'results.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(totals=totals, checks=payload['checks']), ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.source, args.output)
