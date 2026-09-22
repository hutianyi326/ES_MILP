"""Read-only raw adapter with explicit assumptions and immutable provenance."""
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from calendar import isleap
from pathlib import Path
import hashlib
import json
import math
import re
from importlib.metadata import version

from countries.ES.audit_pi_candidate_20260920 import parse_response, MADRID, iso
from project.es_joint_gate_audit_20260920 import CANCEL, IDS, KINDS, spans
from src.data_ingestion.es.omie import parse_omie, standardize_omie_rows
from src.es_synthetic_market.core import QHInput, ContractInput, SyntheticMarketInput, _required_madrid_timezone

QH = timedelta(minutes=15)
UTC = timezone.utc
VERSION = 'ES_CONDITIONAL_ADAPTER_1'
UNITS = {632:'Potencia',633:'Potencia',634:'Precio €/MW',2130:'Precio €/MW',
         680:'Energía',681:'Energía',682:'Precio €/MWh',683:'Precio €/MWh'}
UP = {632,2130,680,682}
ASSUMPTIONS = ['C01_energy_MWh','C02_system_proxy','C03_energy_and_energy_price_same_interval',
               'C04_nominal_no_delay','C05_no_fill_no_clip','capacity_labels_are_starts',
               'public_price_proxy_not_BSP_settlement','no_initial_commitments']

def digest(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,default=str,ensure_ascii=False,
                                    separators=(',',':')).encode()).hexdigest()

def dependency_hashes():
    root=Path(__file__).resolve().parents[2]
    paths=['countries/ES/audit_pi_candidate_20260920.py','project/es_joint_gate_audit_20260920.py',
           'src/data_ingestion/es/omie.py','src/data_ingestion/es/common.py',
           'model/es_conditional_adapter_spec_20260920.md']
    paths += [p.relative_to(root).as_posix() for folder in ('src/es_historical_conditional','src/es_synthetic_market')
              for p in (root/folder).glob('*.py')]
    return {p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in sorted(paths)}

def grid_between(start, end):
    if start.tzinfo is None or end.tzinfo is None or start >= end:
        raise ValueError('aware increasing bounds required')
    a,b=start.astimezone(UTC),end.astimezone(UTC)
    if any(t.minute%15 or t.second or t.microsecond for t in (a,b)):
        raise ValueError('quarter aligned bounds required')
    return {a+QH*i for i in range(int((b-a)/QH))}

def nominal(day, hour, minute=0, previous=False):
    if previous: day -= timedelta(days=1)
    return datetime(day.year,day.month,day.day,hour,minute,tzinfo=MADRID).astimezone(UTC)

def budget(points):
    byday=Counter(t.astimezone(MADRID).date() for t in points)
    result=defaultdict(float)
    for day,n in byday.items():
        h=(nominal(day+timedelta(days=1),0)-nominal(day,0)).total_seconds()/3600
        result[day.year] += 600*(n*.25/h)/(366 if isleap(day.year) else 365)
    return dict(result)

def complete_contracts(points, contracts):
    points=set(points)
    while True:
        remove=set()
        for c in contracts.values():
            slots=set(c['slots']); overlap=slots & points
            if overlap and overlap != slots: remove |= overlap
        if not remove: return points
        points -= remove

@dataclass
class RawBundle:
    grid: set
    values: dict
    refs: dict
    contracts: dict
    spot: dict
    sources: list
    rejected: list

