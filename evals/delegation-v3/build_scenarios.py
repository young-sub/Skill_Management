"""Build delegation-v3/scenarios.json from v2: same prompts, one added hidden check in three scenarios.

The runner rejects `..` in hidden sources, so v2 hidden files are copied byte-for-byte under
`hidden/v2/` and verified by SHA-256. Rerun after changing an addition; `--check` only verifies.
"""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent / 'delegation-v2'
REPO = HERE.parents[1]
PREFIX = 'set "WRANGLER_LOG_PATH=.work\\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 '
ADDITIONS = {
    'rule-all-paths': ('stored-description-limit-after-normalization',
                       'hidden/rule-all-paths/zz-eval-v3-description-normalized.test.ts'),
    'b-sequence-category-branch-copy': ('restore-keeps-category-tree-within-three-levels',
                                        'hidden/b-sequence-category-branch-copy/zz-eval-v3-restore-depth.test.ts'),
    'a-import-offer-sequence': ('legacy-layout-blank-offer-cells-keep-current-offers',
                                'hidden/a-import-offer-sequence/zz-eval-v3-legacy-blank-offers.test.ts'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    suite = json.loads((V2 / 'scenarios.json').read_text(encoding='utf-8'))
    result = copy.deepcopy(suite)
    copies = {}
    for scenario in result['scenarios']:
        for check in scenario['hidden']:
            check['origin'] = 'v2'
            files = {}
            for dest, source in check['files'].items():
                files[dest] = f'hidden/v2/{source.removeprefix("hidden/")}'
                copies[files[dest]] = V2 / source
            check['files'] = files
        changed = HERE / 'reference' / f"{scenario['id']}.patch"
        scenario['reference_patch'] = (changed if changed.is_file() else V2 / 'reference' / f"{scenario['id']}.patch") \
            .relative_to(REPO).as_posix()
        if scenario['id'] in ADDITIONS:
            name, source = ADDITIONS[scenario['id']]
            dest = f'tests/{Path(source).name}'
            scenario['hidden'].append({'name': name, 'command': PREFIX + dest, 'expect': 'pass',
                                       'files': {dest: source}, 'origin': 'v3'})
    assert set(ADDITIONS) <= {s['id'] for s in result['scenarios']}
    for v2_scenario, v3_scenario in zip(suite['scenarios'], result['scenarios']):
        assert v2_scenario.get('prompt') == v3_scenario.get('prompt') and v2_scenario.get('prompts') == v3_scenario.get('prompts')
    return result, copies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Verify the written suite and copies without writing')
    args = parser.parse_args()
    result, copies = build()
    text = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.check:
        assert (HERE / 'scenarios.json').read_text(encoding='utf-8') == text, 'scenarios.json is stale'
    else:
        (HERE / 'scenarios.json').write_text(text, encoding='utf-8')
    for target, source in copies.items():
        path = HERE / target
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, path)
        assert digest(path) == digest(source), f'copy differs from v2: {target}'
    print(f'{len(result["scenarios"])} scenarios, {len(copies)} v2 hidden copies verified, {len(ADDITIONS)} additions')


if __name__ == '__main__':
    main()
