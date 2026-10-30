"""Introduction commit of each rule and Skill, by `git log -S` (pickaxe) on its current wording.

Rules are the bullets of authoring/global/AGENTS.md and CLAUDE.md, each Skill's SKILL.md, and named hook rules
(by a distinctive code string). For every element: the oldest commit whose diff changes the count of its
phrase (current wording introduced), the commit subject, and research/eval docs that commit also touched.
Writes provenance.json. Evidence grades are assigned in the audit record, not here.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / 'plugins/agentic-coding/skills'
HOOK_RULES = {
    'router: route table + default delegate': ('plugins/agentic-coding/hooks/workflow_context.py', "DELEGATE = ('agent-workflow'"),
    'router: SYMPTOM -> diagnose': ('plugins/agentic-coding/hooks/workflow_context.py', "DIAGNOSE = ('diagnose'"),
    'router: QUESTION/TRIVIAL stay direct': ('plugins/agentic-coding/hooks/workflow_context.py', 'TRIVIAL_EDIT = '),
    'guard: edit after last executed command': ('plugins/agentic-coding/hooks/completion_guard.py', 'changed after the last executed command'),
    'guard: independent check required': ('plugins/agentic-coding/hooks/completion_guard.py', 'INDEPENDENT VERIFIER'),
    'guard: shell/interpreter edit sizing': ('plugins/agentic-coding/hooks/completion_guard.py', 'WRITE_CALL = re.compile'),
}


def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, encoding='utf-8',
                          check=False).stdout


def introduced(phrase, *paths):
    lines = git('log', '-S', phrase, '--reverse', '--format=%h|%ad|%s', '--date=short', '--', *paths).splitlines()
    if not lines:
        return None
    sha, date, subject = lines[0].split('|', 2)
    docs = [p for p in git('show', '--name-only', '--format=', sha).splitlines()
            if p.startswith(('docs/research/', 'evals/')) and p.endswith('.md')]
    return {'commit': sha, 'date': date, 'subject': subject, 'docs': docs[:6], 'changes': len(lines)}


def bullets(path):
    text = (ROOT / path).read_text(encoding='utf-8')
    section = None
    for line in text.splitlines():
        if line.startswith('## '):
            section = line[3:].strip()
        elif line.startswith('- '):
            body = line[2:].strip()
            for i, sentence in enumerate(re.split(r'(?<=\.)\s+', body)):
                if len(sentence) > 25:
                    yield section, sentence


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    rows = []
    for path in ('authoring/global/AGENTS.md', 'CLAUDE.md'):
        for section, sentence in bullets(path):
            phrase = sentence[:60]
            sources = [path] + (['AGENTS.md'] if path == 'CLAUDE.md' else [])
            rows.append({'element': f'{path} / {section}', 'text': sentence, 'bytes': len(sentence.encode('utf-8')),
                         'introduced': introduced(phrase, *sources) or introduced(phrase)})
    for skill in sorted(p.name for p in SKILLS.iterdir() if p.is_dir()):
        text = (SKILLS / skill / 'SKILL.md').read_text(encoding='utf-8')
        description = re.search(r'^description:\s*(.+)$', text, re.M)
        first = git('log', '--reverse', '--format=%h|%ad|%s', '--date=short', '--', f'skills/{skill}/SKILL.md',
                    f'plugins/agentic-coding/skills/{skill}/SKILL.md').splitlines()
        sha, date, subject = first[0].split('|', 2) if first else (None, None, None)
        current = description.group(1).strip()[:60] if description else ''
        rows.append({'element': f'skill / {skill}', 'text': description.group(1).strip() if description else '',
                     'bytes': len(text.encode('utf-8')),
                     'first_commit': {'commit': sha, 'date': date, 'subject': subject},
                     'commits_touching': len(first),
                     'introduced': introduced(current, f'plugins/agentic-coding/skills/{skill}/SKILL.md',
                                              f'skills/{skill}/SKILL.md') if current else None})
    for name, (path, phrase) in HOOK_RULES.items():
        rows.append({'element': f'hook / {name}', 'text': phrase, 'introduced': introduced(phrase, path)})
    (Path(args.output) / 'provenance.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding='utf-8')
    for r in rows:
        i = r.get('introduced') or {}
        print(f"{r['element'][:60]:60} {i.get('commit')} {i.get('date')} {str(i.get('subject'))[:70]}")


if __name__ == '__main__':
    sys.exit(main())
