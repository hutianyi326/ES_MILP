"""Build a compact, auditable Markdown/SVG presentation from an ES MILP run."""
from __future__ import annotations

import argparse
import html
import json
import math
import mmap
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

MADRID = ZoneInfo('Europe/Madrid')
MARKETS = ('DA', 'ID', 'cap_up', 'cap_down', 'act_up', 'act_down')
LABELS = {
    'DA': 'DA', 'ID': 'ID', 'cap_up': 'aFRR capacity up',
    'cap_down': 'aFRR capacity down', 'act_up': 'aFRR activation up',
    'act_down': 'aFRR activation down',
}
LABELS_ZH = {
    'DA': 'DA电能', 'ID': 'ID电能', 'cap_up': 'aFRR容量上调',
    'cap_down': 'aFRR容量下调', 'act_up': 'aFRR激活上调',
    'act_down': 'aFRR激活下调',
}
COLORS = {
    'DA': '#4472C4', 'ID': '#ED7D31', 'cap_up': '#70AD47',
    'cap_down': '#A5A5A5', 'act_up': '#FFC000', 'act_down': '#8064A2',
}


def _read_rows(path: Path) -> list[dict]:
    """Read only the top-level rows array from a large result JSON."""
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        marker = b'"rows": ['
        start = data.find(marker)
        months = data.find(b'"months":', start)
        end = data.rfind(b']', start, months)
        if min(start, months, end) < 0:
            raise ValueError(f'Cannot locate result rows in {path}')
        # Keep the opening '[' in the extracted array.
        return json.loads(data[start + len(b'"rows": '):end + 1].decode('utf-8'))


def _top_level_scalars(path: Path, wanted: set[str]) -> dict:
    """Extract selected scalar config values without loading the huge solver input."""
    patterns = {
        key: re.compile(rb'^  "' + re.escape(key.encode()) + rb'"\s*:\s*([^,\r\n]+)', re.M)
        for key in wanted
    }
    result = {}
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        for key, pattern in patterns.items():
            match = pattern.search(data)
            if not match:
                raise ValueError(f'Missing top-level input field {key!r}')
            result[key] = json.loads(match.group(1).strip().decode('utf-8'))
    return result


def _iter_json_array(path: Path):
    """Iterate an array of JSON objects from disk with bounded memory."""
    with path.open('rb') as stream, mmap.mmap(stream.fileno(), 0, access=mmap.ACCESS_READ) as data:
        i = data.find(b'[') + 1
        if i == 0:
            raise ValueError(f'Expected a JSON array in {path}')
        size = len(data)
        while i < size:
            while i < size and data[i] in b' \r\n\t,':
                i += 1
            if i >= size or data[i] == ord(']'):
                return
            if data[i] != ord('{'):
                raise ValueError(f'Expected object at byte {i} in {path}')
            start = i
            depth = 0
            in_string = False
            escaped = False
            while i < size:
                byte = data[i]
                if in_string:
                    if escaped:
                        escaped = False
                    elif byte == ord('\\'):
                        escaped = True
                    elif byte == ord('"'):
                        in_string = False
                elif byte == ord('"'):
                    in_string = True
                elif byte == ord('{'):
                    depth += 1
                elif byte == ord('}'):
                    depth -= 1
                    if depth == 0:
                        i += 1
                        yield json.loads(data[start:i].decode('utf-8'))
                        break
                i += 1
            else:
                raise ValueError(f'Unclosed JSON object in {path}')


def _madrid_time(row: dict) -> datetime:
    value = datetime.fromisoformat(row['time'].replace('Z', '+00:00'))
    return value.astimezone(MADRID)


def _formal_rows(rows: list[dict], start: datetime, end: datetime) -> list[dict]:
    return [row for row in rows
            if start <= datetime.fromisoformat(row['time'].replace('Z', '+00:00')) < end]


