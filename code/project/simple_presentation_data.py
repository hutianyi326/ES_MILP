"""Monthly 4-second JSON ledger and presentation inputs for archived Simple_MILP cases."""
import argparse
import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CASES = ["充100放100 · DA100%", "充100放100 · DA50%", "充100放100 · DA80%", "充50放100 · DA80%"]
MARKET = ["DA净收益", "Up容量", "Dn容量", "Up激活收支", "Dn激活收支", "Dn后续售电价值", "Up补能收支"]
ENERGY = ["DA充电", "DA放电", "Dn激活充电", "Up激活放电"]
COLUMNS = ENERGY + MARKET + ["当期收支合计", "含估值总收益"]
KEYS = ["da_net_eur", "capacity_up_eur", "capacity_down_eur", "activation_up_cash_eur", "activation_down_cash_eur", "down_resale_value_eur", "up_replenishment_cost_eur", "total_cash_eur", "total_with_value_eur"]


def stats(values, quantiles):
    v = values.dropna()
    return [None if v.empty else float(v.quantile(p)) for p in quantiles]


def run(dataset, base, asym, out):
    out.mkdir(parents=True, exist_ok=True)
    q = pd.read_csv(base/"quarter_hour_calculation_basis.csv")
    a = pd.read_csv(asym/"da_schedule_15min.csv")
    assert q.start_utc.equals(a.start_utc)
    q["asym_buy"] = a.charge_mwh_ac
    q["asym_sell"] = a.discharge_mwh_ac
    d = pd.read_csv(base/"daily_inputs.csv").set_index("date")
    expected = pd.read_csv(base/"monthly_scenarios.csv")
    alternate = pd.read_csv(asym/"monthly_results.csv").set_index("month")
    daily = pd.read_csv(base/"daily_scenarios.csv")
    adaily = pd.read_csv(asym/"daily_results.csv")
    report = []
    count = 0
    for path in sorted((dataset/"processed/prices_4s").glob("*.csv.gz")):
        month = path.name[:7]
        slots = q[q.month == month]
        raw = pd.read_csv(path)
        assert len(raw) == len(slots)*225
        assert np.array_equal(raw.start_utc.iloc[::225], slots.start_utc)
        ticks = pd.DatetimeIndex(pd.to_datetime(raw.start_utc, utc=True)).asi8
        assert np.all(np.diff(ticks)==ticks[1]-ticks[0])
        assert pd.Timestamp(raw.start_utc.iloc[1])-pd.Timestamp(raw.start_utc.iloc[0])==pd.Timedelta(seconds=4)
        hourly = slots.assign(hour=slots.start_europe_madrid.str[11:13].astype(int)).groupby("hour")
        cap = slots[["capacity_up_eur_mw_qh","capacity_down_eur_mw_qh"]]
        info = dict(month=month, capacity=hourly[list(cap)].mean().reindex(range(24)).values.tolist(),
                    cap_quantiles=[stats(cap[c],[.25,.5,.75]) for c in cap], activation={}, cases=[])
        hours = np.repeat(slots.start_europe_madrid.str[11:13].astype(int).to_numpy(),225)
        for direction in ["up","down"]:
            price=raw[f"activation_{direction}_eur_mwh"]
            pair=pd.DataFrame(dict(hour=hours,activation=price,da=raw.da_eur_mwh)).dropna()
            hourly_pair=pair.groupby("hour")[["activation","da"]].mean().reindex(range(24))
            spread=(pair.activation-pair.da)*(1 if direction=="up" else -1)
            info["activation"][direction]=dict(hourly=json.loads(hourly_pair.to_json(orient="values", double_precision=15)),
                spread=[float(spread.mean()) if len(spread) else None,*stats(spread,[.75,.25])], valid=len(pair))
        totals=np.zeros((4,len(COLUMNS)))
        archive=out/(month+".json.gz")
        with gzip.open(archive.with_suffix(".tmp"),"wt",encoding="utf-8",compresslevel=1) as f:
            meta=dict(month=month, timezone="Europe/Madrid",step_seconds=4, currency="EUR",energy_unit="MWh AC",
                      cases=CASES,case_columns=COLUMNS,price_columns=["DA","Up容量","Dn容量","Up激活","Dn激活","Up价格状态","Dn价格状态"],
                      parameters=dict(da_share=[1,.5,.8,.8],up_bid_mw=[0,50,20,20],dn_bid_mw=[0,50,20,10],eta=.92,capacity_bid=1,up_threshold=200,dn_threshold=0),
                      indexing="每日各数组第i行对应start_utc + 4*i秒(从0计)，case_rows按cases排序。容量价EUR/MW/15min，其他价格EUR/MWh。方向无价的激活收支及电量为null，合计取可计算部分。")
            meta["awards_mw_by_qh_layout"] = "各场景依次列出当天每15分钟的[Up中标MW,Dn中标MW]；第i个4秒点属于第i//225个15分钟。"
            f.write(json.dumps(meta,ensure_ascii=False)[:-1]+',"days":[\n')
            offset=0
            for j,(date,day) in enumerate(slots.groupby("date",sort=False)):
                n=len(day)*225
                part=raw.iloc[offset:offset+n]
                offset+=n
                da=part.da_eur_mwh.to_numpy()
                cu=part.capacity_up_eur_mw_qh.to_numpy()
                cd=part.capacity_down_eur_mw_qh.to_numpy()
                up=part.activation_up_eur_mwh.to_numpy()
                dn=part.activation_down_eur_mwh.to_numpy()
                p25,p75=d.loc[date,["da_p25","da_p75"]]
                awards = [np.column_stack(((cu[::225]>1)*up_mw, (cd[::225]>1)*dn_mw)).tolist()
                          for up_mw,dn_mw in [(0,0),(50,50),(20,20),(20,10)]]
                if j:f.write(",\n")
                f.write(json.dumps(dict(date=date,start_utc=part.start_utc.iloc[0],points=n,p25=p25,p75=p75,
                                        awards_mw_by_qh=awards),ensure_ascii=False)[:-1]+',"prices":')
                cols=["da_eur_mwh","capacity_up_eur_mw_qh","capacity_down_eur_mw_qh","activation_up_eur_mwh","activation_down_eur_mwh","up_price_status","down_price_status"]
                f.write(part[cols].to_json(orient="values",double_precision=15))
                f.write(',"case_rows":[')
                for k,(s,pu,pd_) in enumerate([(1,0,0),(.5,50,50),(.8,20,20),(.8,20,10)]):
                    buy=np.repeat((day.asym_buy if k==3 else day.da_charge_full_mwh*s).to_numpy(),225)/225
                    sell=np.repeat((day.asym_sell if k==3 else day.da_discharge_full_mwh*s).to_numpy(),225)/225
                    eu=((cu>1)&(up-da>200))*pu/900.
                    ed=((cd>1)&(da-dn>0))*pd_/900.
                    if pu:eu=np.where(np.isnan(up),np.nan,eu)
                    if pd_:ed=np.where(np.isnan(dn),np.nan,ed)
                    u_cash=eu*up if pu else np.zeros(n)
                    d_cash=-ed*dn if pd_ else np.zeros(n)
                    legs=np.column_stack(((sell-buy)*da,np.where(cu>1,cu*pu/225,0),np.where(cd>1,cd*pd_/225,0),u_cash,d_cash,ed*.92**2*p75,-eu/.92**2*p25))
                    rows=np.column_stack((buy,sell,ed,eu,legs,np.nansum(legs[:,:5],axis=1),np.nansum(legs,axis=1)))
                    totals[k]+=np.nansum(rows,axis=0)
                    if k:f.write(",")
                    f.write(pd.DataFrame(rows).to_json(orient="values",double_precision=15))
                f.write("]}")
            f.write("\n]}")
        for k,values in enumerate(totals):
            if k==3:
                ref=alternate.loc[month]
                energy=adaily[adaily.month==month]
            else:
                label=["100% DA","50% DA","80% DA"][k]
                ref=expected[(expected.scenario==label)&(expected.month==month)].iloc[0]
                energy=daily[(daily.scenario==label)&(daily.month==month)]
            target=[*energy[["da_buy_mwh","da_sell_mwh","down_energy_mwh","up_energy_mwh"]].sum(),*ref[KEYS]]
            np.testing.assert_allclose(values,target,rtol=0,atol=1e-4)
            info["cases"].append(values.tolist())
        archive.with_suffix(".tmp").replace(archive)
        count+=len(raw)
        report.append(info)
        print(month,len(raw),flush=True)
    assert count==11189700 and len(report)==17
    (out/"presentation.json").write_text(json.dumps(dict(labels=COLUMNS,cases=CASES,months=report),ensure_ascii=False,allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    p=argparse.ArgumentParser(__doc__)
    p.add_argument("--dataset",type=Path,default=ROOT/"input/datasets/ES/market_20250601_20261031_20261103")
    p.add_argument("--base",type=Path,default=ROOT/"output/simple_period_20250601_20261031_20261103")
    p.add_argument("--asym",type=Path,default=ROOT/"output/simple_asymmetric_50_100_200_80pct_20261104")
    p.add_argument("--out",type=Path,required=True)
    args=p.parse_args()
    run(args.dataset,args.base,args.asym,args.out)