def load_raw(root, start, end):
    """Read only known official file names; no API, credential or raw writes."""
    _required_madrid_timezone()
    root=Path(root); grid=grid_between(start,end)
    halo=grid | {max(grid)+QH}
    values={i:defaultdict(set) for i in IDS}; refs={i:defaultdict(list) for i in IDS}
    sources=[]; rejected=[]
    for p in sorted((root/'raw/ES/esios').rglob('fetch_*.json')):
        if p.stem not in {f'fetch_{i}' for i in IDS}: continue
        iid=int(p.stem.split('_')[1]); ind,rows,stats,sha,size=parse_response(p,iid,halo)
        mp=p.with_suffix('.json.meta.json')
        try: meta=json.loads(mp.read_text(encoding='utf-8'))
        except (OSError,ValueError): meta={}
        rec=dict(path=p.relative_to(root).as_posix(),sha256=sha,bytes=size,indicator=iid,
                 metadata_sha256=hashlib.sha256(mp.read_bytes()).hexdigest() if mp.exists() else None,
                 retrieved_at=meta.get('retrieved_at'),values_updated_at=ind.get('values_updated_at'),
                 parse_rejections=dict(stats),unit=UNITS[iid])
        source_id=len(sources); sources.append(rec)
        direction='subir' if iid in UP else 'bajar'
        valid_meta=(str(ind.get('id'))==str(iid) and direction in str(ind.get('name','')).lower()
                    and UNITS[iid] in [v.get('name') for v in ind.get('magnitud',[])]
                    and any(v.get('id')==218 for v in ind.get('tiempo',[])))
        if not valid_meta or meta.get('http_status') != 200 or meta.get('sha256') != sha:
            rec['rejected']='metadata_unit_direction_http_or_hash'; rejected.append(rec);continue
        for t,v in rows:
            values[iid][t].add(v); refs[iid][t].append(source_id)
    contracts={}; spot={k:defaultdict(set) for k in KINDS}
    first=min(grid).astimezone(MADRID).date(); last=max(grid).astimezone(MADRID).date()
    for p in sorted((root/'raw/ES/omie').rglob('*')):
        m=re.fullmatch(r'marginal(pdbc|pibc)_(\d{8})(\d{2})?\.(\d+)',p.name)
        if not m or not p.is_file(): continue
        day=datetime.strptime(m[2],'%Y%m%d').date()
        if not first <= day <= last: continue
        k='da' if m[1]=='pdbc' else {'01':'ida1','02':'ida2','03':'ida3'}.get(m[3])
        if k is None: continue
        raw=p.read_bytes(); rec=dict(path=p.relative_to(root).as_posix(),
            sha256=hashlib.sha256(raw).hexdigest(),bytes=len(raw),kind=k,delivery_day=str(day),version=int(m[4]))
        sid=len(sources);sources.append(rec)
        try:
            rows=standardize_omie_rows(parse_omie(raw,k,str(day)),str(day)); pending=[]
            for r in rows:
                if (r['year'],r['month'],r['day'])!=(day.year,day.month,day.day):raise ValueError('wrong date')
                t=datetime.fromisoformat(r['utc_time'].replace('Z','+00:00')).astimezone(UTC)
                gran=r['period_granularity']; expected='hour' if day < datetime.strptime('2025-10-01' if k=='da' else '2025-03-19','%Y-%m-%d').date() else '15min'
                if gran != expected: raise ValueError('product version mismatch')
                slots=tuple(t+QH*j for j in range(4 if gran=='hour' else 1))
                if any(x.astimezone(MADRID).date()!=day or x.minute%15 for x in slots):raise ValueError('bad interval')
                if k=='ida3' and any(x.astimezone(MADRID).hour<12 for x in slots):raise ValueError('IDA3 range')
                price=float(r['price_es_eur_mwh'])
                if not math.isfinite(price):raise ValueError('nonfinite')
                pending.append((slots,price,gran))
            if not pending: rec['empty']=True
            for slots,price,gran in pending:
                cid=f'{k}:{day}:{iso(slots[0])}:{gran}'
                c=contracts.setdefault(cid,dict(kind=k,day=day,slots=slots,prices=set(),source_ids=[]))
                c['prices'].add(price);c['source_ids'].append(sid)
                for t in slots:spot[k][t].add(price)
        except (ValueError,TypeError,KeyError,OverflowError):
            rec['rejected']='OMIE_parse_or_product_version'; rejected.append(rec)
    for k in KINDS:
        for t in spot[k]:
            if (k,str(t.astimezone(MADRID).date())) in CANCEL:
                raise ValueError('cancelled session has price records')
    return RawBundle(grid,values,refs,contracts,spot,sources,rejected)

