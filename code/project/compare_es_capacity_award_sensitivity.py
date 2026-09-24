"""Compare full-fill V1, fixed-dispatch haircut, and optimize-mode sensitivity runs."""
import argparse
import csv
import gzip
import json
import mmap
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MARKETS = ('DA', 'ID', 'cap_up', 'cap_down', 'act_up', 'act_down')
NAME = {'DA_energy': 'DA', 'IDA_energy': 'ID'}
MADRID = ZoneInfo('Europe/Madrid')


def rates(path):
    result = {}
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            if row['quality_status'] in ('valid', 'zero_allocated'):
                result[(row['qh_start_utc'], row['direction'])] = float(row['award_rate_proxy'])
    return result


def monthly_rate_quality(path):
    grouped = defaultdict(lambda: {'expected': 0, 'valid': 0, 'rate_sum': 0.0})
    with gzip.open(path, 'rt', encoding='utf-8', newline='') as stream:
        for row in csv.DictReader(stream):
            key = (row['local_date'][:7], row['direction'])
            grouped[key]['expected'] += 1
            if row['quality_status'] in ('valid', 'zero_allocated'):
                grouped[key]['valid'] += 1
                grouped[key]['rate_sum'] += float(row['award_rate_proxy'])
    result = []
    for month in sorted({key[0] for key in grouped}):
        item = {'month': month}
        for direction in ('up', 'down'):
            values = grouped[(month, direction)]
            item[f'{direction}_expected_qh'] = values['expected']
            item[f'{direction}_valid_qh'] = values['valid']
            item[f'{direction}_mean_rate'] = values['rate_sum'] / values['valid'] if values['valid'] else None
        result.append(item)
    return result


def collect(path, *, award_rates=None):
    monthly = defaultdict(lambda: {name: 0.0 for name in MARKETS})
    quantities = defaultdict(lambda: {'up': 0.0, 'down': 0.0})
    missing = []
    executed_capacity_qh = set()
    with path.open(encoding='utf-8') as stream:
        rows = json.load(stream)
    for entry in rows:
        kind = entry['settlement_type']
        if kind in NAME:
            category = NAME[kind]
        elif kind == 'aFRR_capacity':
            category = 'cap_' + entry['direction']
        elif kind == 'aFRR_activation':
            category = 'act_' + entry['direction']
        else:
            raise ValueError(f'unknown settlement type: {kind}')
        month = entry['execution_day'][:7]
        cash = float(entry['cash_eur'])
        if kind == 'aFRR_capacity':
            executed_capacity_qh.add(entry['object_id'])
            quantities[month][entry['direction']] += float(entry['quantity'])
            if award_rates is not None:
                key = (entry['object_id'], entry['direction'])
                rate = award_rates.get(key)
                if rate is None and abs(float(entry['quantity'])) > 1e-8:
                    missing.append(key)
                    continue
                cash *= rate or 0.0
        monthly[month][category] += cash
    return monthly, quantities, missing, executed_capacity_qh


def monthly_efc(path):
    """Read only the top-level rows from a large result JSON without loading windows."""
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        start = data.find(b'"rows": [')
        months = data.find(b'"months":', start)
        end = data.rfind(b']', start, months)
        if min(start, months, end) < 0:
            raise ValueError(f'cannot locate result rows: {path}')
        rows = json.loads(data[start + len(b'"rows": '):end + 1].decode('utf-8'))
    grouped = defaultdict(float)
    for row in rows:
        month = datetime.fromisoformat(row['time']).astimezone(MADRID).strftime('%Y-%m')
        grouped[month] += float(row['efc'] or 0.0)
    return grouped


