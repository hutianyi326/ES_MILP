"""Live February 2026 capacity-price monthly aggregation with raw evidence."""
import sys,json,math
from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
CODE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CODE))
from src.data_ingestion.es.ree import ESIOSClient
from src.data_ingestion.es.esios_batch import read_ree_key
ROOT=CODE.parent;stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
raw=ROOT/'input/raw/ES/esios'/('monthly_check_'+stamp);raw.mkdir(parents=True)
out=ROOT/'reports'/('afrr_month_202602_'+stamp);out.mkdir(parents=True)
key=read_ree_key(ROOT.parents[2]/'data/API_Key.md')
variants={'month_default':('month',None),'month_sum':('month','sum'),'month_average':('month','average'),'qh_default':('fifteen_minutes',None)}
def fetch(job):
    iid,label=job;trunc,agg=variants[label];client=ESIOSClient(api_key=key,timeout=60)
    params=dict(start_date='2026-02-01T00:00:00+01:00',end_date='2026-02-28T23:59:59+01:00',time_trunc=trunc)
    if agg:params['time_agg']=agg
    response,payload=client.fetch_indicator(iid,**params)
    meta=client.save_response(response,raw/f'{iid}_{label}.json',url=client.build_indicator_url(iid,**params),request_params=params)
    if response.status!=200 or not payload or 'indicator' not in payload:raise RuntimeError(f'{iid} {label}: HTTP {response.status}')
    ind=payload['indicator'];rows=[r for r in ind['values'] if r.get('geo_id')==8741]
    return (iid,label),dict(rows=rows,metadata=meta,name=ind.get('name'),unit=ind.get('magnitud'),updated=ind.get('values_updated_at'))
with ThreadPoolExecutor(max_workers=4) as pool:data=dict(pool.map(fetch,[(iid,label) for iid in (2130,634) for label in variants]))
summary=[]
for iid,direction in ((2130,'up'),(634,'down')):
    q=data[iid,'qh_default']['rows'];values=[float(r['value']) for r in q]
    assert len(q)==2688 and len({r['datetime_utc'] for r in q})==2688 and all(math.isfinite(v) for v in values)
    result=dict(indicator=iid,direction=direction,qh_count=len(q),qh_sum=math.fsum(values),qh_average=math.fsum(values)/len(q))
    for label in ('month_default','month_sum','month_average'):
        rows=data[iid,label]['rows'];assert len(rows)==1
        result[label]=float(rows[0]['value'])
    result['default_minus_sum']=result['month_default']-result['month_sum']
    result['api_sum_minus_qh_sum']=result['month_sum']-result['qh_sum']
    result['api_average_minus_qh_average']=result['month_average']-result['qh_average']
    summary.append(result)
payload=dict(retrieved_utc=datetime.now(timezone.utc).isoformat(),timezone='Europe/Madrid',raw_directory=str(raw),summary=summary,
    requests={str(i)+'_'+label:v for (i,label),v in data.items() if label!='qh_default'})
(out/'comparison.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding='utf-8')
lines=['# 2026年2月aFRR容量价格月聚合实测','',f"提取时间UTC：{payload['retrieved_utc']}。来源：REE eSIOS API。区域：Península，geo_id=8741。",'',
'日期范围：2026-02-01T00:00:00+01:00至2026-02-28T23:59:59+01:00；Europe/Madrid当地时间，28日、672小时、2688个QH。','',
'接口：GET https://api.esios.ree.es/indicators/2130（up）；GET https://api.esios.ree.es/indicators/634（down）。locale=es，未设置geo_agg，返回后筛选geo_id=8741。','',
'| 方向 | 月默认（time_agg省略） | 月sum | 月average | QH条数 |','|---|---:|---:|---:|---:|']
for r in summary:lines.append(f"| {r['direction']} | {r['month_default']:.8f} | {r['month_sum']:.8f} | {r['month_average']:.8f} | {r['qh_count']} |")
lines+=['','以上三个请求均为time_trunc=month。另请求time_trunc=fifteen_minutes且省略time_agg，核对月内QH求和与平均。单位保留API的Precio €/MW；sum是月内QH价格累计，average是QH价格平均，不应将两者都称为月均价。','',
'月累计价格不等于电站实际月收益；电站容量随时段变化时，仍需按每QH成交MW乘对应价格再加总。此次仅核验接口数据与聚合，不修改模型，不重跑收益。', '',
f'原始响应及请求参数、URL、获取时间、SHA256保存在：`{raw}`。具体差额和响应值见comparison.json。']
(out/'月聚合对比.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(output=str(out),summary=summary),ensure_ascii=True))
