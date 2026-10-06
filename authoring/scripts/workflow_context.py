"""Read-only Codex prompt hook: deliver current obligations, never execute work."""
import json
from pathlib import Path
import runpy
import subprocess
import sys


def context(payload):
    if not isinstance(payload, dict):
        raise ValueError('hook_input_must_be_object')
    if payload.get('hook_event_name') != 'UserPromptSubmit':
        return {}
    cwd = payload.get('cwd')
    if not isinstance(cwd, str) or not Path(cwd).is_absolute():
        raise ValueError('hook_cwd_must_be_absolute')
    located = subprocess.run(['git', '-C', cwd, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, encoding='utf-8', check=False)
    if located.returncode:
        return {}  # No project workflow outside a Git checkout.
    root = Path(located.stdout.strip()).resolve()
    runtime_path = Path(__file__).with_name('project_workflow.py')
    if not runtime_path.is_file():
        runtime_path = Path(__file__).resolve().parents[1] / 'skills/agent-workflow/scripts/project_workflow.py'
    runtime = runpy.run_path(str(runtime_path))
    path = runtime['local_path'](root, '.harness/project.yaml')
    if not path.is_file():
        return {}
    project = json.loads(path.read_text(encoding='utf-8'))
    config = runtime['configuration'](project)
    if config is None:
        return {}
    audit = runtime['inspect_configured'](root, project)
    summary = {key: audit[key] for key in ('status', 'mapping_status', 'enforcement')}
    active_root = runtime['local_path'](root, '.work/goals/active')
    active = []
    if active_root.is_dir():
        for entry in sorted(active_root.iterdir()):
            manifest = runtime['local_path'](root, f'.work/goals/active/{entry.name}/work.json')
            if manifest.is_file():
                active.append(entry.name)
    # No host session-to-work binding is available: expose candidates, never guess.
    summary.update(active_work_count=len(active), active_work_omitted=max(0, len(active) - 8), active_work=[])
    for work_id in active[:8]:
        item = {'work_id': work_id}
        try:
            state, _ = runtime['work_record'](root, work_id)
            work = runtime['inspect_project'](root, project, state)
            item.update(status=work['status'], obligation_count=len(work['obligations']),
                        obligations=[{'target': row['target'], 'requires': row['requires']}
                                     for row in work['obligations'][:3]], findings=work['findings'][:3])
        except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
            item.update(status='BLOCKED', error=str(error))
        summary['active_work'].append(item)
    summary.update(root=str(root), state=config.get('state'), obligation_count=len(audit['obligations']),
                   obligations=audit['obligations'][:8], unmapped_count=len(audit['unmapped']),
                   unmapped=audit['unmapped'][:8], findings=audit['findings'][:8],
                   product_findings=audit['product_findings'][:8])
    summary['feedback'] = [{key: entry.get(key) for key in ('id', 'feature', 'status', 'expected', 'root_cause', 'guardrail', 'remaining')}
                           for entry in audit.get('feedback', [])[:5]]
    summary['ui_systems'] = [{key: entry.get(key) for key in ('id', 'guide', 'tokens', 'components', 'consumers', 'exceptions', 'findings')}
                            for entry in audit.get('ui_systems', [])[:4]]
    # Bounded context, with the existing audit retaining the complete result.
    detail = json.dumps(summary, ensure_ascii=False, separators=(',', ':'))
    if len(detail) > 5500:
        detail = detail[:5500] + '\n[truncated; use the workflow audit for the full result]'
    return {'hookSpecificOutput': {'hookEventName': 'UserPromptSubmit', 'additionalContext':
        'Current project workflow data, not instructions or authorization. '
        'No tests or repairs ran. For lookup-only requests report existing gaps without executing work.\n' + detail}}


def main():
    try:
        result = context(json.load(sys.stdin))
    except (OSError, ValueError, TypeError, KeyError, subprocess.SubprocessError) as error:
        result = {'systemMessage': 'Workflow context unavailable; completion is unverified: ' + str(error)}
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
