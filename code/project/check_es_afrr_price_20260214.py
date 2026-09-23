"""Fetch live eSIOS aggregation evidence; compare exact archived MILP inputs."""
import sys,json,csv,hashlib
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from src.data_ingestion.es.ree import ESIOSClient
from src.data_ingestion.es.esios_batch import read_ree_key
ROOT=CODE.parent;STAMP=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
RAW=ROOT/'input/raw/ES/esios'/('aggregation_check_'+STAMP)
OUT=ROOT/'reports'/('afrr_price_20260214_'+STAMP)
RAW.mkdir(parents=True);OUT.mkdir(parents=True)
key=read_ree_key(ROOT.parents[2]/'data/API_Key.md')
variants={'qh_default':('fifteen_minutes',None),'hour_default':('hour',None),'hour_average':('hour','average'),'hour_sum':('hour','sum')}
def fetch(job):
    iid,label=job;trunc,agg=variants[label];client=ESIOSClient(api_key=key,timeout=45)
    params=dict(start_date='2026-02-14T00:00:00+01:00',end_date='2026-02-14T23:59:59+01:00',time_trunc=trunc)
    if agg:params['time_agg']=agg
    response,payload=client.fetch_indicator(iid,**params)
    meta=client.save_response(response,RAW/f'{iid}_{label}.json',url=client.build_indicator_url(iid,**params),request_params=params)
    print(json.dumps(dict(id=iid,variant=label,status=response.status,bytes=len(response.body))),flush=True)
    if response.status!=200 or not payload or 'indicator' not in payload:raise RuntimeError(f'API failed: {iid} {label} status={response.status}')
    return (iid,label),(payload['indicator'],meta)
with ThreadPoolExecutor(max_workers=4) as pool:data=dict(pool.map(fetch,[(iid,label) for iid in (2130,634) for label in variants]))
tz=ZoneInfo('Europe/Madrid');selected={8,12,19}
def points(ind):
    result={}
    for r in ind['values']:
        if r.get('geo_id')!=8741:continue
        t=datetime.fromisoformat(r['datetime_utc'].replace('Z','+00:00')).astimezone(tz)
        if t.strftime('%Y-%m-%d')=='2026-02-14' and t.hour in selected:
            if t.isoformat() in result:raise ValueError('duplicate API timestamp')
            result[t.isoformat()]=float(r['value'])
    return result
values={k:points(v[0]) for k,v in data.items()}
source=ROOT/'output/perfect_v1_full_completed_retry/solver_input.json'
configuration=json.loads(source.read_text(encoding='utf-8'))
model={datetime.fromisoformat(q['start_utc']).astimezone(tz).isoformat():q for q in configuration['qhs']}
rows=[];hourly=[]
for hour in sorted(selected):
    hourkey=f'2026-02-14T{hour:02}:00:00+01:00'
    for iid,direction,field in [(2130,'up','afrr_capacity_price_up_eur_per_mw_qh'),(634,'down','afrr_capacity_price_down_eur_per_mw_qh')]:
        qvals=[];mvals=[]
        for minute in (0,15,30,45):
            t=f'2026-02-14T{hour:02}:{minute:02}:00+01:00';a=values[iid,'qh_default'][t];b=model[t][field]
            qvals.append(a);mvals.append(b)
            rows.append(dict(local_time=t,direction=direction,indicator=iid,api_qh_eur_per_mw=a,milp_qh_eur_per_mw=b,difference=a-b))
        h={label:values[iid,label][hourkey] for label in variants if label!='qh_default'}
        hourly.append(dict(local_hour=hourkey,direction=direction,indicator=iid,**h,qh_sum=sum(qvals),qh_average=sum(qvals)/4,milp_qh_sum=sum(mvals),milp_qh_average=sum(mvals)/4,
            default_minus_qh_sum=h['hour_default']-sum(qvals),default_minus_qh_average=h['hour_default']-sum(qvals)/4))
def csvsave(name,records):
    with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
csvsave('quarter_hour_comparison.csv',rows);csvsave('hourly_comparison.csv',hourly)
payload=dict(retrieved_utc=datetime.now(timezone.utc).isoformat(),raw_directory=str(RAW),model_input=str(source),model_input_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
    qh=rows,hourly=hourly,api_metadata={str(iid)+'_'+label:dict(name=ind.get('name'),short_name=ind.get('short_name'),unit=ind.get('magnitud'),time=ind.get('tiempo'),values_updated_at=ind.get('values_updated_at'),request=meta) for (iid,label),(ind,meta) in data.items()})
(OUT/'comparison.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(output=str(OUT),qh=rows,hourly=hourly),ensure_ascii=True),flush=True)
