"""Build the current public Skill cohort as a local plugin, without installing it.

Only tracked public Skill files and the existing capture CLI enter the package.
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
    manifest = json.loads((ROOT / 'distribution/plugin.json').read_text(encoding='utf-8'))
    catalog = json.loads((ROOT / 'distribution/catalog.json').read_text(encoding='utf-8'))
    names = subprocess.run(['git', '-C', str(ROOT), 'ls-files', '-z', '--', 'skills'],
                           check=True, capture_output=True).stdout.decode('utf-8').split('\0')
    selected = {name: name for name in names if name and
                Path(name).parts[1] in catalog['public_skills']}
    selected['scripts/run_check.py'] = 'scripts/run_check.py'
    selected['scripts/unittest_evidence.py'] = 'authoring/scripts/unittest_evidence.py'
    files = {}
    for target, source in sorted(selected.items()):
        path = ROOT / source
        if (not path.resolve().is_relative_to(ROOT) or
                any(p.is_symlink() or (hasattr(p, 'is_junction') and p.is_junction())
                    for p in (path, *path.parents) if p != ROOT.parent) or
                any(p.lower().startswith(('.env', '.dev.vars')) or p.lower() in
                    {'auth.json', 'credentials', 'secrets'} for p in Path(source).parts)):
            raise ValueError(f'Unsafe package source: {source}')
        files[target] = path.read_bytes()
    for skill in catalog['public_skills']:
        if f'skills/{skill}/SKILL.md' not in files:
            raise ValueError(f'Missing public Skill: {skill}')

    def encoded(value):
        return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

    files['plugin.json'] = encoded(manifest)
    # Older Codex CLI hosts consume this overlay; identity has one source above.
    files['.codex-plugin/plugin.json'] = encoded({
        key: manifest[key] for key in ('name', 'version', 'description')
    } | {'skills': './skills/'})
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
