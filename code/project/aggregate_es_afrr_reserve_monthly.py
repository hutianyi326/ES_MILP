"""Aggregate archived REE Peninsula aFRR assigned-reserve QH records monthly."""
import json,csv,hashlib,calendar
from pathlib import Path
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from collections import defaultdict

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'input/raw/ES/esios'; TZ=ZoneInfo('Europe/Madrid')
OUT=ROOT/'reports'/('afrr_reserve_monthly_peninsular_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
IDS={632:('up','上调'),633:('down','下调')}
QH=900

def expected_count(month):
    y,m=map(int,month.split('-'));ny=y+(m==12);nm=1 if m==12 else m+1
    start=datetime(y,m,1,tzinfo=TZ).timestamp();end=datetime(ny,nm,1,tzinfo=TZ).timestamp()
    return int((end-start)//QH)

def candidates(iid):
    grouped=defaultdict(list)
    for path in RAW.rglob(f'fetch_{iid}.json'):
        meta_path=path.with_suffix(path.suffix+'.meta.json')
        try:
            meta=json.loads(meta_path.read_text(encoding='utf-8'))
            digest=hashlib.sha256(path.read_bytes()).hexdigest()
            if meta.get('http_status')!=200 or meta.get('sha256')!=digest:continue
            p=meta.get('request_params',{})
            if p.get('time_trunc')!='fifteen_minutes':continue
            payload=json.loads(path.read_text(encoding='utf-8'))['indicator']
            if int(payload.get('id',-1))!=iid:continue
            for r in payload.get('values',[]):
                if r.get('geo_id')!=8741 or r.get('geo_name')!='Península':continue
                t=datetime.fromisoformat(r['datetime_utc'].replace('Z','+00:00')).astimezone(TZ)
                month=t.strftime('%Y-%m')
                if p.get('start_date','')[:7]!=month:continue
                if t.minute not in (0,15,30,45) or t.second or t.microsecond:continue
                v=float(r['value'])
                if v<0:continue
                # Use epoch seconds as the interval key: aware local datetimes
                # across a DST fold can otherwise compare equal in Python.
                grouped[month].append((int(t.timestamp()),v,path,meta,digest,payload))
        except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):continue
    return grouped

grouped={iid:candidates(iid) for iid in IDS}
months=sorted(set.intersection(*(set(x) for x in grouped.values())))
if not months:raise RuntimeError('No common monthly archive for indicators 632/633')
OUT.mkdir(parents=True)
table=[];source_manifest=[];monthly_values={}
for month in months:
    expected=expected_count(month); agg={}
    for iid in IDS:
        options=[]
        for rows in [grouped[iid][month]]:
            # Archive entries can overlap. Pick a single intact source that maximizes unique QH coverage.
            byfile=defaultdict(dict);metas={}
            for epoch,v,path,meta,digest,payload in rows:
                byfile[path][epoch]=v;metas[path]=(meta,digest,payload)
            for path,values in byfile.items():
                meta,digest,payload=metas[path]
                options.append((len(values),path,values,meta,digest,payload))
        if not options:continue
        options.sort(key=lambda x:(x[0],str(x[1])),reverse=True)
        n,path,values,meta,digest,payload=options[0]
        # Ensure the chosen source does not contain conflicting duplicate timestamps.
        allvals=defaultdict(set)
        for t,v,p,_,_,_ in grouped[iid][month]:
            if p==path:allvals[t].add(v)
        if any(len(v)>1 for v in allvals.values()):raise ValueError(f'Conflicting duplicates: {iid} {month} {path}')
        if len(values)!=n:raise AssertionError('unique count mismatch')
        avg=sum(values.values())/n if n else None;total=sum(values.values()) if n else None
        agg[iid]=dict(avg=avg,total=total,n=n,expected=expected,coverage=n/expected,
                      qh_mw_hours=total*.25 if total is not None else None)
        source_manifest.append(dict(month=month,indicator=iid,path=path.relative_to(ROOT).as_posix(),sha256=digest,
            request_params=meta.get('request_params'),name=payload.get('name'),short_name=payload.get('short_name'),
            unit=payload.get('magnitud'),resolution=payload.get('tiempo'),source_updated_at=payload.get('values_updated_at'),
            unique_peninsular_qh=n,expected_qh=expected))
    if len(agg)!=2:continue
    monthly_values[month]=agg
    a,b=agg[632],agg[633]
    table.append(dict(month=month,region='Península',expected_qh=expected,
        up_valid_qh=a['n'],up_coverage_pct=100*a['coverage'],up_average_MW=a['avg'],up_sum_MW_QH=a['total'],up_sum_times_0_25h_MWh_equiv=a['qh_mw_hours'],
        down_valid_qh=b['n'],down_coverage_pct=100*b['coverage'],down_average_MW=b['avg'],down_sum_MW_QH=b['total'],down_sum_times_0_25h_MWh_equiv=b['qh_mw_hours']))

with (OUT/'monthly_up_down.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(table[0]));w.writeheader();w.writerows(table)
doc=['# REE半岛aFRR上/下调分配容量需求月聚合','',
     f"数据范围：{months[0]}至{months[-1]}（本地已归档交集月份，共{len(table)}个月）。",
     '区域：Península（geo_id=8741）；REE eSIOS指标632=上调分配备用容量，633=下调分配备用容量。按响应中的datetime_utc换算为Europe/Madrid后分月。',
     '口径：均值为该月有效15分钟观测值的算术平均（MW）；sum为有效QH中原始MW数值直接累加（MW·QH，统计量，不是平均MW，也不是月交付电量）。附列sum×0.25小时作为容量时段积分的MWh等价值，方便识别量纲。',
     '聚合基于已归档的time_trunc=fifteen_minutes原始记录，筛选正确HTTP状态、响应哈希、指标ID及半岛区域；每指标每月选择有效QH覆盖最多的单个源文件，重叠归档不重复累加。缺失QH不补值，均值和sum基于有效值，并列出覆盖率。',
     '', '| 月份 | 预期QH | Up有效/覆盖 | Up均值MW | Up sum (MW·QH) | Down有效/覆盖 | Down均值MW | Down sum (MW·QH) |','|---|---:|---:|---:|---:|---:|---:|---:|']
for r in table:
    doc.append(f"| {r['month']} | {r['expected_qh']} | {r['up_valid_qh']} ({r['up_coverage_pct']:.2f}%) | {r['up_average_MW']:.4f} | {r['up_sum_MW_QH']:.2f} | {r['down_valid_qh']} ({r['down_coverage_pct']:.2f}%) | {r['down_average_MW']:.4f} | {r['down_sum_MW_QH']:.2f} |")
doc+=['','月度sum仅累加有效QH。发生整段缺失的月份，sum会因观测数减少而偏低；跨年限比较sum应结合coverage，均值也只代表实际观测时段。完整精度及MWh等价值见monthly_up_down.csv。']
(OUT/'月度聚合说明.md').write_text('\n'.join(doc)+'\n',encoding='utf-8')
manifest=dict(generated_utc=datetime.now(timezone.utc).isoformat(),region={'geo_id':8741,'geo_name':'Península'},
    indicator_definition={str(k):v for k,v in IDS.items()},months=months,sources=source_manifest,
    checks=dict(common_months=len(table),qhs_per_local_day=96,dst_adjusted_expected_qh=True,no_values_filled=True,duplicate_source_overlap_not_summed=True))
(OUT/'source_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps(dict(output=str(OUT),months=len(table),first=months[0],last=months[-1],
    incomplete=[r['month'] for r in table if r['up_valid_qh']<r['expected_qh'] or r['down_valid_qh']<r['expected_qh']],
    rows=table),ensure_ascii=False))
