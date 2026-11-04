"""Non-MILP daily window arbitrage and all-or-nothing aFRR price screening."""
import argparse
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
from zoneinfo import ZoneInfo

TZ = ZoneInfo('Europe/Madrid')


def expand(rows, start, count, seconds, key, select=lambda row: True):
    values = [None]*count
    seen = set()
    for row in rows:
        if not select(row):
            continue
        a = datetime.fromisoformat(row['start'])
        b = datetime.fromisoformat(row['end'])
        left, right = (a-start).total_seconds()/seconds, (b-start).total_seconds()/seconds
        if not left.is_integer() or not right.is_integer():
            raise ValueError('unaligned interval')
        for i in range(max(0, int(left)), min(count, int(right))):
            if i in seen:
                raise ValueError('overlapping series')
            seen.add(i)
            raw = row['point'].get(key)
            if raw is not None:
                value = float(raw)
                if not math.isfinite(value):
                    raise ValueError('nonfinite price')
                values[i] = value
    return values


def profile(energy, power):
    full = power*.25
    n = int(math.ceil(energy/full-1e-12))
    return [full]*(n-1)+[energy-full*(n-1)]


def da_search(prices, power, energy, eta=.92, *, discharge_power=None):
    """One chronological contiguous cycle; search depths in 1% increments."""
    if any(p is None for p in prices):
        raise ValueError('DA price coverage incomplete')
    discharge_power = power if discharge_power is None else discharge_power
    if min(power, discharge_power, energy) <= 0 or not 0 < eta <= 1:
        raise ValueError('positive powers/energy and efficiency in (0,1] required')
    best = dict(profit_eur=0., charge_mwh_ac=[0.]*len(prices), discharge_mwh_ac=[0.]*len(prices), depth=0.)
    for percent in range(1, 101):
        depth = energy*percent/100
        charge, discharge = profile(depth/eta, power), profile(depth*eta, discharge_power)
        nc, nd = len(charge), len(discharge)
        costs = [sum(p*q for p, q in zip(prices[i:i+nc], charge)) for i in range(len(prices)-nc+1)]
        revenues = [sum(p*q for p, q in zip(prices[i:i+nd], discharge)) for i in range(len(prices)-nd+1)]
        for c in range(len(prices)-nc-nd+1):
            d = max(range(c+nc, len(revenues)), key=revenues.__getitem__)
            profit = revenues[d]-costs[c]
            if profit > best['profit_eur']+1e-9:
                ch, dis = [0.]*len(prices), [0.]*len(prices)
                ch[c:c+nc], dis[d:d+nd] = charge, discharge
                best = dict(profit_eur=profit, charge_cost_eur=costs[c], discharge_income_eur=revenues[d],
                            charge_mwh_ac=ch, discharge_mwh_ac=dis, depth=percent/100,
                            charge_start_index=c, discharge_start_index=d)
    return best


def linear_percentile(prices, probability):
    """Equal-duration DA slots, inclusive linear percentile (index=(n-1)*p)."""
    if not prices or any(v is None or not math.isfinite(v) for v in prices):
        raise ValueError('complete finite DA prices required for percentiles')
    if not 0 <= probability <= 1:
        raise ValueError('probability must be in [0,1]')
    values = sorted(prices)
    position = (len(values)-1)*probability
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo]+(values[hi]-values[lo])*(position-lo)