def comparison_normalizer(base_manifest, sens_manifest, base_input, sens_input):
    """Validate comparison modes and return discharge MW and EUR divisor."""
    sens_mode = sens_manifest.get('capacity_award_mode')
    if sens_mode is None and 'capacity_award_rate_proxy' in sens_manifest.get('scenario',''):
        sens_mode = 'optimize'  # first integrated runner did not persist the explicit mode
    if sens_mode != 'optimize':
        raise ValueError(f"sensitivity run must use capacity_award_mode=optimize, got {sens_mode!r}")
    if base_manifest.get('capacity_award_mode','full_fill') != 'full_fill':
        raise ValueError('baseline run must be full_fill')
    discharge_mw = float(base_input['discharge_mw'])
    if discharge_mw <= 0 or float(sens_input['discharge_mw']) != discharge_mw:
        raise ValueError('baseline and sensitivity runs must use the same positive discharge power')
    return discharge_mw,1000.0*discharge_mw


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--sensitivity', type=Path, required=True)
    parser.add_argument('--award-rate-file', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    base_manifest = json.loads((args.baseline / 'manifest.json').read_text(encoding='utf-8'))
    sens_manifest = json.loads((args.sensitivity / 'manifest.json').read_text(encoding='utf-8'))
    base_input = json.loads((args.baseline / 'solver_input.json').read_text(encoding='utf-8'))
    sens_input = json.loads((args.sensitivity / 'solver_input.json').read_text(encoding='utf-8'))
    discharge_mw,normalizer=comparison_normalizer(base_manifest,sens_manifest,base_input,sens_input)
    args.output.mkdir(parents=True)
    award_rates = rates(args.award_rate_file)
    base, base_mw, _, base_qh = collect(args.baseline / 'cash_ledger.json')
    fixed, _, missing, _ = collect(args.baseline / 'cash_ledger.json', award_rates=award_rates)
    if missing:
        raise ValueError(f'{len(set(missing))} nonzero baseline capacity QHs lack an award rate; no full-period fixed comparison')
    reopt, reopt_mw, _, reopt_qh = collect(args.sensitivity / 'cash_ledger.json')
    base_efc = monthly_efc(args.baseline / 'result.json')
    reopt_efc = monthly_efc(args.sensitivity / 'result.json')
    base_summary = json.loads((args.baseline / 'summary.json').read_text(encoding='utf-8'))
    sens_summary = json.loads((args.sensitivity / 'summary.json').read_text(encoding='utf-8'))
    if not base_summary['success'] or not sens_summary['success']:
        raise ValueError('both runs must have completed successfully')
    if base_qh != reopt_qh:
        raise ValueError(f'executed QH sets differ: V1-only={len(base_qh-reopt_qh)}, sensitivity-only={len(reopt_qh-base_qh)}')
    months = sorted(set(base) | set(reopt))
    if set(base) != set(reopt):
        raise ValueError('baseline and sensitivity ledger months differ')
    rows = []
    for month in months:
        item = {'month': month}
        for label, data in (('v1', base), ('fixed_haircut', fixed), ('reoptimized', reopt)):
            for market in MARKETS:
                item[f'{label}_{market}_kEUR_per_MW'] = data[month][market] / normalizer
            item[f'{label}_total_kEUR_per_MW'] = sum(data[month].values()) / normalizer
        for label, data in (('v1', base_mw), ('reoptimized', reopt_mw)):
            item[f'{label}_up_MW_QH'] = data[month]['up']
            item[f'{label}_down_MW_QH'] = data[month]['down']
        rows.append(item)
    with (args.output / 'monthly.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    efc_rows = []
    cum_base = cum_reopt = 0.0
    for month in months:
        if month.endswith('-01'):
            cum_base = cum_reopt = 0.0
        cum_base += base_efc[month]
        cum_reopt += reopt_efc[month]
        efc_rows.append(dict(month=month, v1_efc=base_efc[month],
                             reoptimized_efc=reopt_efc[month],
                             v1_cumulative_efc=cum_base,
                             reoptimized_cumulative_efc=cum_reopt))
    with (args.output / 'efc_monthly.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(efc_rows[0]))
        writer.writeheader()
        writer.writerows(efc_rows)
    rate_monthly = monthly_rate_quality(args.award_rate_file)
    with (args.output / 'award_rate_monthly.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rate_monthly[0]))
        writer.writeheader()
        writer.writerows(rate_monthly)
    totals = {label: sum(row[f'{label}_total_kEUR_per_MW'] for row in rows)
              for label in ('v1', 'fixed_haircut', 'reoptimized')}
    summary = dict(total_kEUR_per_MW=totals,
                   capacity_haircut_kEUR_per_MW=totals['fixed_haircut'] - totals['v1'],
                   reoptimization_effect_kEUR_per_MW=totals['reoptimized'] - totals['fixed_haircut'],
                   solver_seconds={'v1': base_summary['solver_seconds'],
                                   'reoptimized': sens_summary['solver_seconds']},
                   coverage={'v1': base_summary['coverage'], 'reoptimized': sens_summary['coverage']},
                   common_executed_qh=len(base_qh),
                   discharge_mw=discharge_mw,
                   award_rate_file=str(args.award_rate_file))
    (args.output / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    lines = ['# 西班牙 aFRR 容量收入中标率敏感性：V1、固定调度及重新求解', '',
             '单位：千欧元/MW。系数是同一历史 QH、同方向的系统已分配容量 ÷ 总报价容量；它不是本站实际中标率。',
             '本次仅折减容量收入，激活收入和完整容量物理承诺沿用 V1。', '',
             '| 情景 | 总收益 (k€/MW) | 与 V1 差额 (k€/MW) |', '|---|---:|---:|']
    for label, title in (('v1', 'V1 100%中标'), ('fixed_haircut', '固定 V1 决策，仅折减容量收入'),
                         ('reoptimized', '按系数重新求解')):
        lines.append(f"| {title} | {totals[label]:.3f} | {totals[label]-totals['v1']:+.3f} |")
    lines += ['', '| 月份 | V1 | 固定决策折减 | 重新求解 |', '|---|---:|---:|---:|']
    for row in rows:
        lines.append(f"| {row['month']} | {row['v1_total_kEUR_per_MW']:.3f} | "
                     f"{row['fixed_haircut_total_kEUR_per_MW']:.3f} | {row['reoptimized_total_kEUR_per_MW']:.3f} |")
    lines += ['', '### 重新求解的月度收益分项', '',
              '| 月份 | DA | ID | aFRR容量上 | aFRR容量下 | aFRR激活上 | aFRR激活下 |',
              '|---|---:|---:|---:|---:|---:|---:|']
    for row in rows:
        lines.append('| ' + row['month'] + ' | ' + ' | '.join(
            f"{row[f'reoptimized_{market}_kEUR_per_MW']:.3f}" for market in MARKETS) + ' |')
    lines += ['', 'V1、固定调度及重新求解的完整月度分项和上/下容量 MW·QH 见 `monthly.csv`。逐方向 QH 中标率代理算术均值及覆盖见 `award_rate_monthly.csv`。',
              '重新求解沿用入口的滚动窗口和年度EFC预算约束；与固定调度折减的差异反映了改变容量收益系数后滚动决策路径的影响，不等同于对全区间目标一次性全局再优化。逐月EFC及年内累计见 `efc_monthly.csv`。',
              f"本次使用储能功率为 {discharge_mw:g} MW；实际EFC月份范围和年度预算来源见 `efc_monthly.csv` 与 `summary.json`。",
              f"V1 求解器累计 {summary['solver_seconds']['v1']:.3f} 秒；敏感性重新求解累计 {summary['solver_seconds']['reoptimized']:.3f} 秒。",
              f"有效结算 QH 覆盖率：V1 {summary['coverage']['v1']:.2%}，敏感性 {summary['coverage']['reoptimized']:.2%}。"]
    (args.output / '结果对比.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == '__main__':
    main()
