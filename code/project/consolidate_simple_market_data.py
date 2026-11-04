"""Immutable ES price collection, gap re-query, and DST-aware merged datasets."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
from datetime import date, datetime, timedelta, timezone
import gzip
import hashlib
from io import BytesIO
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo
from zipfile import ZipFile

if __package__:
    from .fetch_simple_entsoe_day import parse, ES, ENDPOINT
else:
    from fetch_simple_entsoe_day import parse, ES, ENDPOINT

ROOT = Path(__file__).resolve().parents[2]
COUNTRY = ROOT.parents[2]
BASE = ROOT/'input/datasets/ES/market_20250601_20261031_20261103'
OLD = COUNTRY/'project/es_afrr_cbmp_20261101'
START, END = date(2025, 6, 1), date(2026, 11, 1)
TZ = ZoneInfo('Europe/Madrid')
UTC = timezone.utc
FIELDS = ('da', 'capacity_up', 'capacity_down')


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def bounds(day):
    return tuple(datetime.combine(d, datetime.min.time(), TZ).astimezone(UTC) for d in (day, day+timedelta(days=1)))


def days():
    return [START+timedelta(days=i) for i in range((END-START).days)]


def iso(seconds):
    return datetime.fromtimestamp(seconds, UTC).isoformat().replace('+00:00', 'Z')


def month_end(day):
    return date(day.year+1, 1, 1) if day.month == 12 else date(day.year, day.month+1, 1)


class Sources:
    def __init__(self):
        self.path = BASE/'sources.json'
        self.items = load(self.path) if self.path.exists() else {}

    def add(self, path, kind, expected_hash=None, metadata=None):
        original = path.read_bytes()
        body = gzip.decompress(original) if path.suffix == '.gz' else original
        digest = hashlib.sha256(body).hexdigest()
        if expected_hash and digest != expected_hash:
            raise ValueError('archive hash mismatch: '+path.name)
        sid = 's_'+digest[:24]
        if sid not in self.items:
            target = BASE/'raw/reused'/(sid+('.zip.gz' if body[:2] == b'PK' else '.raw.gz'))
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                target.write_bytes(original if path.suffix == '.gz' else gzip.compress(body, compresslevel=1, mtime=0))
            self.items[sid] = dict(kind=kind, original_path=str(path), archive_path=str(target.relative_to(BASE)),
                                   sha256_uncompressed=digest, uncompressed_bytes=len(body), metadata=metadata or {})
        return sid, body

    def save(self):
        dump(self.path, self.items)

    def body(self, sid):
        item = self.items[sid]
        body = gzip.decompress((BASE/item['archive_path']).read_bytes())
        if hashlib.sha256(body).hexdigest() != item['sha256_uncompressed']:
            raise ValueError('source hash changed')
        return body


def put_interval(grid, field, a, b, value, sid, resolution):
    lo = int(bounds(START)[0].timestamp())
    hi = int(bounds(END)[0].timestamp())
    if a % 900 or b % 900:
        raise ValueError('price interval off quarter-hour grid')
    if value is None:
        return
    if not math.isfinite(value):
        raise ValueError('nonfinite source price')
    for t in range(max(a, lo), min(b, hi), 900):
        grid[field][str(t)] = [value, sid, resolution]


def apply_api_qh(grid, body, label, sid):
    docs, rows = parse(body)
    count = Counter()
    for row in rows:
        s = row['series']
        if s.get('currency_Unit.name') != 'EUR':
            raise ValueError('unexpected currency')
        if label == 'da':
            if s.get('contract_MarketAgreement.type') != 'A01':
                continue
            if s.get('in_Domain.mRID') != ES or s.get('out_Domain.mRID') != ES:
                raise ValueError('wrong DA zone')
            field, key = 'da', 'price.amount'
        else:
            if s.get('businessType') != 'B95' or s.get('type_MarketAgreement.type') != 'A01':
                raise ValueError('unexpected capacity product')
            direction = s.get('flowDirection.direction')
            if direction not in ('A01', 'A02'):
                continue
            field, key = 'capacity_'+{'A01':'up', 'A02':'down'}[direction], 'procurement_Price.amount'
        raw = row['point'].get(key)
        if raw is None:
            continue
        a, b = (int(datetime.fromisoformat(row[k]).timestamp()) for k in ('start','end'))
        put_interval(grid, field, a, b, float(raw), sid, row['resolution'])
        count[field] += (b-a)//900
    return dict(count)


def inventory():
    BASE.mkdir(parents=True, exist_ok=False)
    (BASE/'raw/fetched').mkdir(parents=True)
    (BASE/'processed/prices_4s').mkdir(parents=True)
    sources = Sources()
    grid = {k:{} for k in FIELDS}
    sys.path.insert(0, str(COUNTRY))
    from src.data_ingestion.es.omie import parse_omie, standardize_omie_rows
    files = defaultdict(list)
    for path in (COUNTRY/'data/raw/ES/omie').rglob('marginalpdbc_*'):
        match = re.fullmatch(r'marginalpdbc_(\d{8})\.(\d+)', path.name)
        if not match:
            continue
        day = datetime.strptime(match[1], '%Y%m%d').date()
        if START <= day < END:
            files[day].append((int(match[2]), path))
    for day, candidates in sorted(files.items()):
        # Highest numbered official revision first; reject HTML/empty responses.
        for _, path in sorted(candidates, key=lambda v:(v[0],str(v[1])), reverse=True):
            try:
                rows = standardize_omie_rows(parse_omie(path, 'da', str(day)), str(day))
                if not rows:
                    continue
                sid, _ = sources.add(path, 'OMIE_DA')
                for row in rows:
                    if row['price_es_eur_mwh'] is None:
                        continue
                    a = int(datetime.fromisoformat(row['utc_time'].replace('Z','+00:00')).timestamp())
                    step = 900 if row['period_granularity'] == '15min' else 3600
                    put_interval(grid,'da',a,a+step,float(row['price_es_eur_mwh']),sid,'PT15M' if step==900 else 'PT60M')
                break
            except ValueError:
                continue
    print('Reused DA files',len(files),flush=True)
    for iid, field in ((2130,'capacity_up'), (634,'capacity_down')):
        candidates=[]
        for path in (COUNTRY/'data/raw/ES/esios').rglob(f'fetch_{iid}.json'):
            ym=path.relative_to(COUNTRY/'data/raw/ES/esios').parts[0]
            if re.fullmatch(r'\d{4}-\d{2}',ym) and '2025-06'<=ym<='2026-10':
                candidates.append(path)
        for path in sorted(candidates):
            ind=load(path).get('indicator',{})
            values=[v for v in ind.get('values',[]) if v.get('geo_id')==8741 and v.get('value') is not None]
            if not values:
                continue
            sid,_=sources.add(path,'ESIOS_'+str(iid))
            for v in values:
                a=int(datetime.fromisoformat(v['datetime_utc'].replace('Z','+00:00')).timestamp())
                put_interval(grid,field,a,a+900,float(v['value']),sid,'PT15M')
    sources.save()
    old_days={}
    for i,record in enumerate(load(OLD/'manifest.json')):
        d=date.fromisoformat(record['date'])
        if not START<=d<END:
            continue
        path=OLD/'raw'/record.get('raw_file',str(d)+'.xml.gz')
        sid,_=sources.add(path,'ENTSOE_A84_A67_ARCHIVE',record['sha256'],metadata=record)
        old_days[str(d)]={'source_id':sid,'status':record['status']}
        if len(old_days)%100==0:
            print('Reused activation days',len(old_days),flush=True)
    sources.save()
    dump(BASE/'initial_qh.json',grid)
    dump(BASE/'activation_archive.json',old_days)
    tasks=[];missing={}
    for field in FIELDS:
        absent=[]
        for day in days():
            a,b=(int(t.timestamp()) for t in bounds(day))
            absent.extend(t for t in range(a,b,900) if str(t) not in grid[field])
        missing[field]=dict(missing_qh=len(absent),months=sorted({datetime.fromtimestamp(t,UTC).astimezone(TZ).strftime('%Y-%m') for t in absent}))
    for kind, months in [('da',missing['da']['months']),('capacity', sorted(set(missing['capacity_up']['months']+missing['capacity_down']['months'])))]:
        for ym in months:
            day=date.fromisoformat(ym+'-01')
            tasks.append(dict(kind=kind,window=ym,start=str(max(START,day)),end=str(min(END,month_end(day)))))
    # Re-query every day with missing prices, including explicit source nulls.
    # This checks for source revisions; no statistical fill is ever introduced.
    tasks.extend(dict(kind='activation',window=str(day),start=str(day),end=str(day+timedelta(days=1))) for day in days())
    dump(BASE/'tasks.json',tasks)
    dump(BASE/'inventory.json',dict(start=str(START),end_exclusive=str(END),days=len(days()),local_qh={k:len(v) for k,v in grid.items()},missing=missing,activation_archived_days=len(old_days),api_tasks=len(tasks)))
    print(json.dumps(load(BASE/'inventory.json')),flush=True)


def token():
    value = os.environ.get('ENTSOE_SECURITY_TOKEN', '').strip()
    if value:
        return value
    path=COUNTRY.parent/'Country Dashboard/.env'
    for line in path.read_text(encoding='utf-8-sig').splitlines() if path.exists() else []:
        if line.strip().startswith('ENTSOE_SECURITY_TOKEN='):
            return line.split('=',1)[1].strip().strip('\"\'')
    raise RuntimeError('ENTSOE credential unavailable')


def cached_receipt(target):
    paths=[target.with_suffix('.json'),*target.parent.glob(target.name+'_retry_*.json')]
    for saved_path in sorted(paths,reverse=True):
        try:
            saved=load(saved_path)
        except (OSError,ValueError):
            continue
        if saved.get('status') in ('ok','no_data'):
            return saved
    return None


def fetch_request(task, credential):
    target=BASE/'raw/fetched'/f"{task['kind']}_{task['window']}"
    receipt=target.with_suffix('.json')
    saved=cached_receipt(target)
    if saved:
        return saved
    a=datetime.combine(date.fromisoformat(task['start']),datetime.min.time(),TZ).astimezone(UTC)
    b=datetime.combine(date.fromisoformat(task['end']),datetime.min.time(),TZ).astimezone(UTC)
    if task.get('start_utc'):
        a=datetime.fromisoformat(task['start_utc']);b=datetime.fromisoformat(task['end_utc'])
    params=dict(periodStart=a.strftime('%Y%m%d%H%M'),periodEnd=b.strftime('%Y%m%d%H%M'))
    if task['kind']=='da':
        params.update(documentType='A44',in_Domain=ES,out_Domain=ES)
    elif task['kind']=='capacity':
        params.update(documentType='A81',businessType='B95',processType='A51',controlArea_Domain=ES,
                      **{'Type_MarketAgreement.Type':'A01'})
    else:
        params.update(documentType='A84',processType='A67',businessType='A96',controlArea_Domain=ES,Standard_MarketProduct='A01')
    rec=dict(task=task,endpoint=ENDPOINT,params=params,attempts=[],status='error')
    for attempt in range(3):
        record=dict(retrieved_at=datetime.now(UTC).isoformat())
        try:
            try:
                with urlopen(ENDPOINT+'?'+urlencode({**params,'securityToken':credential}),timeout=45) as response:
                    body,status=response.read(),response.status
            except HTTPError as exc:
                body,status=exc.read(),exc.code
            body=body.replace(credential.encode(),b'[REDACTED]')
            digest=hashlib.sha256(body).hexdigest()
            raw=target.parent/(target.name+f'_attempt{attempt+1}_'+digest[:12]+'.raw.gz')
            if not raw.exists():
                raw.write_bytes(gzip.compress(body,compresslevel=1,mtime=0))
            record.update(http_status=status,raw_path=str(raw.relative_to(BASE)),sha256=digest,bytes=len(body))
            docs,rows=parse(body)
            reasons=[d.get('Reason/text','') for d in docs]
            no_data=any('no matching data' in r.lower() for r in reasons)
            if status==200 and (rows or no_data):
                rec.update(status='ok' if rows else 'no_data',raw_path=record['raw_path'],sha256=digest,
                           source_rows=len(rows),resolutions=sorted({r['resolution'] for r in rows}),reasons=reasons)
                rec['attempts'].append(record)
                break
            record['reasons']=reasons
        except Exception as exc:
            record['error_class']=type(exc).__name__
        rec['attempts'].append(record)
        if attempt<2:
            time.sleep(1+attempt)
    if receipt.exists():
        receipt=target.parent/(target.name+'_retry_'+datetime.now(UTC).strftime('%H%M%S')+'.json')
    dump(receipt,rec)
    return rec


def fetch_one(task, credential):
    a=datetime.combine(date.fromisoformat(task['start']),datetime.min.time(),TZ).astimezone(UTC)
    b=datetime.combine(date.fromisoformat(task['end']),datetime.min.time(),TZ).astimezone(UTC)
    if task['kind']!='activation' or b-a<=timedelta(days=1):
        return fetch_request(task,credential)
    target=BASE/'raw/fetched'/f"activation_{task['window']}"
    saved=cached_receipt(target)
    if saved:
        return saved
    # A84 enforces <=24h, but a Madrid autumn market day has 25h.
    # Keep the two original HTTP responses and also a lossless combined ZIP.
    cuts=(a,min(a+timedelta(days=1),b),b)
    children=[]
    for i in range(2):
        child={**task,'window':task['window']+f'_part{i+1}',
               'start_utc':cuts[i].isoformat(),'end_utc':cuts[i+1].isoformat()}
        children.append(fetch_request(child,credential))
    rec=dict(task=task,endpoint=ENDPOINT,status='error',attempts=[],subrequests=children,
             split_reason='Madrid 25-hour DST day; API limits A84 request duration to 24 hours')
    if all(c['status'] in ('ok','no_data') for c in children):
        buffer=BytesIO()
        with ZipFile(buffer,'w') as archive:
            for i,child in enumerate(children):
                archive.writestr(f'part{i+1}.xml',gzip.decompress((BASE/child['raw_path']).read_bytes()))
        body=buffer.getvalue();digest=hashlib.sha256(body).hexdigest()
        raw=target.parent/(target.name+'_split_'+digest[:12]+'.raw.gz')
        if not raw.exists():raw.write_bytes(gzip.compress(body,compresslevel=1,mtime=0))
        rec.update(status='ok' if any(c['status']=='ok' for c in children) else 'no_data',
                   raw_path=str(raw.relative_to(BASE)),sha256=digest,source_rows=sum(c.get('source_rows',0) for c in children),resolutions=['PT4S'])
    receipt=target.parent/(target.name+'_retry_'+datetime.now(UTC).strftime('%H%M%S')+'.json')
    dump(receipt,rec)
    return rec


def fetch():
    tasks=load(BASE/'tasks.json');credential=token();results=[]
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures={pool.submit(fetch_one,task,credential):task for task in tasks}
        for future in as_completed(futures):
            results.append(future.result())
            if len(results)%10==0 or len(results)==len(tasks):
                snapshot=dict(done=len(results),total=len(tasks),status_counts=dict(Counter(r['status'] for r in results)),last_task=results[-1]['task'])
                dump(BASE/'fetch_progress.json',snapshot)
                dump(BASE/'fetch_manifest.json',sorted(results,key=lambda r:(r['task']['kind'],r['task']['window'])))
                print(json.dumps(snapshot),flush=True)
    return results


def activation_arrays(body, day):
    start,end=bounds(day);n=int((end-start).total_seconds()/4)
    values={d:[None]*n for d in ('up','down')};seen={d:[False]*n for d in values}
    docs,rows=parse(body)
    for doc in docs:
        if 'no matching data' in doc.get('Reason/text','').lower():
            continue
        if doc.get('type')!='A84' or doc.get('process.processType')!='A67' or doc.get('area_Domain.mRID')!=ES:
            raise ValueError('unexpected activation document')
    for row in rows:
        s=row['series'];point=row['point']
        if (s.get('businessType'),s.get('currency_Unit.name'),s.get('price_Measure_Unit.name'),s.get('standard_MarketProduct.marketProductType'))!=('A96','EUR','MWH','A01'):
            raise ValueError('unexpected activation series')
        if row['resolution']!='PT4S':
            raise ValueError('non-4s activation data')
        d={'A01':'up','A02':'down'}[s['flowDirection.direction']]
        a=max(start,datetime.fromisoformat(row['start']));b=min(end,datetime.fromisoformat(row['end']))
        left,right=(a-start).total_seconds()/4,(b-start).total_seconds()/4
        if left!=int(left) or right!=int(right):
            raise ValueError('activation off 4s grid')
        lo,hi=int(left),int(right)
        if lo>=hi:
            continue
        if any(seen[d][lo:hi]):
            raise ValueError('overlapping activation intervals')
        raw=point.get('activation_Price.amount');value=float(raw) if raw is not None else None
        if value is not None and (not math.isfinite(value) or point.get('imbalance_Price.category')!='A08'):
            raise ValueError('invalid activation price/category')
        values[d][lo:hi]=[value]*(hi-lo);seen[d][lo:hi]=[True]*(hi-lo)
    return values,seen


def gap_runs(vals,seen,start):
    """Missing prices are classified, never fabricated or propagated."""
    active=None
    for i in range(len(vals)+1):
        status=None if i==len(vals) or vals[i] is not None else 'source_explicit_null' if seen[i] else 'source_unreported'
        if status != (active[1] if active else None):
            if active:
                yield start+4*active[0],start+4*i,active[1]
            active=(i,status) if status else None


def merge():
    (BASE/'processed/prices_4s').mkdir(parents=True,exist_ok=True)
    sources=Sources();grid=load(BASE/'initial_qh.json');old=load(BASE/'activation_archive.json')
    receipts=load(BASE/'fetch_manifest.json');fresh={};selected={};errors=[]
    for rec in receipts:
        task=rec['task']
        if rec['status']=='error':
            errors.append(task);continue
        sid,body=sources.add(BASE/rec['raw_path'],'ENTSOE_'+task['kind'].upper()+'_REFRESH',rec['sha256'],rec)
        if task['kind']=='activation':
            fresh[task['window']]={'source_id':sid,'status':rec['status']}
        elif rec['status']=='ok':
            apply_api_qh(grid,body,task['kind'],sid)
    sources.save();dump(BASE/'selected_qh.json',grid)
    daily=[];month_stats=defaultdict(Counter);files={};rows4=0;borrowed=0;selected_sources=[]
    refresh_changes=[];change_totals=Counter()
    master=BASE/'processed/market_prices_15min.csv'
    gapfile=BASE/'processed/remaining_price_gaps.csv.gz'
    mf=master.open('w',newline='',encoding='utf-8-sig');mw=csv.writer(mf)
    mw.writerow(['start_utc','start_europe_madrid','da_eur_mwh','capacity_up_eur_mw_qh','capacity_down_eur_mw_qh',
                 'da_native_resolution','da_source_id','capacity_up_source_id','capacity_down_source_id',
                 'activation_up_valid_seconds','activation_down_valid_seconds','activation_up_mean_eur_mwh','activation_down_mean_eur_mwh',
                 'activation_up_reported_seconds','activation_down_reported_seconds','activation_source_id'])
    gf=gzip.open(gapfile,'wt',newline='',encoding='utf-8',compresslevel=1);gw=csv.writer(gf)
    gw.writerow(['field','start_utc','end_utc_exclusive','seconds','reason','source_id'])
    try:
        for day in days():
            ds=str(day);ym=ds[:7];a,b=bounds(day);start=int(a.timestamp());n=int((b-a).total_seconds()/4)
            chosen=fresh.get(ds)
            if not chosen or (chosen['status']=='no_data' and old.get(ds,{}).get('status')=='ok'):
                chosen=old.get(ds);borrowed+=1
            if not chosen:
                values={d:[None]*n for d in ('up','down')};seen={d:[False]*n for d in values};sid='';status='no_archive'
            else:
                sid,status=chosen['source_id'],chosen['status']
                if status=='ok':values,seen=activation_arrays(sources.body(sid),day)
                else:values={d:[None]*n for d in ('up','down')};seen={d:[False]*n for d in values}
            selected_sources.append(dict(date=ds,source_id=sid,status=status))
            change=dict(date=ds,old_source_id=old.get(ds,{}).get('source_id',''),selected_source_id=sid)
            if old.get(ds,{}).get('status')=='ok':
                prior,_=activation_arrays(sources.body(old[ds]['source_id']),day)
            else:
                prior={d:[None]*n for d in ('up','down')}
            for d in ('up','down'):
                metrics=dict(newly_priced=sum(a is None and b is not None for a,b in zip(prior[d],values[d])),
                             now_null=sum(a is not None and b is None for a,b in zip(prior[d],values[d])),
                             changed_valid_price=sum(a is not None and b is not None and abs(a-b)>1e-9 for a,b in zip(prior[d],values[d])))
                for key,value in metrics.items():
                    change[d+'_'+key]=value;change_totals[d+'_'+key]+=value
            refresh_changes.append(change)
            if ym not in files:
                path=BASE/'processed/prices_4s'/(ym+'.csv.gz')
                handle=gzip.open(path,'wt',newline='',encoding='utf-8',compresslevel=1)
                writer=csv.writer(handle)
                writer.writerow(['start_utc','start_europe_madrid','da_eur_mwh','capacity_up_eur_mw_qh','capacity_down_eur_mw_qh',
                                 'da_native_resolution','activation_up_eur_mwh','activation_down_eur_mwh','up_price_status','down_price_status','activation_source_id'])
                files[ym]=(handle,writer)
            writer=files[ym][1]
            for i in range(n):
                t=start+4*i
                if i%225==0:
                    mapped=[grid[field].get(str(t)) for field in FIELDS]
                    repeated=[v[0] if v else '' for v in mapped]
                    native=mapped[0][2] if mapped[0] else ''
                states=[('valid' if values[d][i] is not None else 'source_explicit_null' if seen[d][i] else 'api_no_matching_data' if status=='no_data' else 'source_unreported') for d in ('up','down')]
                writer.writerow([iso(t),datetime.fromtimestamp(t,UTC).astimezone(TZ).isoformat(),
                                 *repeated,native,
                                 values['up'][i] if values['up'][i] is not None else '',values['down'][i] if values['down'][i] is not None else '',*states,sid])
            rows4+=n
            for d in ('up','down'):
                valid=sum(v is not None for v in values[d]);reported=sum(seen[d])
                daily.append(dict(date=ds,field='activation_'+d,expected=n,valid=valid,reported=reported,explicit_null=reported-valid,source_missing=n-reported,source_id=sid,request_status=status))
                month_stats[ym]['activation_'+d+'_expected']+=n;month_stats[ym]['activation_'+d+'_valid']+=valid
                for left,right,reason in gap_runs(values[d],seen[d],start):
                    if status=='no_data':reason='api_no_matching_data'
                    gw.writerow(['activation_'+d,iso(left),iso(right),right-left,reason,sid])
            for j in range(n//225):
                t=start+j*900
                prices=[grid[field].get(str(t)) for field in FIELDS]
                chunks={d:values[d][j*225:(j+1)*225] for d in values}
                nonnull={d:[v for v in chunks[d] if v is not None] for d in values}
                mw.writerow([iso(t),datetime.fromtimestamp(t,UTC).astimezone(TZ).isoformat(),
                    *[v[0] if v else '' for v in prices],prices[0][2] if prices[0] else '',*[v[1] if v else '' for v in prices],
                    len(nonnull['up'])*4,len(nonnull['down'])*4,
                    sum(nonnull['up'])/len(nonnull['up']) if nonnull['up'] else '',sum(nonnull['down'])/len(nonnull['down']) if nonnull['down'] else '',
                    sum(seen['up'][j*225:(j+1)*225])*4,sum(seen['down'][j*225:(j+1)*225])*4,sid])
            for field in FIELDS:
                valid=sum(str(t) in grid[field] for t in range(start,int(b.timestamp()),900));expected=n//225
                daily.append(dict(date=ds,field=field,expected=expected,valid=valid,reported=valid,explicit_null=0,source_missing=expected-valid,source_id='see_15min_file',request_status='merged'))
                month_stats[ym][field+'_expected']+=expected;month_stats[ym][field+'_valid']+=valid
                for t in range(start,int(b.timestamp()),900):
                    if str(t) not in grid[field]:gw.writerow([field,iso(t),iso(t+900),900,'not_available_after_refresh',''])
            if (len(selected_sources)%20)==0:
                print(json.dumps(dict(merged_days=len(selected_sources),rows_4s=rows4,last_date=ds)),flush=True)
                dump(BASE/'merge_progress.json',dict(merged_days=len(selected_sources),rows_4s=rows4,last_date=ds))
    finally:
        mf.close();gf.close()
        for handle,_ in files.values():handle.close()
    with (BASE/'processed/daily_coverage.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(daily[0]));w.writeheader();w.writerows(daily)
    with (BASE/'processed/activation_refresh_changes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=list(refresh_changes[0]));w.writeheader();w.writerows(refresh_changes)
    dump(BASE/'monthly_coverage.json',dict(month_stats));dump(BASE/'activation_selected_sources.json',selected_sources)
    totals={field:dict(expected=sum(r['expected'] for r in daily if r['field']==field),valid=sum(r['valid'] for r in daily if r['field']==field)) for field in (*FIELDS,'activation_up','activation_down')}
    for v in totals.values():v['coverage_pct']=100*v['valid']/v['expected']
    summary=dict(start=str(START),end_exclusive=str(END),days=len(days()),rows_4s=rows4,rows_15min=rows4//225,totals=totals,
                 fetch_status=dict(Counter(r['status'] for r in receipts)),fetch_errors=errors,fallback_to_archive_days=borrowed,
                 activation_refresh_changes=dict(change_totals),sources=len(sources.items))
    dump(BASE/'summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__);parser.add_argument('phase',choices=('inventory','fetch','merge'))
    args=parser.parse_args()
    globals()[args.phase]()
