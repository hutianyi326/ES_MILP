"""Build ex-post QH aFRR allocation/offer ratios from REE monthly ZIPs.

Input archives are read-only. One unmodified archive 234 ZIP per delivery month
is expected in --offer-dir; absent months become null rows with quality flags.
"""
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import re
import zipfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[2]
MADRID = ZoneInfo('Europe/Madrid')
UTC = timezone.utc
QH = timedelta(minutes=15)
ARCHIVE = re.compile(r'^234-Curvas_Ofertas_aFRR-(\d{4})-(\d{2})-01T.*_datos\.zip$')
MEMBER = re.compile(r'^Curvas_Ofertas_aFRR_(\d{8})\.xls$')
DIRECTIONS = {'Subir': 'up', 'Bajar': 'down'}
INDICATORS = {'up': 632, 'down': 633}
FIELDS = ('qh_start_utc', 'local_date', 'local_qh_number', 'direction',
          'offer_mw', 'allocated_mw', 'raw_ratio', 'award_rate_proxy',
          'quality_status', 'offer_rows', 'offer_zip', 'offer_member', 'allocated_source')


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def iso_utc(value):
    return value.astimezone(UTC).isoformat().replace('+00:00', 'Z')


def day_grid(day):
    start = datetime(day.year, day.month, day.day, tzinfo=MADRID).astimezone(UTC)
    next_day = day + timedelta(days=1)
    end = datetime(next_day.year, next_day.month, next_day.day, tzinfo=MADRID).astimezone(UTC)
    return [start + i * QH for i in range(int((end - start) / QH))]


def _month_iter(start, end):
    current = date(start.year, start.month, 1)
    while current < end:
        yield current.strftime('%Y-%m')
        current = date(current.year + (current.month == 12), current.month % 12 + 1, 1)


def _archive_index(folder, selected_zips=()):
    found = {}
    for path in sorted(folder.glob('*.zip')):
        match = ARCHIVE.match(path.name)
        if not match:
            continue
        month = f'{match[1]}-{match[2]}'
        if month in found:
            raise ValueError(f'multiple ZIP versions for {month}; select one explicitly: {found[month]}, {path}')
        found[month] = path
    for path in selected_zips:
        match = ARCHIVE.match(path.name)
        if not match or not path.is_file():
            raise ValueError(f'--offer-zip must name an existing, original archive 234 ZIP: {path}')
        found[f'{match[1]}-{match[2]}'] = path
    return found


