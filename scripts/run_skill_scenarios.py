"""Release gate: run fixed natural-language scenarios against isolated project clones.

Each scenario clones a real project, optionally plants one labelled synthetic defect,
runs a headless Claude Code session with the installed plugin and records which
plugin Skills were invoked, the prompt-hook route, Stop-guard blocks and cost. Optional
probes then re-apply a fault to the session's result and require the project's checks
to fail, so prevention is observed rather than claimed. Sessions are paid model runs:
invoke this explicitly for a release, never from unit tests.
"""
import argparse
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


def replace_once(path, find, replace):
    data = path.read_bytes()
    if data.count(find.encode('utf-8')) != 1:
        raise ValueError(f'fault_target_must_match_once:{path.name}')
    path.write_bytes(data.replace(find.encode('utf-8'), replace.encode('utf-8'), 1))
    return data


def clone(project, destination, ref=None, link_modules=True, log_dir=None):
    """Checkout only the requested tree, without shared Git objects or long-path support."""
    commands = [
        ['git', '-c', 'core.longpaths=false', 'clone', '-q', '--local', '--no-hardlinks',
         '--no-checkout', str(project), str(destination)],
        ['git', '-c', 'core.longpaths=false', '-C', str(destination), 'checkout', '--detach', ref or 'HEAD'],
    ]
    for index, command in enumerate(commands):
        result = subprocess.run(command, capture_output=True)
        if log_dir is not None:
            Path(log_dir, f'clone{index}.stdout').write_bytes(result.stdout)
            Path(log_dir, f'clone{index}.stderr').write_bytes(result.stderr)
        result.check_returncode()
    modules = Path(project) / 'node_modules'
    if link_modules and modules.is_dir():
        link = destination / 'node_modules'
        if os.name == 'nt':
            subprocess.run(['cmd', '/c', 'mklink', '/J', str(link), str(modules)], check=True, capture_output=True)
        else:
            link.symlink_to(modules, target_is_directory=True)


def summarize_session(path):
    """Facts from a stream-json transcript; nothing is inferred from the final prose."""
    skills, tools, routes, blocks, result = [], Counter(), [], 0, {}
    for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get('type') == 'assistant':
            for block in event.get('message', {}).get('content', []):
                if isinstance(block, dict) and block.get('type') == 'tool_use':
                    tools[block.get('name')] += 1
                    if block.get('name') == 'Skill':
                        skills.append(str(block.get('input', {}).get('skill')))
        elif event.get('subtype') == 'hook_response':
            output = event.get('output') or ''
            if event.get('hook_name') == 'Stop' and '"block"' in output:
                blocks += 1
            if event.get('hook_name', '').startswith('UserPromptSubmit') and 'route' in output:
                try:
                    context = json.loads(json.loads(output)['hookSpecificOutput']['additionalContext'].split('\n', 1)[1])
                    routes.append(context.get('route', {}).get('skill'))
                except (ValueError, KeyError, IndexError, TypeError):
                    routes.append('unparsed')
        elif event.get('type') == 'result':
            result = event
    return {'skills': skills, 'plugin_skills': [s.split(':', 1)[-1] for s in skills if s.startswith('agentic-coding:')],
            'tools': dict(tools), 'routes': routes, 'stop_blocks': blocks,
            'turns': result.get('num_turns'), 'cost_usd': result.get('total_cost_usd'),
            'seconds': round((result.get('duration_ms') or 0) / 1000), 'answer': (result.get('result') or '')[:4000]}


def judge(expect, facts):
    failures = []
    if expect.get('skill') and expect['skill'] not in facts['plugin_skills']:
        failures.append(f"expected Skill {expect['skill']} not invoked (got {facts['plugin_skills'] or 'none'})")
    if expect.get('skill') is None and expect.get('no_plugin_skill') and facts['plugin_skills']:
        failures.append(f"no plugin Skill expected, got {facts['plugin_skills']}")
    if expect.get('route', 'unchecked') != 'unchecked' and expect['route'] not in (facts['routes'] or [None]):
        failures.append(f"hook route {facts['routes']} != {expect['route']}")
    for phrase in expect.get('answer_mentions', []):
        if phrase.casefold() not in facts['answer'].casefold():
            failures.append(f'answer does not mention {phrase!r}')
    return failures


