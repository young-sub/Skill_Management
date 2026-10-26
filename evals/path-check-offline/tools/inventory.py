"""List write paths that reference nothing an uncommitted diff changed.

Static and regex-based: SQL write statements in JavaScript/TypeScript sources, their
top-level enclosing symbols and callers. A candidate is a call chain from a writer of a
changed column up to an entry point in which no symbol was changed or refers to a
changed symbol. Candidates are leads for a verifier, not verdicts.
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

SUFFIXES = {'.ts', '.tsx', '.js', '.jsx', '.mjs', '.cjs'}
WRITE = re.compile(r'\b(?:INSERT\s+(?:OR\s+\w+\s+)?INTO|REPLACE\s+INTO|UPDATE|DELETE\s+FROM)\s+([A-Za-z_]\w*)',
                   re.IGNORECASE)
DEFINITION = re.compile(r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)'
                        r'|^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)'
                        r'|^export\s+(default)\b')
IDENTIFIER = re.compile(r'[A-Za-z_$][\w$]{2,}')
CALL = re.compile(r'(?<![\w$])([A-Za-z_$][\w$]*)\s*\(')
FUNCTION_BODY = re.compile(r'\s*(?:export\s+)?(?:default\s+)?(?:async\s+)?function\b')
HUNK = re.compile(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@')
IMPORT_NAMED = re.compile(r'\bimport\s+(?:type\s+)?(?:[A-Za-z_$][\w$]*\s*,\s*)?\{([^}]*)\}\s*from')
IMPORT_DEFAULT = re.compile(r'\bimport\s+([A-Za-z_$][\w$]*)\s*(?:,|\s+from)')
MAX_DEPTH = 6
MAX_ROOTS = 8
MAX_STEPS = 5000


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True, text=True,
                          encoding='utf-8', errors='replace', check=True).stdout


def is_test(path):
    lowered = path.lower()
    return '/tests/' in '/' + lowered or '.test.' in lowered or '.spec.' in lowered or lowered.startswith('test')


def snake(name):
    return re.sub(r'(?<=[a-z0-9])([A-Z])', r'_\1', name).lower()


def symbols(text):
    """Top-level definitions as (name, first line, last line), 1-based and inclusive."""
    lines = text.splitlines()
    starts = [(index + 1, next(g for g in match.groups() if g))
              for index, line in enumerate(lines) for match in [DEFINITION.match(line)] if match]
    return [(name, start, (starts[i + 1][0] - 1) if i + 1 < len(starts) else len(lines))
            for i, (start, name) in enumerate(starts)]


def changes(repo):
    """Changed new-side line numbers and changed-line identifiers per tracked file."""
    lines, words = {}, set()
    current = None
    for line in git(repo, 'diff', '-U0', '--no-color', 'HEAD').splitlines():
        if line.startswith('+++ '):
            current = None if line.endswith('/dev/null') else line[6:]
        elif line.startswith('@@') and current:
            start, count = HUNK.match(line).groups()
            start, count = int(start), int(count if count is not None else 1)
            # A pure deletion still touches the symbol around its position.
            lines.setdefault(current, set()).update(range(start, start + max(count, 1)))
        elif line[:1] in '+-' and not line.startswith(('+++', '---')) and current:
            words.update(IDENTIFIER.findall(line[1:]))
    return lines, words


def written_columns(statement):
    """Columns an INSERT/REPLACE column list or an UPDATE SET clause assigns."""
    listed = re.match(r'\s*(?:INSERT|REPLACE)[^(]*\(([^)]*)\)', statement, re.IGNORECASE)
    if listed:
        return {c.strip().strip('"`[]') for c in listed.group(1).split(',') if c.strip()}
    clause = re.search(r'\bSET\b(.*?)(?:\bWHERE\b|\bRETURNING\b|$)', statement, re.IGNORECASE | re.DOTALL)
    return set(re.findall(r'([A-Za-z_]\w*)\s*=', clause.group(1))) if clause else set()


def imported(text):
    """Local name → exported name for named imports; default imports map to themselves."""
    names = {}
    for group in IMPORT_NAMED.findall(text):
        for part in group.split(','):
            part = re.sub(r'^\s*type\s+', '', part).strip()
            if part:
                original, _, local = part.partition(' as ')
                names[(local or original).strip()] = original.strip()
    names.update({name: name for name in IMPORT_DEFAULT.findall(text)})
    return names


def inventory(repo):
    repo = Path(repo)
    changed_lines, changed_words = changes(repo)
    # Search only the top-level directories the change touches (the application, not offline tools).
    scopes = {Path(p).parts[0] for p in changed_lines if len(Path(p).parts) > 1}
    files = [p for p in git(repo, 'ls-files').splitlines()
             if Path(p).suffix in SUFFIXES and not is_test(p) and Path(p).parts[0] in scopes]
    texts = {p: (repo / p).read_text(encoding='utf-8', errors='replace') for p in files if (repo / p).is_file()}
    table = {(p, name): (start, end) for p, text in texts.items() for name, start, end in symbols(text)}
    split = {p: text.splitlines() for p, text in texts.items()}
    bodies = {key: '\n'.join(split[key[0]][start - 1:end]) for key, (start, end) in table.items()}
    refs = {key: set(IDENTIFIER.findall(body)) for key, body in bodies.items()}
    calls = {key: set(CALL.findall(body)) for key, body in bodies.items()}
    imports = {p: imported(text) for p, text in texts.items()}
    touched = {key for key, (start, end) in table.items()
               if any(start <= n <= end for n in changed_lines.get(key[0], ()))}
    # Constants (schemas, limits) built from a changed symbol carry the change to their users.
    names = {name for _, name in touched}
    grew = True
    while grew:
        grew = False
        for key, body in bodies.items():
            if key not in touched and not FUNCTION_BODY.match(body) and refs[key] & names:
                touched.add(key)
                names.add(key[1])
                grew = True
    writers = []
    for p, text in texts.items():
        for match in WRITE.finditer(text):
            if match.group(1).upper() == 'SET':  # ON CONFLICT ... DO UPDATE SET belongs to its INSERT
                continue
            line = text.count('\n', 0, match.start()) + 1
            owner = next((key for key, (start, end) in table.items() if key[0] == p and start <= line <= end), None)
            statement = text[match.start():match.start() + 600].split('`')[0]
            writers.append({'file': p, 'line': line, 'table': match.group(1), 'owner': owner, 'statement': statement})
    columns = {snake(w) for w in changed_words} | set(changed_words)
    relevant = [w for w in writers if written_columns(w['statement']) & columns]
    defined = {}
    for key in table:
        defined.setdefault(key[1], []).append(key)
    callers = {}
    for key in table:
        for name in calls[key]:
            # Same-file definition first; otherwise only files exporting the imported name.
            if (key[0], name) in table:
                targets = [(key[0], name)]
            elif name in imports[key[0]]:
                targets = defined.get(imports[key[0]][name], [])
            else:
                targets = []
            for other in targets:
                if other != key:
                    callers.setdefault(other, set()).add(key)

    def covered(key):
        return key in touched or bool(refs[key] & names)

    def label(key):
        return f'{key[0]}:{table[key][0]} {key[1]}'

    candidates, unknown = [], []
    for writer in relevant:
        where = f"{writer['file']}:{writer['line']}"
        if writer['owner'] is None:
            unknown.append({'writer': where, 'table': writer['table'], 'reason': 'no top-level enclosing symbol'})
            continue
        # Breadth-first with a per-chain cycle check: paths that merge into one entry point stay
        # distinct, keyed by the writer and its two nearest callers, keeping the shortest chain.
        roots, queue, steps = {}, [[writer['owner']]], 0
        while queue and len(roots) < MAX_ROOTS and steps < MAX_STEPS:
            chain, steps = queue.pop(0), steps + 1
            if covered(chain[-1]):
                continue
            ups = sorted(c for c in callers.get(chain[-1], ()) if c not in chain)
            if not ups or len(chain) >= MAX_DEPTH:
                roots.setdefault(tuple(chain[:3]), chain)
            else:
                queue.extend(chain + [c] for c in ups)
        if roots:
            candidates.append({'writer': where, 'table': writer['table'], 'owner': label(writer['owner']),
                               'paths': [[label(k) for k in chain] for chain in roots.values()]})
    return {'applicable': bool(relevant), 'scopes': sorted(scopes),
            'changed_symbols': sorted(f'{f} {n}' for f, n in touched),
            'relevant_writers': len(relevant), 'candidates': candidates, 'unknown': unknown}


def render(result):
    if not result['applicable']:
        return '(해당 없음: 변경된 이름과 같은 열을 쓰는 SQL 저장문을 찾지 못했습니다.)'
    if not result['candidates'] and not result['unknown']:
        return '(후보 없음: 찾은 저장 경로는 모두 변경된 코드에 닿습니다.)'
    lines = []
    for c in result['candidates']:
        lines.append(f"- {c['table']} 저장 {c['writer']} ({c['owner'].split(' ')[-1]})")
        lines += ['  - ' + ' ← '.join(k.split(' ')[-1] + ' (' + k.split(' ')[0] + ')' for k in path)
                  for path in c['paths']]
    lines += [f"- {u['table']} 저장 {u['writer']}: 해석 불가 ({u['reason']})" for u in result['unknown']]
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo')
    parser.add_argument('--text', action='store_true', help='Print the prompt rendering instead of JSON')
    args = parser.parse_args()
    result = inventory(args.repo)
    print(render(result) if args.text else json.dumps(result, ensure_ascii=False, indent=2))
