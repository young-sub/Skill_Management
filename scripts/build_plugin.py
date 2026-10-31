"""Build the current public Skill cohort as a local plugin, without installing it.

Public Skill files, shared execution tools and the read-only prompt hook enter the package.
Generated-resource drift is rejected before writing. A destination is immutable:
build a new directory for an update; host installation owns cache/version handling.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def index_blobs(sources):
    """The staged bytes of each tracked source (None when untracked), read in one `git cat-file` batch."""
    request = ''.join(f':{source}\n' for source in sources).encode('utf-8')
    output = subprocess.run(['git', '-C', str(ROOT), 'cat-file', '--batch'], input=request,
                            capture_output=True, check=True).stdout
    blobs, offset = {}, 0
    for source in sources:
        end = output.index(b'\n', offset)
        header = output[offset:end].split()
        offset = end + 1
        if len(header) == 2 and header[1] == b'missing':
            blobs[source] = None
            continue
        size = int(header[2])
        blobs[source] = output[offset:offset + size]
        offset += size + 1
    return blobs


def source_bytes(path, staged):
    """Package bytes for one source: its Git line endings, never the checkout's.

    With core.autocrlf the work tree holds CRLF copies of LF files, and a POSIX launcher
    whose shebang ends in CR cannot start. A file identical to its staged blob up to line
    endings uses the staged bytes; a dirty edit keeps its content with the staged line ending."""
    data = path.read_bytes()
    if staged is None or data == staged:
        return data
    if data.replace(b'\r\n', b'\n') == staged.replace(b'\r\n', b'\n') and b'\r' not in staged:
        return staged
    return data.replace(b'\r\n', b'\n') if b'\r' not in staged else data


def build(output):
    output = output.resolve()
    if output.exists():
        raise ValueError('Destination already exists; use a new build directory')
    if output.is_relative_to(ROOT) and output.relative_to(ROOT).parts[0] not in {'.work', 'dist'}:
        raise ValueError('Repository builds must be under .work or dist')
    sync = subprocess.run(['powershell', '-NoProfile', '-File',
                           str(ROOT / 'scripts/sync-skill-resources.ps1'), '-Check'],
                          cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
    if sync.returncode:
        raise ValueError('Generated resource check failed:\n' + sync.stdout + sync.stderr)
    def git(*tokens):
        return subprocess.check_output(['git', '-C', str(ROOT), *tokens], text=True, encoding='utf-8').strip()

    if Path(git('rev-parse', '--show-toplevel')).resolve() != ROOT.resolve():
        raise ValueError('Package source must be its own Git checkout root')
    origin = {'schema_version': 1, 'source_commit': git('rev-parse', 'HEAD'),
              'source_tree': git('rev-parse', 'HEAD^{tree}'),
              'source_dirty': bool(git('status', '--porcelain')),
              'limit': 'Build observation, not a signature or task/host verdict. Dirty source bytes are bound by package-files.json.'}
    manifest = json.loads((ROOT / 'distribution/plugin.json').read_text(encoding='utf-8'))
    catalog = json.loads((ROOT / 'distribution/catalog.json').read_text(encoding='utf-8'))
    names = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--', 'skills'],
                           check=True, capture_output=True).stdout.decode('utf-8').split('\0')
    selected = {name: name for name in names if name and
                Path(name).parts[1] in catalog['public_skills']}
    selected['scripts/run_check.py'] = 'authoring/scripts/run_check.py'
    selected['scripts/probe_check.py'] = 'authoring/scripts/probe_check.py'
    selected['scripts/update_plugin.py'] = 'scripts/update_plugin.py'
    selected['scripts/unittest_evidence.py'] = 'authoring/scripts/unittest_evidence.py'
    selected['hooks/hooks.json'] = 'distribution/hooks.json'
    selected['hooks/run-hook.sh'] = 'distribution/run-hook.sh'
    # One Stop hook; it loads the acceptance and risk gates from the agent-workflow Skill.
    selected['hooks/completion_guard.py'] = 'authoring/scripts/completion_guard.py'
    # PreToolUse and SubagentStop hold delegated work to its stages; delegate.py lives in the Skill.
    selected['hooks/delegation_hook.py'] = 'authoring/scripts/delegation_hook.py'
    selected['agents/acceptance-author.md'] = 'distribution/agents/acceptance-author.md'
    selected['agents/implementer.md'] = 'distribution/agents/implementer.md'
    selected['README.md'] = 'distribution/README.md'
    files = {}
    staged = index_blobs(sorted(set(selected.values())))
    for target, source in sorted(selected.items()):
        path = ROOT / source
        if (not path.resolve().is_relative_to(ROOT) or
                any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
                    for p in (path, *path.parents) if p != ROOT.parent) or
                any(p.lower().startswith(('.env', '.dev.vars')) or p.lower() in
                    {'auth.json', 'credentials', 'secrets'} for p in Path(source).parts)):
            raise ValueError(f'Unsafe package source: {source}')
        files[target] = source_bytes(path, staged[source])
    for skill in catalog['public_skills']:
        if f'skills/{skill}/SKILL.md' not in files:
            raise ValueError(f'Missing public Skill: {skill}')

    def encoded(value):
        return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

    files['plugin.json'] = encoded(manifest)
    # Claude uses default component directories; declaring hooks again duplicates them.
    files['.claude-plugin/plugin.json'] = encoded(manifest)
    files['build-origin.json'] = encoded(dict(origin, version=manifest['version']))
    # Older Codex CLI hosts consume this overlay; identity has one source above.
    files['.codex-plugin/plugin.json'] = encoded({
        key: manifest[key] for key in ('name', 'version', 'description')
    } | {'skills': './skills/', 'hooks': './hooks/hooks.json'})
    files['package-files.json'] = encoded({
        'files': {name: hashlib.sha256(data).hexdigest() for name, data in sorted(files.items())},
        'limit': 'Content inventory, not a signature or evidence of Agent task success.',
    })
    output.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    return {'package': str(output), 'name': manifest['name'], 'version': manifest['version'],
            'skills': len(catalog['public_skills']), 'files': len(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output)))
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
