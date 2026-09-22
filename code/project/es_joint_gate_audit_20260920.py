"""Read-only raw audit; outputs evidence, never production model input.

Official raw OMIE text and eSIOS fetch_<id>.json only. No APIs, credentials,
processed tables, interpolation, or inferred event times are used.
"""
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import hashlib
import json
import math
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from countries.ES.audit_pi_candidate_20260920 import expected_utc_quarters, parse_response, MADRID, iso
from src.data_ingestion.es.omie import parse_omie, standardize_omie_rows

IDS = (632,633,634,2130,680,681,682,683)
KINDS = ("da","ida1","ida2","ida3")
QH = timedelta(minutes=15)
# Previously reviewed direct announcements plus explicitly labelled date mapping.
CANCEL = {
    ("ida3","2025-03-18"): ("direct", "https://www.omie.es/sites/default/files/2025-03/instruccion_1_2025_es_0.pdf"),
    ("ida1","2025-04-20"): ("direct", "https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2025/04/sidc-intraday-auction-ida-cancelation-20250419122000/"),
    ("ida1","2025-11-01"): ("direct", "https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2025/10/sidc-intraday-auction-ida-cancelation-20251031143200/"),
    ("ida1","2025-02-01"): ("reviewed_D_plus_1_mapping", "https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2025/01/sidc-intraday-auction-ida-partial-decoupling-20250131141800/"),
    ("ida1","2026-04-16"): ("reviewed_D_plus_1_mapping", "https://www.nordpoolgroup.com/en/trading/Operational-Message-List/2026/04/sidc-intraday-auction-ida1-cancelation-20260415130100/"),
}

def spans(points):
    out=[]
    for t in sorted(points):
        if out and out[-1][1] == t: out[-1][1]=t+QH;out[-1][2]+=1
        else: out.append([t,t+QH,1])
    return [dict(start_utc=iso(a),end_exclusive_utc=iso(b),start_local=a.astimezone(MADRID).isoformat(),
                 end_exclusive_local=b.astimezone(MADRID).isoformat(),qh=n) for a,b,n in out]