def scenario(bundle, timing, timetable, restrict=None):
    if timing not in ('ts_start','ts_end') or timetable not in ('cap_old','cap_new'):
        raise ValueError('unknown scenario')
    mapped={};excluded={}; grid=bundle.grid
    for t in sorted(grid):
        v={}; provenance={}; reasons=[]
        for i in IDS:
            raw_t=t+QH if timing=='ts_end' and i in (680,681,682,683) else t
            vals=bundle.values[i].get(raw_t,set())
            if len(vals)!=1:reasons.append(f'{i}:missing_or_conflicting');continue
            v[i]=next(iter(vals));provenance[str(i)]=dict(raw_timestamp=iso(raw_t),
                mapped_start=iso(t),value=v[i],source_ids=bundle.refs[i][raw_t],unit=UNITS[i])
        for k in KINDS:
            if k=='ida3' and t.astimezone(MADRID).hour<12:continue
            if (k,str(t.astimezone(MADRID).date())) in CANCEL:continue
            if len(bundle.spot[k].get(t,set()))!=1:reasons.append(k+':missing_or_conflicting')
        if len(v)==8:
            if min(v[632],v[633])<=0 or min(v[680],v[681])<0: reasons.append('invalid_energy_or_denominator')
            else:
                au,ad=v[680]/(v[632]*.25),v[681]/(v[633]*.25)
                if not (0<=au<=1 and 0<=ad<=1 and au+ad<=1): reasons.append('invalid_alpha')
        if reasons:excluded[iso(t)]=reasons
        else:mapped[t]=dict(values=v,provenance=provenance,alpha_up=au,alpha_down=ad)
    points=set(mapped)
    if restrict is not None: points &= set(restrict)
    complete=complete_contracts(points,bundle.contracts)
    for t in points-complete:excluded[iso(t)]=['incomplete_contract_boundary']
    if restrict is not None:
        for t in set(mapped)-set(restrict):excluded[iso(t)]=['outside_comparison_or_trial_mask']
    series={t:mapped[t] for t in sorted(complete)}
    manifest=dict(adapter_version=VERSION,input_scope='historical_conditional',
        timing=timing,timetable=timetable,assumptions=ASSUMPTIONS,event_mode='nominal_no_delay',
        actual_event_utc=None,formal_approved=False,perfect_information_override=True,
        target_start=iso(min(grid)),target_end_exclusive=iso(max(grid)+QH),
        sources=bundle.sources,rejected_files=bundle.rejected,
        cancellations=[dict(kind=k,day=d,evidence_kind=e[0],url=e[1]) for (k,d),e in CANCEL.items()],
        selected_qh=len(complete),segments=spans(complete),annual_efc_budget=budget(complete),
        excluded=excluded,mask_hash=digest([iso(t) for t in sorted(complete)]),
        values_hash=digest({iso(t):v for t,v in series.items()}),tzdata=version('tzdata'),
        dependency_hashes=dependency_hashes())
    return dict(series=series,manifest=manifest,manifest_hash=digest(manifest))

def four_scenarios(bundle, common=False, restrict=None):
    cases={(t,c):scenario(bundle,t,c,restrict) for t in ('ts_start','ts_end') for c in ('cap_old','cap_new')}
    if common:
        points=set.intersection(*(set(v['series']) for v in cases.values()))
        points=complete_contracts(points,bundle.contracts)
        cases={key:scenario(bundle,*key,restrict=points) for key in cases}
    return cases

def model_input(bundle, case):
    series=case['series'];m=case['manifest']
    if not series:raise ValueError('no eligible conditional QH')
    points=set(series);qhs=[];segment=-1;previous=None
    for t,row in series.items():
        if previous is None or t != previous+QH:segment+=1
        previous=t;v=row['values'];day=t.astimezone(MADRID).date()
        h=16 if m['timetable']=='cap_old' else 17
        qhs.append(QHInput(iso(t),t,t+QH,f'S{segment}',day.year,row['alpha_up'],row['alpha_down'],
            v[2130],v[634],v[682],-v[683],nominal(day,h,previous=True),nominal(day,h,30,previous=True)))
    contracts=[]
    for cid,c in sorted(bundle.contracts.items()):
        if not set(c['slots'])<=points:continue
        if len(c['prices'])!=1:raise ValueError('conflicting contract in selected mask')
        k,day=c['kind'],c['day']
        gh,gm,rh,rm,prev={'da':(12,0,12,45,True),'ida1':(15,0,15,20,True),
                          'ida2':(22,0,22,20,True),'ida3':(10,0,10,20,False)}[k]
        contracts.append(ContractInput(cid,'DA' if k=='da' else 'IDA',nominal(day,gh,gm,prev),
            nominal(day,rh,rm,prev),c['slots'][0],c['slots'][-1]+QH,next(iter(c['prices'])),
            {iso(t):1.0 for t in c['slots']}))
    return SyntheticMarketInput(qhs=tuple(qhs),contracts=tuple(contracts),annual_efc_budget=budget(points),
        input_id='ES_HISTORICAL_CONDITIONAL_'+case['manifest_hash'],
        data_scope='historical_conditional',research_provenance=case['manifest_hash'])

def evidence_payload(bundle, case):
    series = case['series']
    series_keys = set(series)
    return dict(manifest=case['manifest'],manifest_hash=case['manifest_hash'],
        rows=[dict(qh=iso(t),**v) for t,v in series.items()],
        contracts=[dict(contract_id=k,kind=c['kind'],day=str(c['day']),
            slots=[iso(t) for t in c['slots']],prices=sorted(c['prices']),source_ids=c['source_ids'])
            for k,c in sorted(bundle.contracts.items()) if set(c['slots'])<=series_keys])

def save_new(path,payload):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(payload,f,default=str,ensure_ascii=False,indent=2)