def activation(price, da, capacity_price, bid, threshold, power, up, *, restoration_price=None):
    if price is None:
        return dict(price_available=False, energy_mwh=0., cash_eur=0., spread_eur=0., efficiency_adjusted_reference_eur=0.,
                    da_restoration_energy_mwh=0., da_restoration_cash_eur=0.)
    spread = price-da if up else da-price
    energy = power*4/3600 if capacity_price > bid and spread > threshold else 0.
    cash = energy*price*(1 if up else -1)
    restoration_energy = energy/.92**2 if up else energy*.92**2
    reference = da if restoration_price is None else restoration_price
    restoration_cash = restoration_energy*reference*(-1 if up else 1)
    adjusted = cash+restoration_cash
    return dict(price_available=True, energy_mwh=energy, cash_eur=cash, spread_eur=energy*spread,
                efficiency_adjusted_reference_eur=adjusted,
                da_restoration_energy_mwh=restoration_energy, da_restoration_cash_eur=restoration_cash)


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--source', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--date', required=True)
    p.add_argument('--da-share', type=float, required=True)
    p.add_argument('--capacity-up-bid', type=float, required=True)
    p.add_argument('--capacity-down-bid', type=float, required=True)
    p.add_argument('--up-spread', type=float, required=True)
    p.add_argument('--down-spread', type=float, required=True)
    p.add_argument('--activation-value-basis',
                   choices=('cash', 'same_qh_da_efficiency', 'daily_da_quantiles_efficiency'),
                   default='daily_da_quantiles_efficiency')
    args = p.parse_args()
    if not 0 < args.da_share < 1:
        p.error('da-share must be in (0,1)')
    args.output.mkdir(parents=True, exist_ok=False)
    start = datetime.fromisoformat(args.date).replace(tzinfo=TZ).astimezone(timezone.utc)
    end = (datetime.fromisoformat(args.date).replace(tzinfo=TZ)+timedelta(days=1)).astimezone(timezone.utc)
    nq = int((end-start).total_seconds()/900)
    def load(label):
        return json.loads((args.source/(label+'.json')).read_text(encoding='utf-8'))['rows']
    da = expand(load('DA'), start, nq, 900, 'price.amount',
                lambda r: r['series'].get('contract_MarketAgreement.type') == 'A01')
    cap, act = {}, {}
    for direction, code in [('up', 'A01'), ('down', 'A02')]:
        select = lambda r, code=code: r['series'].get('flowDirection.direction') == code
        cap[direction] = expand(load('capacity_A01'), start, nq, 900, 'procurement_Price.amount', select)
        act[direction] = expand(load('activation_A67'), start, nq*225, 4, 'activation_Price.amount', select)
        if any(v is None for v in cap[direction]):
            raise ValueError('capacity prices incomplete')
    da_result = da_search(da, 100*args.da_share, 200*args.da_share)
    p25, p75 = linear_percentile(da, .25), linear_percentile(da, .75)
    quantile_valuation = args.activation_value_basis == 'daily_da_quantiles_efficiency'
    activation_keys = ('energy_mwh', 'cash_eur', 'spread_eur', 'efficiency_adjusted_reference_eur',
                       'da_restoration_energy_mwh', 'da_restoration_cash_eur')
    totals = {d: dict(capacity_eur=0., awarded_qh=0, priced_seconds=0, active_seconds=0,
                      **dict.fromkeys(activation_keys, 0.)) for d in cap}
    detail = []
    power = 100*(1-args.da_share)
    for q in range(nq):
        record = dict(start=(start+timedelta(minutes=15*q)).astimezone(TZ).isoformat(),
                      da_price_eur_mwh=da[q], da_charge_mwh=da_result['charge_mwh_ac'][q],
                      da_discharge_mwh=da_result['discharge_mwh_ac'][q])
        for d, bid, threshold in [('up', args.capacity_up_bid, args.up_spread), ('down', args.capacity_down_bid, args.down_spread)]:
            awarded = cap[d][q] > bid
            cap_cash = power*cap[d][q] if awarded else 0.
            totals[d]['capacity_eur'] += cap_cash
            totals[d]['awarded_qh'] += int(awarded)
            qr = dict(capacity_price_eur_mw_qh=cap[d][q], awarded_mw=power if awarded else 0.,
                      capacity_eur=cap_cash, priced_seconds=0, active_seconds=0,
                      da_restoration_price_eur_mwh=(p25 if d == 'up' else p75) if quantile_valuation else da[q],
                      **dict.fromkeys(activation_keys, 0.))
            for i in range(q*225, (q+1)*225):
                a = activation(act[d][i], da[q], cap[d][q], bid, threshold, power, d=='up',
                               restoration_price=qr['da_restoration_price_eur_mwh'])
                qr['priced_seconds'] += 4*int(a['price_available'])
                qr['active_seconds'] += 4*int(a['energy_mwh'] > 0)
                for key in activation_keys:
                    qr[key] += a[key]
            for key in ('priced_seconds', 'active_seconds', *activation_keys):
                totals[d][key] += qr[key]
            record[d] = qr
        detail.append(record)
    capacity = sum(t['capacity_eur'] for t in totals.values())
    summary = dict(date=args.date, timezone='Europe/Madrid', configuration=dict(
        ac_power_mw=100, dc_energy_mwh=200, da_share=args.da_share, efficiency_one_way=.92,
        da_power_mw=100*args.da_share, da_energy_mwh=200*args.da_share, afrr_power_each_direction_mw=power,
        capacity_bid_up=args.capacity_up_bid, capacity_bid_down=args.capacity_down_bid,
        activation_spread_up=args.up_spread, activation_spread_down=args.down_spread),
        assumptions=['DA one contiguous charge followed by one contiguous discharge; initial and final usable energy zero; depth grid 1%',
                     'DA uses allocated rated DC energy, no additional SOC buffer',
                     'capacity price raw EUR/MW/QH; strict >; full award or zero',
                     'aFRR no SOC, replenishment, exclusivity or power ramp limits; directions screened independently',
                     'missing activation price excluded, never zero-filled; totals cover priced intervals only',
                     'spread contribution is DA-reference margin, not reconciled physical cash profit',
                     ('efficiency-adjusted reference uses daily DA P25 for Up replenishment and P75 for Dn resale; no actual restoration schedule'
                      if quantile_valuation else 'efficiency-adjusted reference uses same-QH DA as hypothetical restoration price; no actual restoration schedule'),
                     'activation trigger still compares activation price with same-QH DA, independently of restoration valuation'],
        da=da_result, afrr=totals, activation_revenue_basis=args.activation_value_basis,
        da_percentiles=dict(p25_eur_mwh=p25, p75_eur_mwh=p75, sample_count=len(da),
                            method='linear inclusive: sorted index (n-1)*p; all local-day 15-minute DA slots equally weighted'),
        total_revenue_eur=da_result['profit_eur']+capacity+sum(
            t['cash_eur'] if args.activation_value_basis == 'cash' else t['efficiency_adjusted_reference_eur']
            for t in totals.values()),
        total_with_activation_cash_eur=da_result['profit_eur']+capacity+sum(t['cash_eur'] for t in totals.values()),
        total_with_activation_spread_eur=da_result['profit_eur']+capacity+sum(t['spread_eur'] for t in totals.values()),
        total_with_efficiency_adjusted_reference_eur=da_result['profit_eur']+capacity+sum(t['efficiency_adjusted_reference_eur'] for t in totals.values()),
        provenance={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in args.source.glob('*.json')},
        calculator_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    matrices = {}
    for d in cap:
        for kind, thresholds in [('capacity', list(range(101))), ('activation_price', list(range(0, 1001, 20))),
                                 ('activation_spread', list(range(0, 1001, 20)))]:
            groups = {}
            values = cap[d] if kind == 'capacity' else act[d]
            step = 900 if kind == 'capacity' else 4
            for i, value in enumerate(values):
                group = (start+timedelta(seconds=i*step)).astimezone(TZ).strftime('%Y-%m %H')
                samples = groups.setdefault(group, [])
                if value is None:
                    continue
                if kind == 'activation_spread':
                    value = value-da[i//225] if d == 'up' else da[i//225]-value
                samples.append(value)
            matrices[d+'_'+kind] = dict(thresholds=thresholds, rows=[dict(month_hour=k, valid_samples=len(v),
                exceedance_rates=[sum(x>b for x in v)/len(v) if v else None for b in thresholds]) for k, v in groups.items()])
    for filename, payload in [('summary.json', summary), ('qh_detail.json', detail), ('matrices.json', matrices),
                              ('normalized_prices.json', dict(da=da, capacity=cap, activation=act))]:
        (args.output/filename).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('provenance', 'da')}, ensure_ascii=False, indent=2))
    print('DA', json.dumps(da_result, ensure_ascii=False))


if __name__ == '__main__':
    main()
