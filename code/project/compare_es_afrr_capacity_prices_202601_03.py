"""Compare monthly pooled aFRR capacity prices from QH vs hourly-average API."""
import sys,json,csv,math,hashlib
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from src.data_ingestion.es.ree import ESIOSClient
from src.data_ingestion.es.esios_batch import read_ree_key
ROOT=CODE.parent;stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
RAW=ROOT/'input/raw/ES/esios'/('price_granularity_'+stamp);OUT=ROOT/'reports'/('afrr_capacity_price_monthly_202601_03_'+stamp)
RAW.mkdir(parents=True);OUT.mkdir(parents=True);TZ=ZoneInfo('Europe/Madrid')
key=read_ree_key(ROOT.parents[2]/'data/API_Key.md')
variants={'qh':('fifteen_minutes',None),'hour_average':('hour','average')}
def fetch(job):
    iid,label=job;trunc,agg=variants[label];client=ESIOSClient(api_key=key,timeout=60)
    params=dict(start_date='2026-01-01T00:00:00+01:00',end_date='2026-03-31T23:59:59+02:00',time_trunc=trunc)
    if agg:params['time_agg']=agg
    response,payload=client.fetch_indicator(iid,**params)
    meta=client.save_response(response,RAW/f'{iid}_{label}.json',url=client.build_indicator_url(iid,**params),request_params=params)
    if response.status!=200 or not payload or 'indicator' not in payload:raise RuntimeError(f'{iid} {label}: HTTP {response.status}')
    ind=payload['indicator'];values=defaultdict(list)
    for r in ind.get('values',[]):
        if r.get('geo_id')!=8741 or r.get('geo_name')!='Península':continue
        t=datetime.fromisoformat(r['datetime_utc'].replace('Z','+00:00')).astimezone(TZ)
        values[t.strftime('%Y-%m')].append((t,float(r['value'])))
    print(json.dumps(dict(indicator=iid,variant=label,status=response.status,records=sum(map(len,values.values())))),flush=True)
    return (iid,label),dict(values=dict(values),metadata=meta,name=ind.get('name'),unit=ind.get('magnitud'),resolution=ind.get('tiempo'),updated=ind.get('values_updated_at'))
with ThreadPoolExecutor(max_workers=4) as pool:data=dict(pool.map(fetch,[(iid,v) for iid in (2130,634) for v in variants]))
expected={'2026-01':(2976,744),'2026-02':(2688,672),'2026-03':(2972,743)}
rows=[];monthly=[]
for month,(expected_qh,expected_hour) in expected.items():
    ds={}
    for iid,direction in ((2130,'up'),(634,'down')):
        q=data[iid,'qh']['values'][month];h=data[iid,'hour_average']['values'][month]
        assert len(q)==expected_qh and len(h)==expected_hour,(month,iid,len(q),len(h))
        qvals=[v for _,v in q];hvals=[v for _,v in h]
        qmean=math.fsum(qvals)/len(qvals);hmean=math.fsum(hvals)/len(hvals)
        ds[direction]=(qmean,hmean)
        rows.append(dict(month=month,direction=direction,indicator=iid,qh_count=len(q),qh_average_eur_per_mw=qmean,
                         hour_count=len(h),hour_average_eur_per_mw=hmean,difference_hour_minus_qh=hmean-qmean))
    monthly.append(dict(month=month,qh_intervals_per_direction=expected_qh,hours_per_direction=expected_hour,
        qh_up_average=ds['up'][0],qh_down_average=ds['down'][0],qh_pooled_average=(ds['up'][0]+ds['down'][0])/2,
        hour_up_average=ds['up'][1],hour_down_average=ds['down'][1],hour_pooled_average=(ds['up'][1]+ds['down'][1])/2,
        pooled_difference=(ds['up'][1]+ds['down'][1]-ds['up'][0]-ds['down'][0])/2))
def write_csv(path,data):
    with path.open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
write_csv(OUT/'monthly_pooled_average.csv',monthly);write_csv(OUT/'monthly_direction_check.csv',rows)
meta={f'{iid}_{v}':dict(request=d['metadata'],indicator_name=d['name'],unit=d['unit'],resolution=d['resolution'],values_updated_at=d['updated']) for (iid,v),d in data.items()}
payload=dict(retrieved_utc=datetime.now(timezone.utc).isoformat(),region={'geo_id':8741,'geo_name':'Península'},
    date_range_local=['2026-01-01','2026-03-31'],pooling_definition='arithmetic mean of equal counts of Up indicator 2130 and Down indicator 634 values',
    hourly_definition='API time_agg=average; mean of hourly average prices within month',raw_directory=str(RAW),requests=meta,monthly=monthly,direction_checks=rows)
(OUT/'comparison.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 2026年1–3月aFRR容量价格：QH与小时均价口径对比','',
f"数据来源：REE eSIOS API，Península（geo_id=8741）；提取时间UTC {payload['retrieved_utc']}。",
'Up为指标2130，Down为指标634；下表总平均将Up与Down观测等权合并。QH口径直接平均月内所有15分钟值；小时口径平均月内API返回的小时均值。',
'小时请求显式使用`time_trunc=hour&time_agg=average`；QH请求使用`time_trunc=fifteen_minutes`并省略`time_agg`。不使用小时默认聚合，因为此前实测该默认返回sum。', '',
'| 月份 | QH Up均价 | QH Down均价 | QH合并均价 | Hourly Up均价 | Hourly Down均价 | Hourly合并均价 | 小时−QH |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in monthly:lines.append(f"| {r['month']} | {r['qh_up_average']:.6f} | {r['qh_down_average']:.6f} | {r['qh_pooled_average']:.6f} | {r['hour_up_average']:.6f} | {r['hour_down_average']:.6f} | {r['hour_pooled_average']:.6f} | {r['pooled_difference']:+.9f} |")
lines+=['','单位沿用API的€/MW。月平均价格不是月收益；储能收益还须按每QH成交容量逐项计算。数据为事后历史序列，不涉及模型重算。','',f"原始响应及含参数的元数据保存在`{RAW}`；逐方向数据见monthly_direction_check.csv。"]
(OUT/'月度对比说明.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(output=str(OUT),monthly=monthly),ensure_ascii=False))
