"""Write the data dictionary and human-readable consolidation acceptance report."""
import json
from pathlib import Path

if __package__:
    from .consolidate_simple_market_data import BASE, ROOT, load, dump
else:
    from consolidate_simple_market_data import BASE, ROOT, load, dump


def main():
    s=load(BASE/'summary.json');v=load(BASE/'validation.json');inv=load(BASE/'inventory.json')
    assert not s['fetch_errors'] and v['da_and_capacity_complete']
    assert v['rows_4s']==s['rows_4s'] and v['rows_15min']==s['rows_15min']
    dictionary={
      'start_utc':dict(unit='ISO8601 UTC',meaning='inclusive interval start; four-second file interval ends 4 seconds later'),
      'start_europe_madrid':dict(unit='ISO8601 with offset',meaning='Madrid local timestamp including DST offset'),
      'da_eur_mwh':dict(unit='EUR/MWh',meaning='DA price; hourly source repeated within its original delivery hour, QH source within original quarter-hour'),
      'capacity_up_eur_mw_qh':dict(unit='EUR/MW/15min',meaning='Up marginal capacity price; not EUR/MW/hour'),
      'capacity_down_eur_mw_qh':dict(unit='EUR/MW/15min',meaning='Dn marginal capacity price; no sign reversal'),
      'da_native_resolution':dict(values=['PT60M','PT15M'],meaning='original source DA delivery resolution, not the output sampling step'),
      'activation_up_eur_mwh':dict(unit='EUR/MWh',meaning='native 4-second central-selection aFRR CBMP Up; no sign reversal'),
      'activation_down_eur_mwh':dict(unit='EUR/MWh',meaning='native 4-second central-selection aFRR CBMP Dn; no sign reversal'),
      'up_price_status':dict(values=['valid','source_explicit_null','source_unreported','api_no_matching_data']),
      'down_price_status':dict(values=['valid','source_explicit_null','source_unreported','api_no_matching_data']),
      'activation_source_id':dict(meaning='key in sources.json, leading to immutable raw snapshot and uncompressed SHA256'),
      'activation_up_mean_eur_mwh':dict(unit='EUR/MWh',meaning='research-only 15min mean of valid 4s prices, not energy-weighted or official settlement price'),
      'activation_down_mean_eur_mwh':dict(unit='EUR/MWh',meaning='research-only 15min mean of valid 4s prices, not energy-weighted or official settlement price'),
      'activation_up_valid_seconds':dict(unit='seconds',meaning='nonempty 4s price duration within the quarter-hour'),
      'activation_down_valid_seconds':dict(unit='seconds',meaning='nonempty 4s price duration within the quarter-hour'),
      'activation_up_reported_seconds':dict(unit='seconds',meaning='reported duration including explicit null price blocks'),
      'activation_down_reported_seconds':dict(unit='seconds',meaning='reported duration including explicit null price blocks'),
      'da_source_id':dict(meaning='key in sources.json for the original DA source document'),
      'capacity_up_source_id':dict(meaning='key in sources.json for original Up capacity source document'),
      'capacity_down_source_id':dict(meaning='key in sources.json for original Dn capacity source document'),
    }
    dump(BASE/'data_dictionary.json',dictionary)
    lines=['# 西班牙市场价格数据整理与补抓','',
      '范围：2025-06-01至2026-10-31，Europe/Madrid当地自然日；右端不含2026-11-01。整理及重新查询日期：2026-11-03。',
      '', '## 完成情况','',
      f"共{s['days']}天、{s['rows_15min']:,}个15分钟时段、{s['rows_4s']:,}个4秒时段，按17个月分文件。",'',
      '| 价格字段 | 应有记录 | 有效价格记录 | 有效率 |','|---|---:|---:|---:|']
    labels={'da':'DA价格（15分钟时间轴）','capacity_up':'Up容量价格（15分钟）','capacity_down':'Dn容量价格（15分钟）','activation_up':'Up激活价格（4秒）','activation_down':'Dn激活价格（4秒）'}
    for field,label in labels.items():
        t=s['totals'][field];lines.append(f"| {label} | {t['expected']:,} | {t['valid']:,} | {t['coverage_pct']:.4f}% |")
    lines += ['',
      f"DA与双向容量各补齐{inv['missing']['da']['missing_qh']:,}个本地缺失时段，范围为2026年9—10月。既有原始归档均保留，新集合单独存储。",'',
      f"本轮完成{s['fetch_status'].get('ok',0)+s['fetch_status'].get('no_data',0)}项重新查询任务，最终错误0项；其中{s['fetch_status'].get('no_data',0)}项为官方无匹配数据响应，不将其归类为网络错误。所有518个当地日的4秒价格均重新查询以检查修订。",'',
      f"4秒数据仍有真实空值，未填零、未插值、未以前后价格延续，也未用15分钟激活价冒充4秒价格。本轮首个有效CBMP（UTC）：Up {v['first_valid_utc'].get('up')}；Dn {v['first_valid_utc'].get('down')}。空价块不能仅凭此字段解释为未激活。",
      '', '## 数据文件','',
      '- `processed/prices_4s/YYYY-MM.csv.gz`：主数据，共17个按月压缩CSV。每行一个4秒时段，已对齐DA、Up/Dn容量价、Up/Dn激活价五类价格，同时保留DA原生粒度、上下调价格状态及激活来源ID。',
      '- `processed/market_prices_15min.csv`：全区间15分钟总表，包含三类DA/容量价格、来源ID，以及4秒激活价的有价时间均值和有效秒数。激活均值只是研究整理值；阈值回测应使用4秒文件。',
      '- `processed/daily_coverage.csv`：逐日、逐字段应有量、有价量、显式空值和未报告量。',
      '- `processed/remaining_price_gaps.csv.gz`：余留缺口的UTC起止时间、原因和来源ID。',
      '- `processed/activation_refresh_changes.csv`：本轮相对11月1日归档的新有价点、变空点及有效价格修订数。',
      '- `sources.json`与`raw/reused/`：所有复用及合并选用的原始快照副本、原文件位置和原文SHA256。',
      '- `raw/fetched/`与`fetch_manifest.json`：本轮原始HTTP响应、无凭据参数、获取日期、重试和分段记录。',
      '- `data_dictionary.json`、`summary.json`、`monthly_coverage.json`、`validation.json`和`data_manifest.json`：字段定义、汇总、月度覆盖、独立验证与整理文件哈希。',
      '', '## 来源与合并方法','',
      '- DA：复用OMIE官方原始价格文件，支持`.1`及`.2/.3`修订版；缺失月份使用ENTSO-E A44的A01日前序列补抓，排除A07日内序列。',
      '- 容量：复用REE/eSIOS半岛区域8741的2130/634指标；缺失月份使用ENTSO-E A81/B95/A51日合同A01、A01/A02方向补抓。单位EUR/MW/15分钟。',
      '- 激活：ENTSO-E A84/A67/A96、标准产品A01，原生PT4S，非空价格类别A08；保留原价符号。',
      '- 早期DA是原生小时产品；只在其原交付小时内映射到15分钟及4秒时间轴，`da_native_resolution=PT60M`，不宣称存在独立的15分钟出清价。',
      '- A03可变块按块的起止时间无损展开；新空块会终止此前价格，真实0仍为有效价格。',
      '- 新查询有数据时，以该日新快照为准并记录相对旧快照的变化；查询失败或新查询无数据但有历史快照时保留历史快照并记载来源。本轮最终无查询错误。',
      '- 2025-10-26及2026-10-25为25小时日，A84接口最多允许24小时，分别拆为24小时和1小时查询，再按UTC无重叠拼接；春季23小时日保留原长度。',
      '- 主文件时间均为区间左端，终点不含；UTC是唯一时间键，本地ISO时间保留+01/+02偏移。价格为空时必须看状态列，不能替换为0。',
      '', '## 本轮激活价格修订对比','',
      '| 方向 | 原空值变为有价（4秒点） | 原有价变为空值 | 有效价格改变 |','|---|---:|---:|---:|']
    for d,label in [('up','Up'),('down','Dn')]:
        c=s['activation_refresh_changes'];lines.append(f"| {label} | {c[d+'_newly_priced']:,} | {c[d+'_now_null']:,} | {c[d+'_changed_valid_price']:,} |")
    lines += ['', '## 验证与边界','',
      f"6项边界测试通过。另独立逐行回读全部{v['rows_4s']:,}行4秒文件，验证固定步长、唯一时间键、UTC/本地时间一致、月份边界、五类价格对齐、空值状态以及15分钟覆盖秒数和均价；核验{v['raw_source_hashes_verified']:,}份原始快照哈希。",'',
      '本任务仅整理官方历史数据，不运行收益测算，不新增投标、中标或激活量假设；空值的业务原因仍待官方解释。价格数据不等于本站实际结算，官方后续仍可能修订。',
      '', '## 官方来源入口','',
      '- ENTSO-E生产API：https://web-api.tp.entsoe.eu/api；端点说明：https://transparencyplatform.zendesk.com/hc/en-us/articles/15696677194644-Request-Endpoint 。',
      '- ENTSO-E A03说明：https://transparencyplatform.zendesk.com/hc/en-us/articles/30262342482961-CurveType-A01-vs-CurveType-A03 。',
      '- OMIE官方文件：https://www.omie.es/en/file-download；REE/eSIOS：https://api.esios.ree.es/ 。',
      '- ENTSO-E原归档的官方字段、版本和章节证据：Counry_Investigation/project/es_afrr_cbmp_20261101/SOURCES.md。',
      '', '每个月4秒CSV均小于Excel单表行数上限，解压后可分别打开。读取压缩数据可用Python标准库gzip/csv。全区间不合并成单一Excel工作表。','']
    (BASE/'README.md').write_text('\n'.join(lines),encoding='utf-8')
    report=ROOT/'reports/simple_market_data_20250601_20261031_20261103'
    report.mkdir(exist_ok=True)
    (report/'数据整理与验收.md').write_text('\n'.join(lines)+f'\n本机数据目录：`{BASE}`\n',encoding='utf-8')
    print('Data dictionary and reports written')


if __name__=='__main__':
    main()