def offer_rows_for_month(path, month):
    import xlrd
    offers = {}
    daily = []
    with zipfile.ZipFile(path) as archive:
        members = {}
        duplicate_days = set()
        for member in archive.namelist():
            match = MEMBER.match(member)
            if not match:
                continue
            day = datetime.strptime(match[1], '%Y%m%d').date()
            if day.strftime('%Y-%m') != month:
                daily.append(dict(day=str(day), member=member, status='out_of_month_member'))
                continue
            if day in members or day in duplicate_days:
                daily.append(dict(day=str(day), member=member, status='duplicate_day_member'))
                duplicate_days.add(day)
                members.pop(day)
                continue
            members[day] = member
        month_start = date.fromisoformat(month + '-01')
        next_month = date(month_start.year + (month_start.month == 12), month_start.month % 12 + 1, 1)
        current = month_start
        while current < next_month:
            if current not in members:
                daily.append(dict(day=str(current), member='', status='missing_day_member'))
            current += timedelta(days=1)
        for day, member in sorted(members.items()):
            try:
                book = xlrd.open_workbook(file_contents=archive.read(member), on_demand=True,
                                          logfile=io.StringIO())
            except (OSError, ValueError, xlrd.XLRDError, RuntimeError):
                daily.append(dict(day=str(day), member=member, status='unreadable_workbook'))
                continue
            sheet = book.sheet_by_index(0)
            grid = day_grid(day)
            if sheet.ncols < 5 or sheet.nrows < 2:
                daily.append(dict(day=str(day), member=member, status='invalid_workbook'))
                continue
            header = sheet.row_values(1)[:5]
            if header[0] != 'Cuarto de Hora del dia' or header[1] != 'Sentido' or header[4] != 'Potencia ofertada (MW)':
                daily.append(dict(day=str(day), member=member, status='unexpected_columns'))
                continue
            try:
                sheet_day = xlrd.xldate_as_datetime(sheet.cell_value(0, 4), book.datemode).date()
            except (TypeError, ValueError, xlrd.XLRDError):
                daily.append(dict(day=str(day), member=member, status='invalid_date_cell'))
                continue
            if sheet_day != day:
                daily.append(dict(day=str(day), member=member, status='date_mismatch'))
                continue
            sums = defaultdict(float)
            counts = Counter()
            invalid = set()
            for i in range(2, sheet.nrows):
                qh, label, price, _, power = sheet.row_values(i)[:5]
                if label not in DIRECTIONS or not isinstance(qh, (int, float)) or not float(qh).is_integer():
                    invalid.add('invalid_direction_or_qh')
                    continue
                number = int(qh)
                if not 1 <= number <= len(grid):
                    invalid.add('qh_out_of_range')
                    continue
                direction = DIRECTIONS[label]
                key = (iso_utc(grid[number - 1]), direction)
                if (not isinstance(power, (int, float)) or not math.isfinite(power) or power < 0
                        or not isinstance(price, (int, float)) or not math.isfinite(price)):
                    invalid.add('invalid_offer_row')
                    continue
                sums[key] += float(power)
                counts[key] += 1
            # An invalid bid row has no reliable QH attribution: quarantine the day.
            if invalid:
                daily.append(dict(day=str(day), member=member, status='|'.join(sorted(invalid))))
                continue
            for key, total in sums.items():
                offers[key] = (total, counts[key], path.name, member)
            daily.append(dict(day=str(day), member=member, status='ok',
                              expected_qh_per_direction=len(grid),
                              up_qh=sum(k[1] == 'up' for k in sums),
                              down_qh=sum(k[1] == 'down' for k in sums)))
    return offers, daily


def allocated_for_month(raw_dir, month, indicator):
    choices = []
    for path in raw_dir.glob(f'{month}/*/fetch_{indicator}.json'):
        meta_path = path.with_suffix(path.suffix + '.meta.json')
        try:
            meta = json.loads(meta_path.read_text(encoding='utf-8'))
            digest = sha256(path)
            if meta.get('http_status') != 200 or meta.get('sha256') != digest:
                continue
            if meta.get('request_params', {}).get('time_trunc') != 'fifteen_minutes':
                continue
            payload = json.loads(path.read_text(encoding='utf-8'))['indicator']
            if int(payload['id']) != indicator:
                continue
            values = defaultdict(set)
            for row in payload.get('values', []):
                if row.get('geo_id') != 8741 or row.get('geo_name') != 'Península':
                    continue
                moment = datetime.fromisoformat(row['datetime_utc'].replace('Z', '+00:00')).astimezone(UTC)
                if moment.astimezone(MADRID).strftime('%Y-%m') == month:
                    values[iso_utc(moment)].add(float(row['value']))
            if any(len(v) != 1 for v in values.values()):
                continue
            choices.append((len(values), str(path), {k: next(iter(v)) for k, v in values.items()}, digest))
        except (OSError, ValueError, KeyError, TypeError, OverflowError):
            continue
    if not choices:
        return {}, None
    choices.sort(key=lambda row: (row[0], row[1]), reverse=True)
    _, path, values, digest = choices[0]
    return values, dict(path=str(Path(path).relative_to(ROOT)), sha256=digest, valid_qh=len(values))


