"""Independent, streaming validation of the merged fixed-4s and 15min files."""
import csv
from collections import Counter
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path

if __package__:
    from .consolidate_simple_market_data import BASE, START, END, bounds
else:
    from consolidate_simple_market_data import BASE, START, END, bounds


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def stamp(text):
    return int(datetime.fromisoformat(text.replace('Z','+00:00')).timestamp())


def main():
    summary=read(BASE/'summary.json');sources=read(BASE/'sources.json')
    a,b=(int(bounds(day)[0].timestamp()) for day in (START,END))
    qh={};expected=a
    with (BASE/'processed/market_prices_15min.csv').open(encoding='utf-8-sig',newline='') as f:
        for row in csv.DictReader(f):
            t=stamp(row['start_utc']);assert t==expected
            assert stamp(row['start_europe_madrid'])==t
            for key in ('da_eur_mwh','capacity_up_eur_mw_qh','capacity_down_eur_mw_qh'):
                assert row[key]!='' and math.isfinite(float(row[key]))
            for key in ('da_source_id','capacity_up_source_id','capacity_down_source_id','activation_source_id'):
                assert row[key] in sources
            assert row['da_native_resolution'] in ('PT60M','PT15M')
            qh[t]=row;expected+=900
    assert expected==b and len(qh)==summary['rows_15min']
    expected=a;counts=Counter();month_counts=Counter();max_mean_error=0.;qh_count=0
    first_valid={};last_valid={}
    files=sorted((BASE/'processed/prices_4s').glob('*.csv.gz'))
    for path in files:
        chunk={'up':[],'down':[]};reported=Counter();start=None
        with gzip.open(path,'rt',encoding='utf-8',newline='') as f:
            for row in csv.DictReader(f):
                t=stamp(row['start_utc']);assert t==expected,(t,expected)
                assert stamp(row['start_europe_madrid'])==t
                assert row['start_europe_madrid'][:7]==path.name[:7]
                assert row['activation_source_id'] in sources
                parent=qh[(t//900)*900]
                for key in ('da_eur_mwh','capacity_up_eur_mw_qh','capacity_down_eur_mw_qh','da_native_resolution'):
                    assert row[key]==parent[key],(t,key)
                if start is None:start=t
                for d in ('up','down'):
                    value=row['activation_'+d+'_eur_mwh'];status=row[d+'_price_status']
                    assert status in ('valid','source_explicit_null','source_unreported','api_no_matching_data')
                    if status=='valid':
                        assert value!='' and math.isfinite(float(value))
                        chunk[d].append(float(value));counts[d+'_valid']+=1
                        first_valid.setdefault(d,row['start_utc']);last_valid[d]=row['start_utc']
                    else:assert value==''
                    if status in ('valid','source_explicit_null'):reported[d]+=1
                    counts[d+'_'+status+'_seconds']+=4
                counts['rows_4s']+=1;month_counts[path.name[:7]]+=1;expected+=4
                if expected-start==900:
                    original=qh[start]
                    for d in ('up','down'):
                        assert int(original['activation_'+d+'_valid_seconds'])==4*len(chunk[d])
                        assert int(original['activation_'+d+'_reported_seconds'])==4*reported[d]
                        raw=original['activation_'+d+'_mean_eur_mwh']
                        if chunk[d]:
                            err=abs(float(raw)-sum(chunk[d])/len(chunk[d]));max_mean_error=max(max_mean_error,err);assert err<1e-7
                        else:assert raw==''
                    qh_count+=1;chunk={'up':[],'down':[]};reported=Counter();start=None
        assert start is None
        print(json.dumps(dict(validated_month=path.name[:7],rows_4s=month_counts[path.name[:7]])),flush=True)
    assert expected==b and counts['rows_4s']==summary['rows_4s'] and qh_count==len(qh)
    for d in ('up','down'):
        assert counts[d+'_valid']==summary['totals']['activation_'+d]['valid']
    gaps=Counter()
    with gzip.open(BASE/'processed/remaining_price_gaps.csv.gz','rt',encoding='utf-8',newline='') as f:
        for row in csv.DictReader(f):
            left,right=stamp(row['start_utc']),stamp(row['end_utc_exclusive'])
            assert a<=left<right<=b and right-left==int(row['seconds'])
            gaps[row['field']]+=right-left
    for field in ('da','capacity_up','capacity_down'):
        assert gaps[field]==0
    for d in ('up','down'):
        assert gaps['activation_'+d]==(summary['rows_4s']-counts[d+'_valid'])*4
    for sid,item in sources.items():
        body=gzip.decompress((BASE/item['archive_path']).read_bytes())
        assert hashlib.sha256(body).hexdigest()==item['sha256_uncompressed'],sid
    result=dict(expected_start_utc=datetime.fromtimestamp(a,timezone.utc).isoformat(),
                end_exclusive_utc=datetime.fromtimestamp(b,timezone.utc).isoformat(),
                rows_15min=len(qh),rows_4s=counts['rows_4s'],months=len(files),
                activation_valid_points={d:counts[d+'_valid'] for d in ('up','down')},
                first_valid_utc=first_valid,last_valid_utc=last_valid,
                missing_seconds=dict(gaps),max_derived_mean_error_eur_mwh=max_mean_error,
                raw_source_hashes_verified=len(sources),source_hash_errors=0,duplicate_timestamps=0,
                timezone_and_dst_checks=True,all_prices_finite=True,
                da_and_capacity_complete=True,tests_passed=6)
    (BASE/'validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    manifest=[]
    for path in sorted((BASE/'processed').rglob('*')):
        if path.is_file():
            h=hashlib.sha256()
            with path.open('rb') as f:
                for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
            manifest.append(dict(path=str(path.relative_to(BASE)),bytes=path.stat().st_size,sha256=h.hexdigest()))
    (BASE/'data_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    main()