def aggregate(rows: list[dict], discharge_mw: float) -> dict:
    monthly = defaultdict(lambda: {'cash_eur': {m: 0.0 for m in MARKETS}, 'valid_qh': 0,
                                   'total_qh': 0, 'efc': 0.0})
    total = {m: 0.0 for m in MARKETS}
    valid_rows = {}
    daily = defaultdict(lambda: {'valid_qh': 0, 'total_qh': 0})
    hourly_qhs = defaultdict(dict)
    for row in rows:
        local = _madrid_time(row)
        month = local.strftime('%Y-%m')
        month_row = monthly[month]
        month_row['total_qh'] += 1
        daily[local.date().isoformat()]['total_qh'] += 1
        if row.get('efc') is not None:
            month_row['efc'] += float(row['efc'])
        cash = row.get('cash')
        if cash is None:
            continue
        month_row['valid_qh'] += 1
        daily[local.date().isoformat()]['valid_qh'] += 1
        valid_rows[row['qh_id']] = row
        for market in MARKETS:
            value = float(cash.get(market, 0.0) or 0.0)
            month_row['cash_eur'][market] += value
            total[market] += value
        offset = int(local.utcoffset().total_seconds() // 60)
        hour_key = (local.date().isoformat(), local.hour, offset)
        hourly_qhs[hour_key][local.minute] = {m: float(cash.get(m, 0.0) or 0.0) for m in MARKETS}

    complete_hours = []
    for (day, hour, _offset), qhs in hourly_qhs.items():
        if set(qhs) != {0, 15, 30, 45}:
            continue
        month = int(day[5:7])
        components = {m: sum(qhs[minute][m] for minute in (0, 15, 30, 45)) /
                      (1000.0 * discharge_mw) for m in MARKETS}
        complete_hours.append({'date': day, 'hour': hour, 'quarter': (month - 1) // 3 + 1,
                               'components': components})

    hours = _hourly_means(complete_hours, range(24))
    quarters = {f'Q{q}': _hourly_means([h for h in complete_hours if h['quarter'] == q], range(24))
                for q in range(1, 5)}
    monthly_hours = _monthly_hourly_means(complete_hours)
    return {'monthly': dict(monthly), 'market_eur': total, 'valid_rows': valid_rows,
            'complete_hours': complete_hours, 'hours': hours, 'quarters': quarters,
            'monthly_hours': monthly_hours, 'daily': dict(daily),
            'total_eur': sum(total.values()), 'total_efc': sum(v['efc'] for v in monthly.values()),
            'valid_qh': sum(v['valid_qh'] for v in monthly.values()),
            'total_qh': sum(v['total_qh'] for v in monthly.values()), 'discharge_mw': discharge_mw}


def _hourly_means(hours: list[dict], bins) -> list[dict]:
    sums = {hour: {m: 0.0 for m in MARKETS} for hour in bins}
    counts = {hour: 0 for hour in bins}
    for item in hours:
        counts[item['hour']] += 1
        for market in MARKETS:
            sums[item['hour']][market] += item['components'][market]
    return [{'hour': hour, 'count': counts[hour],
             'components': {m: sums[hour][m] / counts[hour] if counts[hour] else 0.0 for m in MARKETS}}
            for hour in bins]


def _monthly_hourly_means(hours: list[dict]) -> dict[str, list[dict]]:
    grouped = defaultdict(list)
    for item in hours:
        grouped[item['date'][:7]].append(item)
    result = {}
    for month, month_hours in sorted(grouped.items()):
        means = _hourly_means(month_hours, range(24))
        result[month] = [{'hour': row['hour'], 'count': row['count'],
                          'total_kEUR_per_MW': sum(row['components'].values())}
                         for row in means]
    return result


def _expected_qh_for_day(day: str) -> int:
    local_date = datetime.fromisoformat(day).date()
    start = datetime.combine(local_date, datetime.min.time(), tzinfo=MADRID)
    end = datetime.combine(local_date.fromordinal(local_date.toordinal() + 1),
                           datetime.min.time(), tzinfo=MADRID)
    return int((end.astimezone(ZoneInfo('UTC')) - start.astimezone(ZoneInfo('UTC'))).total_seconds() / 900)


def _scale_series(rows: list[dict], factor: float) -> list[dict]:
    return [{'hour': row['hour'], 'count': row['count'],
             'components': {m: row['components'][m] * factor for m in MARKETS}}
            for row in rows]


def _nice_tick_step(span: float) -> int:
    target = max(span / 10.0, 1.0)
    magnitude = 10 ** math.floor(math.log10(target))
    for multiplier in (1, 2, 5, 10):
        step = multiplier * magnitude
        if step >= target:
            return int(step)
    return int(10 * magnitude)


def _rolling_12m(months: dict, discharge_mw: float) -> list[dict]:
    available = set(months)
    results = []
    for end_month in sorted(available):
        year, month = map(int, end_month.split('-'))
        end_index = year * 12 + month - 1
        window = []
        for index in range(end_index - 11, end_index + 1):
            window_year, month_index = divmod(index, 12)
            window.append(f'{window_year:04d}-{month_index + 1:02d}')
        if not all(key in available for key in window):
            continue
        total_eur = sum(sum(months[key]['cash_eur'].values()) for key in window)
        results.append({'month': end_month, 'window_start': window[0], 'window_end': end_month,
                        'total_eur': total_eur, 'kEUR': total_eur / 1000,
                        'kEUR_per_MW': total_eur / (1000 * discharge_mw)})
    return results


def _rolling_12m_svg(rows: list[dict], path: Path,
                     v1_rows: list[dict] | None = None) -> None:
    width, height = 1480, 540
    left, right, top, bottom = 98, 30, 76, 100
    plot_w, plot_h = width - left - right, height - top - bottom
    v1_rows = v1_rows or []
    v1_by_month = {r['month']: r for r in v1_rows}
    aligned_v1 = [v1_by_month[r['month']] for r in rows if r['month'] in v1_by_month]
    values = [r['kEUR_per_MW'] for r in rows] + [r['kEUR_per_MW'] for r in aligned_v1]
    low_data, high_data = min(values + [0.0]), max(values + [0.0])
    step = _nice_tick_step(max(high_data - low_data, 1.0))
    low = math.floor(low_data / step) * step
    while low + 10 * step < high_data:
        step = _nice_tick_step(step + 1)
        low = math.floor(low_data / step) * step
    high = low + 10 * step

    def y(value):
        return top + (high - value) / (high - low) * plot_h

    band = plot_w / max(len(rows), 1)
    x_by_month = {row['month']: left + band * (i + 0.5) for i, row in enumerate(rows)}
    coords = [(x_by_month[row['month']], y(row['kEUR_per_MW'])) for row in rows]
    v1_coords = [(x_by_month[row['month']], y(row['kEUR_per_MW']))
                 for row in aligned_v1]
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#263238}.tick{font-size:13px}.xlabel{font-size:12px}.title{font-size:21px;font-weight:600}.axis{font-size:14px}</style>',
             f'<text class="title" x="{width/2}" y="32" text-anchor="middle">{html.escape("滚动12个月单位功率收益")}</text>']
    for tick in range(11):
        value = low + tick * step
        yy = y(value)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{width-right}" y2="{yy:.2f}" stroke="#d9dfe5"/>')
        parts.append(f'<text class="tick" x="{left-10}" y="{yy+4:.2f}" text-anchor="end">{value:d}</text>')
    if coords:
        parts.append('<polyline fill="none" stroke="#2878a5" stroke-width="3" points="' +
                     ' '.join(f'{x:.2f},{yy:.2f}' for x, yy in coords) + '"/>')
    if v1_coords:
        parts.append('<polyline fill="none" stroke="#e87522" stroke-width="3" points="' +
                     ' '.join(f'{x:.2f},{yy:.2f}' for x, yy in v1_coords) + '"/>')
    for row, (x, yy) in zip(rows, coords):
        period = f'{row["window_start"].replace("-", "/")}–{row["window_end"].replace("-", "/")}'
        parts.append(f'<circle cx="{x:.2f}" cy="{yy:.2f}" r="5" fill="#2878a5"><title>{period}: {row["kEUR_per_MW"]:.2f} kEUR/MW</title></circle>')
        parts.append(f'<text class="xlabel" x="{x:.2f}" y="{top+plot_h+23}" text-anchor="middle">{row["month"].replace("-", "/")}</text>')
    for row, (x, yy) in zip(aligned_v1, v1_coords):
        period = f'{row["window_start"].replace("-", "/")}–{row["window_end"].replace("-", "/")}'
        parts.append(f'<circle cx="{x:.2f}" cy="{yy:.2f}" r="5" fill="#e87522"><title>V1 100%中标；{period}: {row["kEUR_per_MW"]:.2f} kEUR/MW</title></circle>')
    if v1_coords:
        legend_y = height - 25
        parts.extend([f'<line x1="{left+plot_w/2-170}" y1="{legend_y-4}" x2="{left+plot_w/2-140}" y2="{legend_y-4}" stroke="#2878a5" stroke-width="3"/>',
                      f'<text class="axis" x="{left+plot_w/2-132}" y="{legend_y}" >含供需系数（重新优化）</text>',
                      f'<line x1="{left+plot_w/2+72}" y1="{legend_y-4}" x2="{left+plot_w/2+102}" y2="{legend_y-4}" stroke="#e87522" stroke-width="3"/>',
                      f'<text class="axis" x="{left+plot_w/2+110}" y="{legend_y}">V1（100%中标）</text>'])
    zero = y(0)
    parts.extend([f'<line x1="{left}" y1="{zero:.2f}" x2="{width-right}" y2="{zero:.2f}" stroke="#37474f" stroke-width="1.4"/>',
                  f'<text class="axis" x="20" y="{top+plot_h/2:.1f}" text-anchor="middle" transform="rotate(-90 20 {top+plot_h/2:.1f})">收益（kEUR/MW）</text>',
                  '</svg>'])
    path.write_text('\n'.join(parts), encoding='utf-8')


