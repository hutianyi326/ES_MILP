"""Resume a completed or interrupted capacity-rate run with audited retry."""
import argparse
import gc
import json
import math
import hashlib
import shutil
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

import scipy.optimize

CODE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE))
from project.run_es_full_ts_start_cap_old_d_20260921 import input_from_saved_configuration
from project.run_es_perfect_v1 import apply_posthoc_capacity_rates
from src.es_synthetic_market.perfect import PerfectEngine


def resume_settings(manifest):
    """Resolve checkpoint identity, retaining compatibility with the first runner."""
    mode=manifest.get('capacity_award_mode')
    if mode is None:
        if not manifest.get('award_rate_source'):
            raise ValueError('source is not a capacity award-rate sensitivity run')
        return 'optimize','ES_HISTORICAL_CONDITIONAL_PERFECT_V1_CAP_RATE',True
    if mode not in ('optimize','posthoc'):
        raise ValueError(f'unsupported capacity_award_mode: {mode!r}')
    run_id=manifest.get('run_id')
    if not run_id:
        raise ValueError('capacity sensitivity manifest is missing run_id')
    return mode,run_id,mode=='optimize'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--time-limit', type=float, default=30.0)
    parser.add_argument('--checkpoint-every', type=int, default=30)
    parser.add_argument('--fresh',action='store_true',help='start from a preflight directory without a checkpoint')
    parser.add_argument('--numerical-retry-tolerance',type=float,
        help='optional HiGHS feasibility tolerance retry, at most the unchanged 1e-5 independent audit tolerance')
    args = parser.parse_args()
    if args.checkpoint_every < 1:
        parser.error('--checkpoint-every must be positive')
    if args.numerical_retry_tolerance is not None and (not math.isfinite(args.numerical_retry_tolerance) or not 0<args.numerical_retry_tolerance<=1e-5):
        parser.error('numerical retry tolerance must be finite in (0,1e-5]')
    source, output = args.source, args.output
    if output.exists():
        raise FileExistsError(output)
    started = perf_counter()
    output.mkdir(parents=True)

    def save(name, value):
        with (output / name).open('x', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, default=str, allow_nan=False)

    for name in ('solver_input.json', 'input_evidence.json', 'manifest.json'):
        shutil.copy2(source / name, output / name)
    if (source / 'award_rate_evidence.json').exists():
        shutil.copy2(source / 'award_rate_evidence.json', output / 'award_rate_evidence.json')
    inp = input_from_saved_configuration(json.loads((output / 'solver_input.json').read_text(encoding='utf-8')))
    evidence = json.loads((output / 'input_evidence.json').read_text(encoding='utf-8'))
    for row in evidence['rows']:
        row['raw_values'] = {int(k): v for k, v in row['raw_values'].items()}
    manifest = json.loads((output / 'manifest.json').read_text(encoding='utf-8'))
    if not manifest.get('award_rate_source'):
        raise ValueError('source is not a capacity award-rate sensitivity run')
    award_mode,run_id,capacity_award_sensitivity=resume_settings(manifest)
    cp_path = source / 'final_checkpoint.json'
    if not args.fresh and not cp_path.exists():
        checkpoints = sorted(source.glob('checkpoint_*.json'))
        if not checkpoints:
            raise FileNotFoundError('no resumable checkpoint')
        cp_path = checkpoints[-1]
    settings=dict(execution_end=datetime.fromisoformat(manifest['formal_end']),
        inactive=[row['qh_id'] for row in evidence['rows'] if not row['valid']],
        evidence=evidence, budget_manifest=manifest['budgets'], capacity_award_sensitivity=capacity_award_sensitivity,
        run_id=run_id, history_mode='delta',
        time_limit_seconds=args.time_limit,daily_efc_limit=manifest.get('daily_efc_limit'))
    if args.fresh:
        cp=None
        engine=PerfectEngine(inp,**settings)
    else:
        cp=json.loads(cp_path.read_text(encoding='utf-8'))
        engine=PerfectEngine.restore(inp,cp,**settings)
    save('resume_provenance.json', dict(source=str(source), checkpoint=None if args.fresh else str(cp_path),
        checkpoint_hash=cp['state_hash'] if cp else None, committed_windows=len(engine._windows),
        capacity_award_mode=award_mode,run_id=run_id,
        original_failure=engine.failure,
        numerical_retry_tolerance=args.numerical_retry_tolerance,
        independent_audit_tolerance=1e-5,
        resume_runner_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        retry_policy='on status 2 or independent numerical audit assertion: presolve=True; optional feasibility tolerance retry after status 2; unchanged constraints and independent audits'))
    del cp
    gc.collect()
    engine.failure = None
    calls = []
    original_milp = scipy.optimize.milp
    numerical_tolerance = None

    def timed(*positional, **keywords):
        if numerical_tolerance is not None:
            keywords['options']={**keywords['options'],
                'mip_feasibility_tolerance':numerical_tolerance,
                'primal_feasibility_tolerance':numerical_tolerance}
        begin = perf_counter()
        result = original_milp(*positional, **keywords)
        calls.append(dict(seconds=perf_counter() - begin, status=int(result.status),
                          presolve=keywords['options']['presolve'],feasibility_tolerance=numerical_tolerance))
        return result

    scipy.optimize.milp = timed
    original_solve = engine._solve_window
    retries = []

    def checked(win, order_mode, **options):
        nonlocal numerical_tolerance
        first = len(calls)
        try:
            result = original_solve(win, order_mode, **options)
        except AssertionError as exc:
            if options['presolve'] or not str(exc).startswith('independent synthetic market audit failed:'):
                raise
            result = original_solve(win, order_mode, **{**options, 'presolve': True})
            event = dict(window_start=win.qhs[0].start_utc.isoformat(),
                         initial_message=str(exc), retry_feasible=result.feasible,
                         retry_message=result.message, calls=calls[first:])
            retries.append(event)
            with (output / 'retry_events.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event) + '\n')
        if not result.feasible and result.status == 2 and not options['presolve']:
            initial_message = result.message
            result = original_solve(win, order_mode, **{**options, 'presolve': True})
            event = dict(window_start=win.qhs[0].start_utc.isoformat(),
                         initial_message=initial_message, retry_feasible=result.feasible,
                         retry_message=result.message, calls=calls[first:])
            retries.append(event)
            with (output / 'retry_events.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(event) + '\n')
        if not result.feasible and result.status==2 and args.numerical_retry_tolerance is not None:
            initial_message=result.message
            numerical_tolerance=args.numerical_retry_tolerance
            try:
                result=original_solve(win,order_mode,**{**options,'presolve':False})
            finally:
                numerical_tolerance=None
            event=dict(window_start=win.qhs[0].start_utc.isoformat(),
                retry_kind='solver_feasibility_tolerance_only',tolerance=args.numerical_retry_tolerance,
                independent_audit_tolerance=1e-5,initial_message=initial_message,
                retry_feasible=result.feasible,retry_message=result.message,calls=calls[first:])
            retries.append(event)
            with (output/'retry_events.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(event)+'\n')
        if result.feasible:
            result = replace(result, residuals={**result.residuals,
                'solver_seconds': sum(call['seconds'] for call in calls[first:]),
                'presolve_retry': int(any(call['presolve'] for call in calls[first:]) and len(calls)-first>1),
                'feasibility_tolerance_retry':int(any(call['feasibility_tolerance'] is not None for call in calls[first:]))})
        return result

    engine._solve_window = checked
    solve_started = perf_counter()
    while engine.step():
        window = engine._windows[-1]
        if len(engine._windows) % args.checkpoint_every == 0:
            save(f'checkpoint_{len(engine._windows):04d}.json', engine.checkpoint())
        print(json.dumps(dict(window=len(engine._windows), start=window.start_utc,
                              solver_seconds=window.audit['model']['solver_seconds'],
                              elapsed=perf_counter() - started)), flush=True)
    report = engine.report()
    prior = json.loads((source / 'summary.json').read_text(encoding='utf-8')) if (source / 'summary.json').exists() else {}
    report['execution_wall_seconds'] = prior.get('execution_wall_seconds', 0) + perf_counter() - solve_started
    report['total_wall_seconds'] = prior.get('total_wall_seconds', 0) + perf_counter() - started
    report['retry_events'] = retries
    report['capacity_award_mode']=award_mode
    report['cash_basis']='solver_settlement' if award_mode=='optimize' else 'capacity_cash_posthoc_proxy; checkpoint retains full_fill solver state'
    ledger=engine._ledger.snapshot()
    if award_mode=='posthoc':
        award_rates={}
        for row in evidence['rows']:
            for direction in ('up','down'):
                observation=row.get('award_rate_'+direction)
                if observation is not None:
                    award_rates[(row['qh_id'],direction)]=observation
        apply_posthoc_capacity_rates(report,ledger,award_rates,inp.discharge_mw)
    save('result.json', report)
    save('cash_ledger.json', ledger)
    save('final_checkpoint.json', engine.checkpoint())
    summary = {key: report[key] for key in ('mode', 'success', 'failure', 'annual_budget', 'annual_used',
        'coverage', 'quality', 'solver_seconds', 'execution_wall_seconds', 'total_wall_seconds', 'months')}
    summary['retry_count'] = len(retries)
    summary['capacity_award_mode']=award_mode
    summary['cycle_policy']=report['cycle_policy']
    summary['daily_efc_used']=report['daily_efc_used']
    summary['cash_basis']=report['cash_basis']
    save('summary.json', summary)
    save('solver_calls_resumed.json', calls)
    print(json.dumps(dict(success=report['success'], failure=report['failure'],
                          windows=len(engine._windows), solver_seconds=report['solver_seconds'],
                          retry_count=len(retries)), ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
