"""Archive ENTSO-E prices without logging credentials; preserve native intervals."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen
from xml.etree import ElementTree as ET
from zipfile import ZipFile, is_zipfile
from zoneinfo import ZoneInfo

ENDPOINT = 'https://web-api.tp.entsoe.eu/api'
ES = '10YES-REE------0'


def name(node):
    return node.tag.rsplit('}', 1)[-1]


def metadata(node, exclude=()):
    result = {}
    def walk(n, prefix=''):
        for child in n:
            if name(child) in exclude:
                continue
            key = prefix + name(child)
            if len(child):
                walk(child, key + '/')
            else:
                result[key] = (child.text or '').strip()
    walk(node)
    return result


def unpack(body):
    if is_zipfile(BytesIO(body)):
        with ZipFile(BytesIO(body)) as archive:
            for member in archive.namelist():
                if not member.endswith('/'):
                    yield from unpack(archive.read(member))
    else:
        yield body


def parse(body):
    docs, rows = [], []
    for content in unpack(body):
        root = ET.fromstring(content)
        doc = metadata(root, ('TimeSeries', 'Bid_TimeSeries', 'BidTimeSeries'))
        docs.append(doc)
        for series in root:
            if name(series) not in ('TimeSeries', 'Bid_TimeSeries', 'BidTimeSeries'):
                continue
            fields = metadata(series, ('Period',))
            for period in series:
                if name(period) != 'Period':
                    continue
                head = metadata(period, ('Point',))
                start = datetime.fromisoformat(head['timeInterval/start'].replace('Z', '+00:00'))
                end = datetime.fromisoformat(head['timeInterval/end'].replace('Z', '+00:00'))
                resolution = head['resolution']
                match = re.fullmatch(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', resolution)
                if not match:
                    raise ValueError('unsupported resolution: ' + resolution)
                step = timedelta(seconds=sum(int(v or 0)*w for v, w in zip(match.groups(), (3600, 60, 1))))
                if step.total_seconds() <= 0:
                    raise ValueError('nonpositive resolution')
                points = sorted((metadata(p) for p in period if name(p) == 'Point'), key=lambda p: int(p['position']))
                for i, point in enumerate(points):
                    a = start + (int(point['position'])-1)*step
                    b = min(a+step, end)
                    if fields.get('curveType') == 'A03':
                        b = start+(int(points[i+1]['position'])-1)*step if i+1 < len(points) else end
                    rows.append(dict(start=a.isoformat(), end=b.isoformat(), resolution=resolution,
                                     series=fields, point=point))
    return docs, rows


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--date', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--credential-file', type=Path)
    args = parser.parse_args()
    token = os.environ.get('ENTSOE_SECURITY_TOKEN', '')
    if not token and args.credential_file:
        for line in args.credential_file.read_text(encoding='utf-8-sig').splitlines():
            if line.strip().startswith('ENTSOE_SECURITY_TOKEN='):
                token = line.split('=', 1)[1].strip().strip('\"\'')
    if not token:
        raise RuntimeError('ENTSOE_SECURITY_TOKEN unavailable')
    args.output.mkdir(parents=True, exist_ok=False)
    start = datetime.fromisoformat(args.date).replace(tzinfo=ZoneInfo('Europe/Madrid'))
    end = start+timedelta(days=1)
    base = dict(periodStart=start.astimezone(timezone.utc).strftime('%Y%m%d%H%M'),
                periodEnd=end.astimezone(timezone.utc).strftime('%Y%m%d%H%M'))
    tasks = [('DA', dict(documentType='A44', in_Domain=ES, out_Domain=ES)),
             ('capacity_A01', dict(documentType='A81', businessType='B95', processType='A51',
                                   controlArea_Domain=ES, **{'Type_MarketAgreement.Type': 'A01'})),
             ('activation_A16', dict(documentType='A84', processType='A16', businessType='A96', controlArea_Domain=ES)),
             ('activation_A67', dict(documentType='A84', processType='A67', businessType='A96',
                                     controlArea_Domain=ES, Standard_MarketProduct='A01'))]
    def fetch(task):
        label, query = task
        params = {**base, **query}
        record = dict(label=label, endpoint=ENDPOINT, params=params, retrieved_at=datetime.now(timezone.utc).isoformat(), attempts=[])
        for attempt in range(3):
            try:
                try:
                    with urlopen(ENDPOINT+'?'+urlencode({**params, 'securityToken': token}), timeout=45) as response:
                        body, status = response.read(), response.status
                except HTTPError as error:
                    body, status = error.read(), error.code
                # A server response should never echo a credential into archived output.
                body = body.replace(token.encode(), b'[REDACTED]')
                suffix = '.zip' if is_zipfile(BytesIO(body)) else '.xml'
                raw = label+f'_attempt{attempt+1}'+suffix
                (args.output/raw).write_bytes(body)
                evidence = dict(status=status, file=raw, sha256=hashlib.sha256(body).hexdigest())
                record['attempts'].append(evidence)
                if status == 200:
                    record['documents'], record['rows'] = parse(body)
                    break
                if status not in (404, 429, 500, 502, 503, 504):
                    break
            except Exception as error:
                record['attempts'].append(dict(error_class=type(error).__name__))
        (args.output/(label+'.json')).write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')
        summary = dict(label=label, attempts=record['attempts'], rows=len(record.get('rows', [])),
                       resolutions=sorted({r['resolution'] for r in record.get('rows', [])}),
                       documents=record.get('documents', []),
                       series=list({json.dumps(r['series'], sort_keys=True) for r in record.get('rows', [])}))
        print(json.dumps(summary, ensure_ascii=False), flush=True)
        return {k: v for k, v in summary.items() if k != 'series'}
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, tasks))
    (args.output/'fetch_summary.json').write_text(json.dumps(dict(date=args.date, timezone='Europe/Madrid', results=results),
                                                           ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