def average_capacity(ledger_path: Path, valid_qh_ids: set[str], total_qh: int) -> dict:
    by_qh = defaultdict(lambda: {m: 0.0 for m in MARKETS})
    for entry in _iter_json_array(ledger_path):
        settlement = entry['settlement_type']
        if settlement in ('DA_energy', 'IDA_energy'):
            try:
                qh_id = json.loads(entry['object_id'])[-1]
            except (TypeError, json.JSONDecodeError):
                continue
            market = 'DA' if settlement == 'DA_energy' else 'ID'
            # Day-ahead and intraday ledgers can contain multiple signed
            # transactions for a delivery QH; net them before taking the mean.
            quantity = abs(float(entry['quantity']))
            direction = str(entry.get('direction', '')).lower()
            mw = -quantity if direction in ('buy', 'charge') else quantity
        else:
            qh_id = entry['object_id']
            if settlement == 'aFRR_capacity':
                market = 'cap_' + entry['direction']
                mw = abs(float(entry['quantity']))
            elif settlement == 'aFRR_activation':
                market = 'act_' + entry['direction']
                quantity = abs(float(entry['quantity']))
                unit = entry.get('quantity_unit')
                duration = float(entry.get('hours') or 0.25)
                mw = quantity / duration if unit == 'MWh' else quantity
            else:
                continue
        if qh_id in valid_qh_ids:
            by_qh[qh_id][market] += mw
    denom = max(total_qh, 1)
    averages = {market: sum(row[market] for row in by_qh.values()) / denom for market in MARKETS}
    averages['spot_net_da_id'] = sum(row['DA'] + row['ID'] for row in by_qh.values()) / denom
    averages['reserve_both_directions'] = sum(row['cap_up'] + row['cap_down']
                                               for row in by_qh.values()) / denom
    return averages


def _chart_svg(title: str, unit: str, labels: list[str], values: list[dict], path: Path,
               *, width: int = 1500, height: int = 560) -> None:
    left, right, top, bottom = 100, 28, 74, 148 if len(labels) > 24 else 122
    plot_w, plot_h = width - left - right, height - top - bottom
    lows, highs = [], []
    for item in values:
        positives = sum(max(0.0, item['components'][m]) for m in MARKETS)
        negatives = sum(min(0.0, item['components'][m]) for m in MARKETS)
        lows.append(negatives)
        highs.append(positives)
    data_low = min(lows + [0.0])
    data_high = max(highs + [0.0])
    span = max(data_high - data_low, 1.0)
    tick_step = _nice_tick_step(span)
    low = math.floor(data_low / tick_step) * tick_step
    while low + 10 * tick_step < data_high:
        tick_step = _nice_tick_step(tick_step + 1)
        low = math.floor(data_low / tick_step) * tick_step
    high = low + 10 * tick_step
    def y(v):
        return top + (high - v) / (high - low) * plot_h
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#263238}.tick{font-size:13px}.xlabel{font-size:12px}.legend{font-size:13px}.title{font-size:21px;font-weight:600}.axis{font-size:14px}</style>',
             f'<text class="title" x="{width/2:.1f}" y="30" text-anchor="middle">{html.escape(title)}</text>']
    for tick in range(11):
        val = low + tick * tick_step
        yy = y(val)
        parts.append(f'<line x1="{left}" y1="{yy:.2f}" x2="{width-right}" y2="{yy:.2f}" stroke="#d9dfe5"/>')
        parts.append(f'<text class="tick" x="{left-10}" y="{yy+4:.2f}" text-anchor="end">{val:d}</text>')
    zero = y(0)
    parts.append(f'<line x1="{left}" y1="{zero:.2f}" x2="{width-right}" y2="{zero:.2f}" stroke="#37474f" stroke-width="1.4"/>')
    parts.append(f'<text class="axis" x="20" y="{top+plot_h/2:.1f}" text-anchor="middle" transform="rotate(-90 20 {top+plot_h/2:.1f})">{html.escape(unit)}</text>')
    band = plot_w / max(len(labels), 1)
    bar_w = min(band * 0.72, 45 if len(labels) > 24 else 54)
    for idx, (label, item) in enumerate(zip(labels, values)):
        cx = left + band * (idx + 0.5)
        positive = 0.0
        negative = 0.0
        for market in MARKETS:
            val = item['components'][market]
            if val >= 0:
                y0, y1 = y(positive), y(positive + val)
                positive += val
            else:
                y0, y1 = y(negative), y(negative + val)
                negative += val
            if abs(val) > 1e-12:
                parts.append(f'<rect x="{cx-bar_w/2:.2f}" y="{min(y0,y1):.2f}" width="{bar_w:.2f}" height="{max(abs(y1-y0),0.7):.2f}" fill="{COLORS[market]}"/>')
        parts.append(f'<text class="xlabel" x="{cx:.2f}" y="{top+plot_h+23}" text-anchor="middle">{html.escape(label)}</text>')
    legend_y = height - 46
    step = plot_w / len(MARKETS)
    for i, market in enumerate(MARKETS):
        x0 = left + i * step
        parts.append(f'<rect x="{x0:.1f}" y="{legend_y}" width="14" height="14" fill="{COLORS[market]}"/>')
        parts.append(f'<text class="legend" x="{x0+20:.1f}" y="{legend_y+12}">{html.escape(LABELS_ZH[market])}</text>')
    parts.append('</svg>')
    path.write_text('\n'.join(parts), encoding='utf-8')