def ratio(offer, allocated):
    if offer is None:
        return None, None, 'missing_offer'
    if allocated is None:
        return None, None, 'missing_allocated'
    if not all(math.isfinite(v) and v >= 0 for v in (offer, allocated)):
        return None, None, 'invalid_quantity'
    if offer == 0:
        return None, None, 'zero_market' if allocated == 0 else 'allocated_without_offer'
    raw = allocated / offer
    if allocated > offer + 1e-6:
        return raw, None, 'allocated_exceeds_offer'
    return raw, min(1.0, raw), 'valid' if allocated else 'zero_allocated'


def build(start, end, offer_dir, raw_dir, output, selected_zips=()):
    if start >= end or start.day != 1 or end.day != 1:
        raise ValueError('use first-of-month start and exclusive end dates')
    archives = _archive_index(offer_dir, selected_zips)
    months = list(_month_iter(start, end))
    offers = {}
    allocated = {}
    sources = []
    daily = []
    for month in months:
        archive = archives.get(month)
        if archive is not None:
            try:
                current, days = offer_rows_for_month(archive, month)
            except (zipfile.BadZipFile, OSError):
                current, days = {}, [dict(day=month, member='', status='unreadable_zip')]
            offers.update(current)
            daily.extend(days)
            sources.append(dict(month=month, kind='offer_curve', path=str(archive), sha256=sha256(archive),
                                daily_files=sum(bool(day['member']) and day['status']=='ok' for day in days)))
        else:
            daily.append(dict(day=month, member='', status='missing_month_archive'))
        for direction, indicator in INDICATORS.items():
            values, source = allocated_for_month(raw_dir, month, indicator)
            allocated.update({(qh, direction): value for qh, value in values.items()})
            if source:
                sources.append(dict(month=month, kind='allocated_reserve', direction=direction, **source))
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        raise FileExistsError(output)
    counts = Counter()
    with output.open('wb') as binary, gzip.GzipFile(fileobj=binary, mode='wb', filename='', mtime=0) as packed, io.TextIOWrapper(packed, encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        day = start
        while day < end:
            for number, moment in enumerate(day_grid(day), 1):
                qh = iso_utc(moment)
                for direction in INDICATORS:
                    key = (qh, direction)
                    offer = offers.get(key)
                    award = allocated.get(key)
                    raw, rate, status = ratio(offer[0] if offer else None, award)
                    counts[status] += 1
                    writer.writerow(dict(qh_start_utc=qh, local_date=str(day), local_qh_number=number,
                        direction=direction, offer_mw=offer[0] if offer else '',
                        allocated_mw=award if award is not None else '',
                        raw_ratio=raw if raw is not None else '',
                        award_rate_proxy=rate if rate is not None else '', quality_status=status,
                        offer_rows=offer[1] if offer else '', offer_zip=offer[2] if offer else '',
                        offer_member=offer[3] if offer else '', allocated_source=INDICATORS[direction]))
            day += timedelta(days=1)
    manifest = dict(start=str(start), end_exclusive=str(end), offer_dir=str(offer_dir), raw_dir=str(raw_dir),
                    output=str(output), output_sha256=sha256(output), counts=dict(counts), sources=sources,
                    daily_checks=daily, region_assumption='offer_curve_peninsular_scope_pending_independent_confirmation',
                    meaning='ex_post_system_allocation_to_total_offer_proxy_not_site_probability')
    manifest_path = output.with_suffix(output.suffix + '.manifest.json')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start', type=date.fromisoformat, required=True)
    parser.add_argument('--end', type=date.fromisoformat, required=True, help='exclusive first day of month')
    parser.add_argument('--offer-dir', type=Path, default=Path(r'C:\Users\Tianyi\Desktop\西班牙数据\容量报价曲线'))
    parser.add_argument('--offer-zip', type=Path, action='append', default=[],
                        help='explicit replacement ZIP for its month; repeatable')
    parser.add_argument('--raw-dir', type=Path, default=ROOT / 'input/raw/ES/esios')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.start, args.end, args.offer_dir, args.raw_dir, args.output, args.offer_zip)
    print(json.dumps(dict(output=result['output'], output_sha256=result['output_sha256'],
                          counts=result['counts']), ensure_ascii=False))


if __name__ == '__main__':
    main()
