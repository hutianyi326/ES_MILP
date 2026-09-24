"""Versioned nominal calendar and nullable P0 adapter (no raw-file mutation)."""
import csv
import gzip
from datetime import timedelta
from math import isfinite
from pathlib import Path
from .adapter import (IDS, KINDS, CANCEL, MADRID, QH, iso, nominal, budget, digest,
                      QHInput, ContractInput, SyntheticMarketInput)

CALENDAR = {
    'da':(12,0,12,45,True), 'ida1':(15,0,15,20,True),
    'ida2':(22,0,22,20,True), 'ida3':(10,0,10,20,False),
    'capacity':(16,0,16,30,True),
}

def events(day,kind):
    gh,gm,rh,rm,prev=CALENDAR[kind]
    return nominal(day,gh,gm,prev),nominal(day,rh,rm,prev)

def load_award_rates(path):
    """Read a QH/direction proxy table; invalid observations remain null."""
    path = Path(path)
    rates = {}
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            direction = row['direction']
            if direction not in ('up', 'down'):
                raise ValueError('unknown aFRR direction')
            key = (row['qh_start_utc'], direction)
            if key in rates:
                raise ValueError(f'duplicate aFRR award rate: {key}')
            status = row['quality_status']
            value = row['award_rate_proxy']
            if status in ('valid', 'zero_allocated'):
                rate = float(value)
                if not isfinite(rate) or not 0 <= rate <= 1:
                    raise ValueError(f'invalid aFRR award rate: {key}')
            else:
                if value:
                    raise ValueError(f'non-null rate for invalid aFRR observation: {key}')
                rate = None
            rates[key] = dict(rate=rate, status=status,
                              offer_mw=row['offer_mw'], allocated_mw=row['allocated_mw'])
    return rates


def prepare(bundle, execution_end, *, formal_budget=None, budget_source='formal_valid_mask', award_rates=None):
    """The bundle grid includes one extra local day, including null tail rows."""
    start=min(bundle.grid);rows=[];qhs=[];inactive=set();valid_points=set()
    for t in sorted(bundle.grid):
        day=t.astimezone(MADRID).date();gate,release=events(day,'capacity')
        vals={i:next(iter(bundle.values[i].get(t,()))) if len(bundle.values[i].get(t,()))==1 else None for i in IDS}
        reasons=[];required=[];spot={}
        if gate>=start:
            required=list(IDS)
            for i in IDS:
                if vals[i] is None or not isfinite(vals[i]):reasons.append(f'{i}:missing_or_invalid')
        au=ad=0.
        if gate>=start and not reasons:
            if min(vals[632],vals[633])<=0 or min(vals[680],vals[681])<0:
                reasons.append('invalid_alpha_denominator')
            else:
                au=vals[680]/(vals[632]*.25);ad=vals[681]/(vals[633]*.25)
                if not (0<=au<=1 and 0<=ad<=1 and au+ad<=1):reasons.append('invalid_alpha')
        for k in KINDS:
            if (k=='ida3' and t.astimezone(MADRID).hour<12) or (k,str(day)) in CANCEL:continue
            quote=bundle.spot[k].get(t,set());spot[k]=next(iter(quote)) if len(quote)==1 else None
            if events(day,k)[0]>=start:
                required.append(k)
                if spot[k] is None or not isfinite(spot[k]):reasons.append(k+':missing_or_invalid')
        valid=not reasons
        if valid:valid_points.add(t)
        else:inactive.add(iso(t))
        rate_up = award_rates.get((iso(t), 'up')) if award_rates is not None else None
        rate_down = award_rates.get((iso(t), 'down')) if award_rates is not None else None
        row=dict(qh_id=iso(t),raw_values=vals,spot=spot,required=required,reasons=reasons,valid=valid)
        if award_rates is not None:
            row.update(award_rate_up=rate_up,award_rate_down=rate_down)
        rows.append(row)
        def price(i):
            return float(vals[i]) if valid and gate>=start else 0.
        qhs.append(QHInput(iso(t),t,t+QH,'continuous',day.year,
            au if valid else 0.,ad if valid else 0.,price(2130),price(634),price(682),-price(683),gate,release,
            afrr_award_rate_up=1.0 if award_rates is None else rate_up['rate'] if rate_up else None,
            afrr_award_rate_down=1.0 if award_rates is None else rate_down['rate'] if rate_down else None))
    contracts=[]
    for cid,c in sorted(bundle.contracts.items()):
        if not set(c['slots'])<=bundle.grid:continue  # never truncate products
        gate,release=events(c['day'],c['kind'])
        prices=c['prices'];price=next(iter(prices)) if len(prices)==1 else None
        if price is None or not isfinite(price):
            # Missing closed price has no cash relevance. Open products must be disabled.
            if gate>=start:
                inactive.update(iso(t) for t in c['slots'])
                for r in rows:
                    if r['qh_id'] in {iso(t) for t in c['slots']}:
                        r['valid']=False;r['reasons'].append('invalid_contract_price')
            price=0.
        contracts.append(ContractInput(cid,'DA' if c['kind']=='da' else 'IDA',gate,release,
            c['slots'][0],c['slots'][-1]+QH,float(price),{iso(t):1. for t in c['slots']}))
    valid_points={t for t in valid_points if iso(t) not in inactive}
    formal={t for t in valid_points if t<execution_end}
    computed=budget(formal)
    formal_years={q.madrid_year for q in qhs if q.start_utc<execution_end}
    if formal_budget is not None and set(formal_budget)!=formal_years:
        raise ValueError('explicit formal budget must cover exactly formal years')
    limits={y:float(formal_budget[y]) if formal_budget is not None else computed.get(y,0.) for y in formal_years}
    manifests={y:dict(kind='formal',value=v,source=budget_source,
        valid_qh=sum(t.astimezone(MADRID).year==y for t in formal),
        interval=[iso(start),iso(execution_end)],mask_hash=digest([iso(t) for t in sorted(formal)])) for y,v in limits.items()}
    for y in {q.madrid_year for q in qhs}-formal_years:
        points={t for t in valid_points if t.astimezone(MADRID).year==y}
        limits[y]=budget(points).get(y,0.)
        manifests[y]=dict(kind='lookahead_only',value=limits[y],source='600_effective_local_days',
            valid_qh=len(points),interval=[iso(execution_end),iso(max(bundle.grid)+QH)],mask_hash=digest([iso(t) for t in sorted(points)]))
    provenance=digest(dict(rows=rows,calendar=CALENDAR,budget=manifests))
    inp=SyntheticMarketInput(tuple(qhs),tuple(contracts),annual_efc_budget=limits,
        input_id='ES_HISTORICAL_CONDITIONAL_P0_'+provenance,data_scope='historical_conditional',research_provenance=provenance)
    gaps=[];qmap=inp.qh_by_id
    for r in rows:
        if r['qh_id'] not in inactive:continue
        if not gaps or gaps[-1]['end']!=r['qh_id']:
            gaps.append(dict(gap_id=f'gap-{len(gaps)+1}',start=r['qh_id'],end=r['qh_id'],qh=0,fields=[]))
        g=gaps[-1];q=qmap[r['qh_id']];g['end']=iso(q.end_utc);g['qh']+=1
        g['fields']=sorted(set(g['fields'])|set(r['reasons']));r['gap_id']=g['gap_id']
    evidence=dict(rows=rows,gaps=gaps,calendar=CALENDAR,calendar_status='cap_old_assumed',
                  headroom_status='stage1_full_fill_from_gct',source_hash=digest(bundle.sources))
    return inp,inactive,evidence,manifests