def _monthly_hourly_heatmap(monthly_hours: dict[str, list[dict]], path: Path) -> None:
    width, left, right, top, row_h, bottom = 1580, 112, 24, 82, 30, 94
    months = sorted(monthly_hours)
    cell_w = (width - left - right) / 24
    height = top + len(months) * row_h + bottom
    vals = [r['total_kEUR_per_MW'] for month in months for r in monthly_hours[month] if r['count']]
    scale = max((max((abs(v) for v in vals), default=0.0)), 1e-12)

    def color(value: float) -> str:
        intensity = min(abs(value) / scale, 1.0)
        end = (28, 90, 150) if value >= 0 else (180, 55, 55)
        start = (247, 249, 251)
        rgb = tuple(round(start[i] + intensity * (end[i] - start[i])) for i in range(3))
        return '#%02x%02x%02x' % rgb

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<style>text{font-family:Segoe UI,Arial,sans-serif;fill:#263238}.tick{font-size:12px}.cell{font-size:10px}.title{font-size:21px;font-weight:600}.axis{font-size:14px}</style>',
             f'<text class="title" x="{width/2}" y="32" text-anchor="middle">按月和小时的平均总收益热力图</text>']
    for hour in range(24):
        x = left + hour * cell_w + cell_w / 2
        parts.append(f'<text class="tick" x="{x:.1f}" y="{top-12}" text-anchor="middle">{hour}</text>')
    for ridx, month in enumerate(months):
        y = top + ridx * row_h
        parts.append(f'<text class="tick" x="{left-10}" y="{y+row_h*0.68:.1f}" text-anchor="end">{month.replace("-", "/")}</text>')
        for hour, item in enumerate(monthly_hours[month]):
            x = left + hour * cell_w
            if item['count']:
                value = item['total_kEUR_per_MW']
                parts.append(f'<rect x="{x+0.5:.1f}" y="{y+0.5:.1f}" width="{cell_w-1:.1f}" height="{row_h-1:.1f}" fill="{color(value)}" stroke="white"><title>{month} {hour:02d}:00，平均 {value:.2f} kEUR/MW，完整样本 {item["count"]} 小时</title></rect>')
                text_color = 'white' if abs(value) / scale > 0.55 else '#263238'
                parts.append(f'<text class="cell" x="{x+cell_w/2:.1f}" y="{y+row_h*0.67:.1f}" text-anchor="middle" fill="{text_color}">{value:.2f}</text>')
            else:
                parts.append(f'<rect x="{x+0.5:.1f}" y="{y+0.5:.1f}" width="{cell_w-1:.1f}" height="{row_h-1:.1f}" fill="#eceff1" stroke="white"><title>{month} {hour:02d}:00，无完整有效小时</title></rect>')
    y0 = top + len(months) * row_h + 38
    parts.extend([f'<text class="axis" x="{left}" y="{y0}">平均收益（kEUR/MW）</text>',
                  f'<rect x="{left+205}" y="{y0-15}" width="22" height="16" fill="#b43737"/>',
                  f'<text class="tick" x="{left+233}" y="{y0-2}">负收益</text>',
                  f'<rect x="{left+320}" y="{y0-15}" width="22" height="16" fill="#f7f9fb" stroke="#cfd8dc"/>',
                  f'<text class="tick" x="{left+348}" y="{y0-2}">接近零</text>',
                  f'<rect x="{left+435}" y="{y0-15}" width="22" height="16" fill="#1c5a96"/>',
                  f'<text class="tick" x="{left+463}" y="{y0-2}">正收益</text>', '</svg>'])
    path.write_text('\n'.join(parts), encoding='utf-8')


def _money_table(months: dict, discharge_mw: float, years: list[int], per_mw: bool) -> str:
    unit = 'kEUR/MW' if per_mw else 'kEUR'
    columns = ['月份'] + [LABELS_ZH[m] for m in MARKETS] + ['合计']
    lines = ['| ' + ' | '.join(columns) + ' |', '| ' + ' | '.join(['---'] * len(columns)) + ' |']
    for year in years:
        year_rows = [m for m in sorted(months) if int(m[:4]) == year]
        annual = {market: sum(months[m]['cash_eur'][market] for m in year_rows) for market in MARKETS}
        for month in year_rows:
            values = months[month]['cash_eur']
            converted = {m: values[m] / (1000 * discharge_mw if per_mw else 1000) for m in MARKETS}
            total = sum(converted.values())
            lines.append('| ' + ' | '.join([month.replace('-', '/')]
                           + [f'{converted[m]:,.2f}' for m in MARKETS] + [f'{total:,.2f}']) + ' |')
        annual_c = {m: annual[m] / (1000 * discharge_mw if per_mw else 1000) for m in MARKETS}
        month_count = max(len(year_rows), 1)
        average_c = {m: annual_c[m] / month_count for m in MARKETS}
        lines.append('| ' + ' | '.join([f'**{year}年月均（{month_count}个月）**'] +
                   [f'**{average_c[m]:,.2f}**' for m in MARKETS] +
                   [f'**{sum(average_c.values()):,.2f}**']) + ' |')
        lines.append('| ' + ' | '.join([f'**{year}年合计**'] +
                   [f'**{annual_c[m]:,.2f}**' for m in MARKETS] +
                   [f'**{sum(annual_c.values()):,.2f}**']) + ' |')
    return f'单位：{unit}。\n\n' + '\n'.join(lines)