def run_probe(repo, probe, timeout):
    """Re-apply one fault to the session's final tree and require the named checks to fail."""
    path = repo / probe['file']
    original = replace_once(path, probe['find'], probe['replace'])
    try:
        process = subprocess.run(probe['command'], cwd=repo, shell=True, capture_output=True, timeout=timeout)
    finally:
        path.write_bytes(original)
    detected = process.returncode != 0
    return {'name': probe['name'], 'detected': detected, 'exit': process.returncode,
            'ok': detected == probe.get('expect_detected', True),
            'tail': process.stdout.decode('utf-8', 'replace')[-600:]}


def run(scenario, output, claude, timeout):
    work = output / scenario['id']
    work.mkdir(parents=True)
    repo = work / 'repo'
    clone(Path(scenario['project']), repo)
    if scenario.get('fault'):
        fault = scenario['fault']
        replace_once(repo / fault['file'], fault['find'], fault['replace'])
        subprocess.run(['git', '-c', 'user.name=scenario', '-c', 'user.email=scenario@invalid', 'commit', '-qam',
                        fault['commit_message']], cwd=repo, check=True)
        (work / 'SYNTHETIC-FAULT.json').write_text(json.dumps(fault, ensure_ascii=False, indent=2), encoding='utf-8')
    transcript = work / 'session.jsonl'
    started = time.time()
    with transcript.open('wb') as stream:
        process = subprocess.run([claude, '-p', scenario['prompt'], '--permission-mode', 'bypassPermissions',
                                  '--output-format', 'stream-json', '--verbose', '--include-hook-events'],
                                 cwd=repo, stdout=stream, stderr=subprocess.PIPE, timeout=timeout)
    facts = summarize_session(transcript)
    facts.update(exit=process.returncode, wall_seconds=round(time.time() - started))
    failures = judge(scenario.get('expect', {}), facts)
    probes = [run_probe(repo, probe, timeout) for probe in scenario.get('probes', [])]
    failures += [f"probe {p['name']} detected={p['detected']}" for p in probes if not p['ok']]
    return {'id': scenario['id'], 'project': scenario['project'], 'prompt': scenario['prompt'],
            'expect': scenario.get('expect', {}), 'facts': facts, 'probes': probes,
            'status': 'PASS' if not failures else 'FAIL', 'failures': failures}


def markdown(results):
    lines = ['# Skill scenario gate', '', '| Scenario | Expected | Invoked | Route | Stop blocks | Probes | Cost | Status |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    for r in results:
        probes = ', '.join(f"{p['name']}={'caught' if p['detected'] else 'missed'}" for p in r['probes']) or '-'
        lines.append(f"| {r['id']} | {r['expect'].get('skill') or 'none'} | {', '.join(r['facts']['plugin_skills']) or 'none'} "
                     f"| {', '.join(str(x) for x in r['facts']['routes']) or '-'} | {r['facts']['stop_blocks']} | {probes} "
                     f"| ${r['facts']['cost_usd'] or 0:.2f} / {r['facts']['seconds']}s | {r['status']} |")
    for r in results:
        if r['failures']:
            lines += ['', f"**{r['id']}**: " + '; '.join(r['failures'])]
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenarios', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='New directory for clones, transcripts and the report')
    parser.add_argument('--only', action='append', default=[])
    parser.add_argument('--claude', default=shutil.which('claude') or 'claude')
    parser.add_argument('--timeout', type=float, default=3000)
    parser.add_argument('--dry-run', action='store_true', help='List selected scenarios without cloning or model runs')
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding='utf-8')  # Reports carry Korean prompts; never emit the console codec.
    scenarios = [s for s in json.loads(args.scenarios.read_text(encoding='utf-8'))['scenarios']
                 if not args.only or s['id'] in args.only]
    if args.dry_run:
        print(json.dumps([{key: s.get(key) for key in ('id', 'project', 'expect')} for s in scenarios], ensure_ascii=False))
        return 0
    args.output.mkdir(parents=True, exist_ok=False)
    results = [run(scenario, args.output, args.claude, args.timeout) for scenario in scenarios]
    (args.output / 'report.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    (args.output / 'report.md').write_text(markdown(results), encoding='utf-8')
    print(markdown(results))
    return 0 if all(r['status'] == 'PASS' for r in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
