"""Local hook latency: run the plugin hooks the way the Windows host does and time each call.

UserPromptSubmit: every recorded real user prompt from routes.json, cwd = this repository.
Stop: every real session transcript, cwd = the session's recorded cwd when it still exists. Both hooks
are read-only (the guard runs `git diff --numstat`). Writes latency.json; prints p50/p95.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PLUGIN = ROOT / 'plugins' / 'agentic-coding'
PROJECTS = Path.home() / '.claude' / 'projects'


def run_hook(name, payload, cwd):
    command = [sys.executable, '-c', "import os,runpy; runpy.run_path(os.path.join(os.environ['CLAUDE_PLUGIN_ROOT'],"
               f"'hooks','{name}'),run_name='__main__')"]
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(PLUGIN), PYTHONIOENCODING='utf-8')
    env.pop('AGENT_WORKFLOW_CONTEXT', None)
    start = time.perf_counter()
    done = subprocess.run(command, input=json.dumps(payload, ensure_ascii=False), capture_output=True, text=True,
                          encoding='utf-8', cwd=cwd, env=env, timeout=60)
    return (time.perf_counter() - start) * 1000, done.returncode, done.stdout


def pct(values, q):
    values = sorted(values)
    return round(values[min(len(values) - 1, int(q * len(values)))], 1) if values else None


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    out = Path(args.output)
    routes = json.loads((out / 'routes.json').read_text(encoding='utf-8'))
    sessions = json.loads((out / 'real_sessions.json').read_text(encoding='utf-8'))['sessions']
    ups = []
    for row in (r for r in routes if r['kind'] == 'user'):
        ms, code, stdout = run_hook('workflow_context.py', {'hook_event_name': 'UserPromptSubmit', 'cwd': str(ROOT),
                                                             'prompt': row['text'], 'session_id': 'lean-audit'}, ROOT)
        ups.append({'id': row['id'], 'ms': round(ms, 1), 'exit': code, 'context_bytes': len(stdout.encode('utf-8'))})
    stop = []
    for s in sessions:
        transcript = PROJECTS / s['project'] / f"{s['session']}.jsonl"
        cwd = Path(s['cwd']) if s.get('cwd') and Path(s['cwd']).is_dir() else ROOT
        ms, code, stdout = run_hook('completion_guard.py', {'hook_event_name': 'Stop', 'cwd': str(cwd),
                                                             'transcript_path': str(transcript), 'stop_hook_active': False,
                                                             'session_id': s['session']}, cwd)
        decision = json.loads(stdout).get('decision') if stdout.strip().startswith('{') else None
        stop.append({'session': s['session'], 'ms': round(ms, 1), 'exit': code, 'decision': decision,
                     'reason': json.loads(stdout).get('reason', '')[:300] if decision else '',
                     'transcript_mb': round(transcript.stat().st_size / 1e6, 2)})
    baseline = [run_hook('workflow_context.py', {'hook_event_name': 'Other', 'cwd': str(ROOT)}, ROOT)[0] for _ in range(20)]
    summary = {
        'python_start_baseline_ms': {'p50': pct(baseline, .5), 'p95': pct(baseline, .95), 'n': len(baseline)},
        'user_prompt_submit_ms': {'p50': pct([u['ms'] for u in ups], .5), 'p95': pct([u['ms'] for u in ups], .95), 'n': len(ups)},
        'stop_ms': {'p50': pct([s['ms'] for s in stop], .5), 'p95': pct([s['ms'] for s in stop], .95), 'n': len(stop)},
        'stop_blocks_at_session_end': sum(1 for s in stop if s['decision'] == 'block'),
        'nonzero_exits': sum(1 for x in ups + stop if x['exit']),
    }
    (out / 'latency.json').write_text(json.dumps({'summary': summary, 'ups': ups, 'stop': stop}, ensure_ascii=False, indent=1),
                                      encoding='utf-8')
    print(json.dumps(summary, indent=1))


if __name__ == '__main__':
    sys.exit(main())