def _rolling_12m_table(rows: list[dict], v1_rows: list[dict] | None = None) -> str:
    v1_by_month = {r['month']: r for r in (v1_rows or [])}
    if v1_rows is None:
        lines = ['| 统计月份 | 对应12个月窗口 | 滚动收益（kEUR/MW） |', '|---|---|---:|']
    else:
        lines = ['| 统计月份 | 对应12个月窗口 | 含供需系数（kEUR/MW） | V1 100%中标（kEUR/MW） | 差额：V1−含系数 |', '|---|---|---:|---:|---:|']
    for row in rows:
        window = f'{row["window_start"].replace("-", "/")}–{row["window_end"].replace("-", "/")}'
        if v1_rows is None:
            lines.append(f'| {row["month"].replace("-", "/")} | {window} | {row["kEUR_per_MW"]:,.2f} |')
        else:
            v1_value = v1_by_month.get(row['month'], {}).get('kEUR_per_MW')
            v1_cell = f'{v1_value:,.2f}' if v1_value is not None else '—'
            delta = f'{v1_value-row["kEUR_per_MW"]:,.2f}' if v1_value is not None else '—'
            lines.append(f'| {row["month"].replace("-", "/")} | {window} | {row["kEUR_per_MW"]:,.2f} | {v1_cell} | {delta} |')
    return '\n'.join(lines)


def _rolling_v1_from_monthly_csv(path: Path) -> list[dict]:
    import csv
    with path.open(encoding='utf-8-sig', newline='') as stream:
        records = {row['month']: float(row['v1_total_kEUR_per_MW'])
                   for row in csv.DictReader(stream)}
    results = []
    for end_month in sorted(records):
        year, month = map(int, end_month.split('-'))
        end_index = year * 12 + month - 1
        window = []
        for index in range(end_index - 11, end_index + 1):
            window_year, month_index = divmod(index, 12)
            window.append(f'{window_year:04d}-{month_index + 1:02d}')
        if all(key in records for key in window):
            results.append({'month': end_month, 'window_start': window[0],
                            'window_end': end_month,
                            'kEUR_per_MW': sum(records[key] for key in window)})
    return results