def audit():
    assert version("tzdata") == "2026.4"
    grid=set(expected_utc_quarters());assert len(grid)==58364
    values={i:defaultdict(set) for i in IDS};sources=[];rejections=Counter()
    for p in sorted((ROOT/"data/raw/ES/esios").rglob("fetch_*.json")):
        if p.stem not in {f"fetch_{i}" for i in IDS}:continue
        iid=int(p.stem.split("_")[1])
        ind,rows,stats,digest,size=parse_response(p,iid,grid)
        rejections.update(stats)
        mp=p.with_suffix(".json.meta.json")
        meta=json.loads(mp.read_text(encoding="utf-8")) if mp.exists() else {}
        http=meta.get("http_status")
        if http is not None and http != 200:rows=[];rejections["http_not_200"]+=1
        if meta.get("sha256") and meta["sha256"] != digest:
            rows=[];rejections["recorded_hash_mismatch"]+=1
        sources.append(dict(path=str(p.relative_to(ROOT)),sha256=digest,bytes=size,indicator=iid,
            rows_target=len(rows),rejections=dict(stats),http_status=http,
            retrieved_at=meta.get("retrieved_at"),values_updated_at=ind.get("values_updated_at"),
            metadata_present=mp.exists(),metadata_sha256=hashlib.sha256(mp.read_bytes()).hexdigest() if mp.exists() else None,
            recorded_sha256_matches=meta.get("sha256")==digest,
            request_range={k:meta.get("request_params",{}).get(k) for k in ("start_date","end_date","time_trunc")},
            source_endpoint=f"https://api.esios.ree.es/indicators/{iid}"))
        for t,v in rows:values[iid][t].add(v)
    clean={i:{t:next(iter(v)) for t,v in s.items() if len(v)==1} for i,s in values.items()}
    afsummary={str(i):dict(present=len(clean[i]),missing_or_conflicting=len(grid-set(clean[i])),
        conflicts=sum(len(v)>1 for v in values[i].values()),missing_spans=spans(grid-set(clean[i]))) for i in IDS}
    prices={k:defaultdict(set) for k in KINDS};contracts={};empty=[];bad=[];omie_sources=[]
    for p in sorted((ROOT/"data/raw/ES/omie").rglob("*")):
        m=re.fullmatch(r"marginal(pdbc|pibc)_(\d{8})(\d{2})?\.(\d+)",p.name)
        if not m or not p.is_file():continue
        day=datetime.strptime(m[2],"%Y%m%d").date().isoformat()
        if not "2025-01-01"<=day<"2026-09-01":continue
        kind="da" if m[1]=="pdbc" else {"01":"ida1","02":"ida2","03":"ida3"}.get(m[3])
        if kind is None:continue
        raw=p.read_bytes();record=dict(path=str(p.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest(),
            bytes=len(raw),kind=kind,delivery_day=day,file_version=int(m[4]),
            source_url=f"https://www.omie.es/es/file-download?filename={p.name}&parents=marginal{m[1]}")
        try:
            rows=standardize_omie_rows(parse_omie(raw,kind,day),day)
            points=[]
            for r in rows:
                if (r["year"],r["month"],r["day"])!=tuple(map(int,day.split("-"))):
                    raise ValueError("source row delivery day mismatch")
                price=float(r["price_es_eur_mwh"])
                if not math.isfinite(price) or not r.get("utc_time"):raise ValueError("invalid price/time")
                start=datetime.fromisoformat(r["utc_time"].replace("Z","+00:00"))
                slots=tuple(start+QH*j for j in range(4 if r["period_granularity"]=="hour" else 1))
                if any(t not in grid or t.astimezone(MADRID).date().isoformat()!=day for t in slots):
                    raise ValueError("period outside delivery day")
                if kind=="ida3" and any(t.astimezone(MADRID).hour<12 for t in slots):
                    raise ValueError("IDA3 outside working delivery range")
                points.append((slots,price,r["period_granularity"]))
            record["rows"]=len(rows)
            if not rows:empty.append(dict(kind=kind,day=day,path=record["path"]))
            for slots,price,granularity in points:
                cid=f"{kind}:{day}:{iso(slots[0])}:{granularity}"
                contracts[cid]=slots
                for t in slots:prices[kind][t].add(price)
        except (ValueError,TypeError,KeyError,OverflowError):
            record["parse_validation_error"]=True;bad.append(record["path"])
        omie_sources.append(record)
    valid={k:{t for t,v in s.items() if len(v)==1} for k,s in prices.items()}
    expected={k:({t for t in grid if t.astimezone(MADRID).hour>=12} if k=="ida3" else grid) for k in KINDS}
    cancelled={k:set() for k in KINDS}
    for (k,day),evidence in CANCEL.items():
        cancelled[k].update(t for t in expected[k] if t.astimezone(MADRID).date().isoformat()==day)
    # Even conflicting price revisions must block a cancellation classification;
    # removing them from `valid` must not silently restore the slot as cancelled.
    cancellation_conflicts={k:len(cancelled[k]&prices[k].keys()) for k in KINDS}
    assert not any(cancellation_conflicts.values()),"cancelled session has prices: manual review required"
    spotsummary={k:dict(expected=len(expected[k]),present=len(valid[k]&expected[k]),
        confirmed_or_reviewed_cancelled=len(cancelled[k]),
        unknown_missing=len(expected[k]-valid[k]-cancelled[k]),
        conflicting_qh=sum(len(v)>1 for v in prices[k].values()),
        unknown_missing_spans=spans(expected[k]-valid[k]-cancelled[k])) for k in KINDS}
    common=set(grid)
    for i in IDS:common &= clean[i].keys()
    rawcommon=set(common)
    for k in KINDS:
        rawcommon &= valid[k] | (grid-expected[k])
        common &= valid[k] | cancelled[k] | (grid-expected[k])
    invalid_alpha={};alpha_pass=set()
    for t in sorted(grid & clean[632].keys() & clean[633].keys() & clean[680].keys() & clean[681].keys()):
        ru,rd,eu,ed=(clean[i][t] for i in (632,633,680,681))
        if min(ru,rd)<=0 or min(eu,ed)<0:invalid_alpha[iso(t)]="invalid_denominator_or_negative_energy";continue
        au,ad=eu/(ru*.25),ed/(rd*.25)
        if au+ad>1:invalid_alpha[iso(t)]="unmappable_alpha_sum_gt_1"
        else:alpha_pass.add(t)
    conditional=common & alpha_pass
    trimmed=set(conditional);rounds=0
    while True:
        rejected=set()
        for slots in contracts.values():
            present=set(slots)&trimmed
            if present and len(present)!=len(slots):rejected.update(present)
        if not rejected:break
        trimmed-=rejected;rounds+=1
    unknown_sessions=sorted({(k,t.astimezone(MADRID).date().isoformat()) for k in KINDS for t in expected[k]-valid[k]-cancelled[k]})
    result=dict(scope="raw structural audit; no model input approval",timezone="Europe/Madrid; UTC keys",
        tzdata=version("tzdata"),target_qh=len(grid),afrr=afsummary,spot=spotsummary,
        raw_common_qh=len(rawcommon),cancel_adjusted_common_qh=len(common),
        conditional_alpha_valid_qh=len(alpha_pass),conditional_joint_qh=len(conditional),
        contract_boundary_trimmed_candidate_qh=len(trimmed),contract_trim_rounds=rounds,
        candidate_spans=spans(trimmed),excluded_contract_edge_qh=spans(conditional-trimmed),
        invalid_alpha=invalid_alpha,unknown_sessions=[dict(kind=k,delivery_day=d) for k,d in unknown_sessions],
        cancellation_evidence=[dict(kind=k,delivery_day=d,evidence_kind=e[0],url=e[1]) for (k,d),e in CANCEL.items()],
        esios_sources=sources,omie_sources=omie_sources,raw_rejections=dict(rejections),
        empty_file_count=len(empty),empty_files=empty,omie_rejected_files=bad,
        approved_qh_count=0,formal_mask_generated=False,
        blockers=["gate1 units/time/population evidence", "gate2 historical rules and event mapping",
                  "price units/signs and immutable source/event provenance acceptance", "independent data review"],
        assumptions=["IDA3 noon-midnight working coverage, pending rule matrix",
                     "raw API timestamps provisionally treated as quarter starts only for conditional coverage",
                     "energy/capacity ratio provisional, not approved site activation",
                     "hourly contracts mapped for coverage only, never independent quarter trades"],
        no_fill=True,no_production_inputs=True)
    return result

if __name__=="__main__":
    result=audit()
    target=ROOT/"project/es_joint_gate_evidence_20260920_r2.json"
    with target.open("x",encoding="utf-8") as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:v for k,v in result.items() if k in {"target_qh","raw_common_qh","cancel_adjusted_common_qh","conditional_joint_qh","contract_boundary_trimmed_candidate_qh","approved_qh_count","invalid_alpha"}},ensure_ascii=False))
    print(json.dumps({"spot":{k:{n:v for n,v in d.items() if n!="unknown_missing_spans"} for k,d in result["spot"].items()},"candidate_count":len(result["candidate_spans"]),"source_files":len(result["esios_sources"])+len(result["omie_sources"])},ensure_ascii=False))