def build(run_dir: Path, output_dir: Path, v1_monthly_csv: Path | None = None) -> Path:
    if output_dir.exists():
        raise FileExistsError(output_dir)
    manifest = json.loads((run_dir / 'manifest.json').read_text(encoding='utf-8'))
    result_path = run_dir / 'result.json'
    summary_path = run_dir / 'summary.json'
    summary = json.loads(summary_path.read_text(encoding='utf-8'))
    config = _top_level_scalars(run_dir / 'solver_input.json', {
        'charge_mw', 'discharge_mw', 'e_min_mwh', 'e_max_mwh', 'e_initial_mwh',
        'e_terminal_mwh', 'eta_charge', 'eta_discharge', 'reserve_limit_up_mw',
        'reserve_limit_down_mw', 'data_scope',
    })
    rows = _read_rows(result_path)
    start = datetime.fromisoformat(str(manifest['formal_start']))
    end = datetime.fromisoformat(str(manifest['formal_end']))
    rows = _formal_rows(rows, start, end)
    data = aggregate(rows, float(config['discharge_mw']))
    capacity_avg = average_capacity(run_dir / 'cash_ledger.json', set(data['valid_rows']), data['total_qh'])
    output_dir.mkdir(parents=True)

    months = data['monthly']
    years = sorted({int(m[:4]) for m in months})
    annual = {}
    complete_dates = {
        day for day, item in data['daily'].items()
        if item['total_qh'] == _expected_qh_for_day(day) and item['valid_qh'] == _expected_qh_for_day(day)
    }
    formal_start_date = start.astimezone(MADRID).date()
    formal_end_date = end.astimezone(MADRID).date()
    for year in years:
        monthly_keys = [m for m in months if int(m[:4]) == year]
        cash = {market: sum(months[m]['cash_eur'][market] for m in monthly_keys) for market in MARKETS}
        year_start = max(formal_start_date, datetime(year, 1, 1).date())
        year_end = min(formal_end_date, datetime(year + 1, 1, 1).date())
        total_days = max((year_end - year_start).days, 0)
        complete_days = sum(1 for day in complete_dates if year_start.isoformat() <= day < year_end.isoformat())
        annual[year] = {'cash_eur': cash, 'efc': sum(months[m]['efc'] for m in monthly_keys),
                        'total_qh': sum(months[m]['total_qh'] for m in monthly_keys),
                        'valid_qh': sum(months[m]['valid_qh'] for m in monthly_keys),
                        'complete_days': complete_days, 'total_days': total_days}
    rolling_12m = _rolling_12m(months, data['discharge_mw'])
    v1_rolling_12m = _rolling_v1_from_monthly_csv(v1_monthly_csv) if v1_monthly_csv else None

    month_names = sorted(months)
    _chart_svg('月度收益分解', '收入（kEUR）', [m.replace('-', '/') for m in month_names],
               [{'components': {k: v / 1000 for k, v in months[m]['cash_eur'].items()}} for m in month_names],
               output_dir / 'monthly_revenue_kEUR.svg')
    _chart_svg('月度单位功率收益分解', '收入（kEUR / MW）', [m.replace('-', '/') for m in month_names],
               [{'components': {k: v / (1000 * data['discharge_mw']) for k, v in months[m]['cash_eur'].items()}} for m in month_names],
               output_dir / 'monthly_revenue_kEUR_per_MW.svg')
    _rolling_12m_svg(rolling_12m, output_dir / 'rolling_12m_revenue_kEUR_per_MW.svg', v1_rolling_12m)
    hour_labels = [str(i) for i in range(24)]
    hourly_scaled = _scale_series(data['hours'], 1000.0)
    _chart_svg('全周期小时平均收益分解', '平均收益（kEUR/MW × 10⁻³）', hour_labels, hourly_scaled,
               output_dir / 'hourly_average_kEUR_per_MW.svg')
    _monthly_hourly_heatmap(data['monthly_hours'], output_dir / 'monthly_hourly_heatmap_kEUR_per_MW.svg')
    quarter_files = []
    for quarter, values in data['quarters'].items():
        filename = f'{quarter.lower()}_hourly_average_kEUR_per_MW.svg'
        _chart_svg(f'{quarter} 小时平均收益分解', '平均收益（kEUR/MW × 10⁻³）', hour_labels,
                   _scale_series(values, 1000.0), output_dir / filename, width=1000, height=410)
        quarter_files.append((quarter, filename))

    total = data['total_eur']
    total_per_mw = total / (1000 * data['discharge_mw'])
    valid_qh = max(data['valid_qh'], 1)
    raw_complete = summary.get('quality', {}).get('raw_field_complete_qh')
    quality = summary.get('quality', {})
    award = manifest.get('award_rate_source') or {}
    mode = manifest.get('capacity_award_mode')
    if mode is None:
        mode = 'optimize' if 'capacity_award_rate_proxy' in manifest.get('scenario', '') else 'full_fill'
    source_ids = sorted({str(item.get('indicator')) for item in manifest.get('source_files', [])
                         if item.get('indicator') is not None}, key=lambda x: int(x))
    usable_mwh = float(config['e_max_mwh']) - float(config['e_min_mwh'])
    efc_denominator = 2 * usable_mwh
    income_lines = ['| 市场 | 收益（kEUR） | 收益（kEUR/MW） | 占净总收益 |', '|---|---:|---:|---:|']
    for market in MARKETS:
        eur = data['market_eur'][market]
        share = eur / total * 100 if total else 0.0
        income_lines.append(f'| {LABELS_ZH[market]} | {eur/1000:,.2f} | {eur/(1000*data["discharge_mw"]):,.2f} | {share:,.2f}% |')
    income_lines.append(f'| **合计** | **{total/1000:,.2f}** | **{total_per_mw:,.2f}** | **100.00%** |')
    cap_lines = ['| 市场/方向 | 平均功率（MW） | 口径 |', '|---|---:|---|']
    for market in MARKETS:
        if market in ('DA', 'ID'):
            definition = '按全部正式QH求有符号均值；售电为正、购电为负，空闲桥接按0计'
        elif market in ('cap_up', 'cap_down'):
            definition = '第一阶段全额成交假设下的方向容量QH平均'
        else:
            definition = 'QH平均激活功率（MWh按时长折算）'
        label = {'DA': 'DA电能执行功率', 'ID': 'ID电能执行功率'}.get(market, LABELS_ZH[market])
        cap_lines.append(f'| {label} | {capacity_avg[market]:,.2f} | {definition} |')
    cap_lines.insert(4, f'| DA+ID合并现货执行功率 | {capacity_avg["spot_net_da_id"]:,.2f} | 逐QH合并DA和ID有符号净功率后求全期平均 |')

    start_local = start.astimezone(MADRID).strftime('%Y/%m/%d')
    end_local = (end.astimezone(MADRID).date()).strftime('%Y/%m/%d')
    input_end = manifest.get('input_end', '未记录')
    raw_coverage = (raw_complete / quality['formal_qh'] * 100
                    if raw_complete is not None and quality.get('formal_qh') else None)
    settled_coverage = data['valid_qh'] / data['total_qh'] * 100 if data['total_qh'] else 0.0
    avg_month_eur = total / max(len(months), 1)
    avg_month_per_mw = total_per_mw / max(len(months), 1)
    overview_income = ['| 期间 | 收益（kEUR） | 收益（kEUR/MW） |', '|---|---:|---:|',
                       f'| 全期合计 | {total/1000:,.2f} | {total_per_mw:,.2f} |',
                       f'| 月均（{len(months)}个月） | {avg_month_eur/1000:,.2f} | {avg_month_per_mw:,.2f} |']
    overview_cycles = ['| 期间 | 等效循环次数（EFC） |', '|---|---:|',
                       f'| 全期合计 | {data["total_efc"]:,.2f} |',
                       f'| 月均（{len(months)}个月） | {data["total_efc"]/max(len(months),1):,.2f} |']
    for year, item in sorted(annual.items()):
        year_total = sum(item['cash_eur'].values())
        period_label = f'{year}年（完整天 {item["complete_days"]}/{item["total_days"]}）'
        overview_income.append(f'| {period_label} | {year_total/1000:,.2f} | {year_total/(1000*data["discharge_mw"]):,.2f} |')
        overview_cycles.append(f'| {period_label} | {item["efc"]:,.2f} |')
    latest_rolling = rolling_12m[-1] if rolling_12m else None
    annualized_income = ['| 滚动窗口 | 年化收益（kEUR） | 年化收益（kEUR/MW） |', '|---|---:|---:|']
    if latest_rolling:
        latest_window = f'{latest_rolling["window_start"].replace("-", "/")}–{latest_rolling["window_end"].replace("-", "/")}'
        annualized_income.append(f'| 最近完整12个月（{latest_window}） | {latest_rolling["kEUR"]:,.2f} | {latest_rolling["kEUR_per_MW"]:,.2f} |')
    else:
        annualized_income.append('| 数据不足12个连续月份 | — | — |')
    if v1_rolling_12m:
        latest_v1 = {r['month']: r for r in v1_rolling_12m}.get(latest_rolling['month']) if latest_rolling else None
        if latest_v1:
            annualized_income.append(f'| V1 100%中标（同窗口） | {latest_v1["kEUR_per_MW"]*data["discharge_mw"]:,.2f} | {latest_v1["kEUR_per_MW"]:,.2f} |')
    report = [
        '# 西班牙储能 MILP 结果展示', '',
        f'输入结果目录：`{run_dir.as_posix()}`。情景：`{manifest.get("scenario", mode)}`；中标系数模式：`{mode}`。',
        f'正式统计期：马德里当地 **{start_local} 至 {(end.astimezone(MADRID).date()).fromordinal((end.astimezone(MADRID).date()).toordinal()-1).strftime("%Y/%m/%d")}**（结束日期按排除端处理）。本次计算成功：`{summary.get("success")}`。', '',
        '## 假设概览', '',
        '| 项目 | 本次配置 |', '|---|---|',
        f'| 数据时间范围 | 正式结算日 {start_local}–{(end.astimezone(MADRID).date()).fromordinal((end.astimezone(MADRID).date()).toordinal()-1).strftime("%Y/%m/%d")}；求解输入加载到 `{input_end}`（含观察数据） |',
        f'| 时间分辨率与时区 | 15 分钟 QH；本地展示按 Europe/Madrid |',
        f'| 输入来源标识 | eSIOS 指标 {", ".join(source_ids) if source_ids else "未记录"}；aFRR 系数文件 `{Path(award.get("path", "未记录")).name}` |',
        f'| 系数文件 SHA-256 | `{award.get("sha256", "未记录")}` |',
        f'| 原始字段完整度 | {raw_complete:,} / {quality.get("formal_qh", data["total_qh"]):,} QH ({raw_coverage:.2f}%) |' if raw_coverage is not None else '| 原始字段完整度 | 无法读取 |',
        f'| 已结算覆盖率 | {data["valid_qh"]:,} / {data["total_qh"]:,} QH ({settled_coverage:.2f}%)；假设空缺时段空闲桥接 {quality.get("assumed_idle_hours", 0):,.1f} 小时；未知状态阻断 QH {quality.get("blocked_qh", 0)} |',
        '| 完整天统计口径 | 当地自然日内所有预期 QH 均有有效结算记录；夏令时切换日按实际 92 或 100 个 QH 计算 |',
        f'| 电池配置 | 充电/放电功率 {config["charge_mw"]:g}/{config["discharge_mw"]:g} MW；能量边界 {config["e_min_mwh"]:g}–{config["e_max_mwh"]:g} MWh；初始/终端能量 {config["e_initial_mwh"]:g}/{config["e_terminal_mwh"]:g} MWh |',
        f'| 效率与备用上限 | 充/放电效率 {config["eta_charge"]:.1%}/{config["eta_discharge"]:.1%}；aFRR 上/下备用功率上限 {config["reserve_limit_up_mw"]:g}/{config["reserve_limit_down_mw"]:g} MW |',
        f'| 年度 EFC 预算 | ' + '；'.join(f'{year}: {float(v["value"]):,.3f}' for year, v in manifest.get('budgets', {}).items()) + ' EFC |',
        f'| 循环口径 | EFC 分母 = 2 × 可用能量 = {efc_denominator:,.1f} MWh；循环数采用模型记录的等效全循环（EFC） |',
        '', '重要建模假设：', '',
        '- 完美历史价格信息是事后理论上限，不是可执行的实时策略收益。',
        '- 中标系数仅折减 aFRR 容量收入优化目标；本结果列示的上下调容量仍是第一阶段全额成交假设下的计划申报量，不是按中标率折算后的预期中标 MW。激活收益与物理容量承诺沿用原 V1 口径。系统分配量/报价量是敏感性代理，不是该电站的真实中标率。',
        '- GCT 后备用余量按第一阶段全额成交建模假设处理；缺失输入按配置允许的空闲桥接处理。',
        '', '## 结果概览', '',
        '### 收益：全期、月均与自然年', '', *overview_income, '',
        '### 年化收益：截至最新月份的滚动12个月', '', *annualized_income, '',
        '### 逐月滚动12个月收益（kEUR/MW）', '',
        '每个统计月份以当月为窗口终点，累计当月及此前连续11个月；仅列出具备连续12个月数据的窗口。V1 按同一 12 个月窗口计算，容量收入系数为 100%。V1 使用自身重新优化的调度结果，因此两条线的差额同时包含容量收益计价方式和调度变化。', '',
        '![逐月滚动12个月收益，kEUR/MW](rolling_12m_revenue_kEUR_per_MW.svg)', '',
        _rolling_12m_table(rolling_12m, v1_rolling_12m), '',
        '### 循环次数：全期、月均与自然年', '',
        'EFC（等效全循环）按各 QH 的 SOC 变化绝对值累计，再除以 2 × 可用能量；它可为小数，表示累计吞吐量折合了多少次满可用能量往返。完整充放电循环则是一次实际的充电—放电过程，按事件计数；部分循环、跨期循环及不同深度循环使两者不必相等。', '', *overview_cycles, '',
        '### 市场收益和净收益占比', '', *income_lines, '',
        '占比以净总收益为分母，因此负收益市场显示负占比，正收益市场占比之和可能超过 100%。', '',
        '### 各市场平均执行功率和申报容量', '', *cap_lines, '',
        'DA、ID 和合并现货行均按全期正式 QH 求带方向的净功率均值，不取绝对值；售电为正、购电为负，相反方向时段会抵消。没有有效市场数据并按假设空闲桥接的 QH 按 0 MW 计入平均。若要衡量市场内交易强度，可另看平均绝对净功率，本表不采用该口径。aFRR 上下调列是按全期 QH 统计的第一阶段全额成交假设下申报容量均值，空闲桥接 QH 以 0 计；供需系数折减容量收益，不折减申报 MW。上、下方向分开列示，不能相加理解为同一方向功率；激活列是平均实际激活功率。', '',
        '## 月度结果概览', '',
        '### 月度收入（kEUR）', '',
        '![月度各市场收入，kEUR](monthly_revenue_kEUR.svg)', '',
        '### 月度单位功率收入（kEUR/MW）', '',
        '![月度各市场收入，kEUR/MW](monthly_revenue_kEUR_per_MW.svg)', '',
        '### 月度收益明细与自然年合计', '',
        _money_table(months, data['discharge_mw'], years, per_mw=False), '',
        _money_table(months, data['discharge_mw'], years, per_mw=True), '',
        '## 小时级结果概览', '',
        '下图按马德里本地钟点，将每个完整且有效的实际小时内四个 QH 市场现金流先求和，再按可用小时求平均；数值按 0.001 kEUR/MW 作整数刻度，轴标题标明缩放系数，重复夏令时小时按实际 UTC 偏移分别计入。', '',
        '![全周期0–23时平均小时收益](hourly_average_kEUR_per_MW.svg)', '',
        f'完整有效小时：{len(data["complete_hours"]):,}。小时均值分母按小时 0–23 分别计算；每小时样本数见 `hourly.csv`。', '',
        '### 月度 × 小时平均收益热力图', '',
        '每格为该月该小时的完整有效小时平均总收益，单位 kEUR/MW；收益先按四个 QH 合计，再在当月同一钟点的样本小时间取平均。颜色以零为中心，红色表示负收益、蓝色表示正收益；格内显示数值。', '',
        '![各月各小时平均收益热力图，kEUR/MW](monthly_hourly_heatmap_kEUR_per_MW.svg)', '',
        '### 按季度分组的小时收益', '',
        '每张图按跨年度相同季度汇总（例如 Q1 合并所有年份的一月至三月）；整数轴刻度为 0.001 kEUR/MW。', '',
    ]
    for quarter, filename in quarter_files:
        report.extend([f'#### {quarter}', '', f'![{quarter} 0–23时平均收益]({filename})', ''])
    report.extend([
        '## 输出文件与口径', '',
        '- `monthly.csv`：逐月六市场收益、总收益、每 MW 收益、结算覆盖率和 EFC；自然年合计另列于 `annual.csv`。',
        '- `hourly.csv`、`quarterly_hourly.csv`：小时均值、样本小时数与六市场拆分。',
        '- `monthly_hourly_heatmap.csv`：热力图每月每小时平均总收益和样本小时数。',
        '- `rolling_12m.csv`：每月为窗口终点的连续12个月总收益。',
        '- 图表均为 SVG，可放大查看；本脚本使用 Python 标准库生成，不依赖绘图库。',
        '- 输入结果目录、来源清单、系数文件哈希以及本报告的小时完整性过滤口径均保留，便于审计和复算。',
    ])
    (output_dir / 'monthly.csv').write_text(_monthly_csv(months, data['discharge_mw'], years), encoding='utf-8-sig')
    (output_dir / 'annual.csv').write_text(_annual_csv(annual, data['discharge_mw']), encoding='utf-8-sig')
    (output_dir / 'hourly.csv').write_text(_hourly_csv(data['hours']), encoding='utf-8-sig')
    (output_dir / 'quarterly_hourly.csv').write_text(_quarterly_csv(data['quarters']), encoding='utf-8-sig')
    (output_dir / 'monthly_hourly_heatmap.csv').write_text(_monthly_hourly_csv(data['monthly_hours']), encoding='utf-8-sig')
    (output_dir / 'rolling_12m.csv').write_text(_rolling_12m_csv(rolling_12m, v1_rolling_12m), encoding='utf-8-sig')
    report_path = output_dir / '结果展示.md'
    report_path.write_text('\n'.join(report) + '\n', encoding='utf-8')
    return report_path


def _monthly_csv(months: dict, discharge_mw: float, years: list[int]) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['month', *[f'{m}_kEUR' for m in MARKETS], 'total_kEUR',
                     *[f'{m}_kEUR_per_MW' for m in MARKETS], 'total_kEUR_per_MW',
                     'valid_qh', 'total_qh', 'settlement_coverage', 'efc'])
    for month, item in sorted(months.items()):
        values = item['cash_eur']
        total = sum(values.values())
        writer.writerow([month, *[f'{values[m] / 1000:.2f}' for m in MARKETS], f'{total / 1000:.2f}',
                         *[f'{values[m] / (1000 * discharge_mw):.2f}' for m in MARKETS],
                         f'{total / (1000 * discharge_mw):.2f}', item['valid_qh'], item['total_qh'],
                         item['valid_qh'] / item['total_qh'] if item['total_qh'] else 0,
                         item['efc']])
    return stream.getvalue().replace('\r\n', '\n')


def _annual_csv(annual: dict, discharge_mw: float) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['year', *[f'{m}_kEUR' for m in MARKETS], 'total_kEUR',
                     *[f'{m}_kEUR_per_MW' for m in MARKETS], 'total_kEUR_per_MW',
                     'valid_qh', 'total_qh', 'settlement_coverage', 'complete_days', 'total_days', 'efc'])
    for year, item in sorted(annual.items()):
        values = item['cash_eur']
        total = sum(values.values())
        writer.writerow([year, *[f'{values[m] / 1000:.2f}' for m in MARKETS], f'{total / 1000:.2f}',
                         *[f'{values[m] / (1000 * discharge_mw):.2f}' for m in MARKETS],
                         f'{total / (1000 * discharge_mw):.2f}', item['valid_qh'], item['total_qh'],
                         item['valid_qh'] / item['total_qh'] if item['total_qh'] else 0,
                         item['complete_days'], item['total_days'],
                         item['efc']])
    return stream.getvalue().replace('\r\n', '\n')


def _hourly_csv(rows: list[dict]) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['hour', *[f'{m}_kEUR_per_MW' for m in MARKETS],
                     'total_kEUR_per_MW', 'sample_hours'])
    for row in rows:
        vals = row['components']
        writer.writerow([row['hour'], *[f'{vals[m]:.2f}' for m in MARKETS],
                         f'{sum(vals.values()):.2f}', row['count']])
    return stream.getvalue().replace('\r\n', '\n')


def _quarterly_csv(quarters: dict) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['quarter', 'hour', *[f'{m}_kEUR_per_MW' for m in MARKETS],
                     'total_kEUR_per_MW', 'sample_hours'])
    for quarter, rows in quarters.items():
        for row in rows:
            vals = row['components']
            writer.writerow([quarter, row['hour'], *[f'{vals[m]:.2f}' for m in MARKETS],
                             f'{sum(vals.values()):.2f}', row['count']])
    return stream.getvalue().replace('\r\n', '\n')


def _monthly_hourly_csv(monthly_hours: dict[str, list[dict]]) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    writer.writerow(['month', 'hour', 'average_total_kEUR_per_MW', 'sample_hours'])
    for month, rows in sorted(monthly_hours.items()):
        for row in rows:
            value = f'{row["total_kEUR_per_MW"]:.2f}' if row['count'] else ''
            writer.writerow([month, row['hour'], value, row['count']])
    return stream.getvalue().replace('\r\n', '\n')


def _rolling_12m_csv(rows: list[dict], v1_rows: list[dict] | None = None) -> str:
    import csv
    from io import StringIO
    stream = StringIO()
    writer = csv.writer(stream)
    v1_by_month = {r['month']: r for r in (v1_rows or [])}
    writer.writerow(['month', 'window_start_month', 'window_end_month',
                     'rolling_total_kEUR', 'rolling_total_kEUR_per_MW',
                     'v1_100pct_kEUR_per_MW', 'v1_minus_coefficient_kEUR_per_MW'])
    for row in rows:
        v1_value = v1_by_month.get(row['month'], {}).get('kEUR_per_MW')
        writer.writerow([row['month'], row['window_start'], row['window_end'],
                         f'{row["kEUR"]:.2f}', f'{row["kEUR_per_MW"]:.2f}',
                         f'{v1_value:.2f}' if v1_value is not None else '',
                         f'{v1_value-row["kEUR_per_MW"]:.2f}' if v1_value is not None else ''])
    return stream.getvalue().replace('\r\n', '\n')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-dir', type=Path, required=True, help='completed MILP output directory')
    parser.add_argument('--output-dir', type=Path, required=True, help='new presentation output directory')
    parser.add_argument('--v1-monthly-csv', type=Path, help='optional V1 100%%-award monthly.csv for rolling comparison')
    args = parser.parse_args()
    print(build(args.run_dir, args.output_dir, args.v1_monthly_csv))


if __name__ == '__main__':
    main()
