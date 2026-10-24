"""Author and verify the offer-list complaint; no commits or installs."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import audit

IDENT = 'a-update-offer-list-complaint'
REPO = audit.TEMP / 'root-offer-complaint'
EVIDENCE = audit.SUITE / 'evidence' / IDENT
SOURCE = REPO / 'src/worker/products.ts'
PREFIX = 'set "WRANGLER_LOG_PATH=.work\\eval-wrangler.log"&& npx vitest run --configLoader runner --cache=false --maxWorkers=2 '
REGRESSION = PREFIX + 'tests/product.test.ts tests/productImportPerformance.test.ts src/client/ProductForm.test.tsx'
HIDDEN = PREFIX + 'tests/zz-eval-offer-list-complaint.test.ts'
FIND = 'statements.push(...input.offers.map((offer, index) => db.prepare'
WRAPPER = '  const prepared = await prepareProductUpdate(db, id, raw, actorEmail);'
CLAMP_WRAPPER = ('  const input = updateProductSchema.parse(raw);\n'
                 '  const prepared = await prepareProductUpdate(db, id, { ...input, offers: input.offers?.slice(0, 3) }, actorEmail);')
CLAMP_BATCH = FIND.replace('input.offers.map', '(freshProduct ? input.offers.slice(0, 3) : input.offers).map')
EVIDENCE = EVIDENCE / 'final'
EVIDENCE.mkdir(parents=True, exist_ok=True)
resume = '--resume-after-start' in sys.argv
results = json.loads((EVIDENCE / 'results.json').read_text(encoding='utf-8')) if resume else []


def run(stage, command, expected):
    attempts = []
    for attempt in range(2):
        started = time.monotonic()
        result = subprocess.run(command, shell=True, cwd=REPO, capture_output=True, timeout=180)
        log = EVIDENCE / f'{stage}{"-retry" if attempt else ""}.log'
        log.write_bytes(result.stdout + result.stderr)
        lines = log.read_text(encoding='utf-8', errors='replace').splitlines()
        assertions = [{'line': i, 'text': line} for i, line in enumerate(lines, 1)
                      if 'AssertionError:' in line or ' FAIL ' in line]
        attempts.append({'exit': result.returncode, 'seconds': round(time.monotonic() - started, 3),
                         'log': log.relative_to(audit.SUITE).as_posix(), 'assertions': assertions})
        if result.returncode == 0:
            break
    record = {'stage': stage, 'command': command, 'attempts': attempts}
    results.append(record)
    (EVIDENCE / 'results.json').write_text(json.dumps(results, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(stage, result.returncode, attempts[-1]['seconds'], flush=True)
    assert result.returncode == expected, record
    if expected:
        assert assertions, 'A setup/runtime failure is not a behavioral kill'


def report():
    lines = ['# Offer-list complaint validation', '', f'## `{IDENT}`', '',
        'Feature: delegated-work evaluation assets. Fresh clone `root-offer-complaint` at Labeler '
        '`984e4f646e08b75a8dfc4b9c62913670960c1659`, with the required evaluation dependency junction.', '',
        'The synthetic fault independently caps standalone updates and cached batch updates at three offer rows. '
        'The reference removes both caps; its resulting product source is byte-identical to the pinned original. '
        'No commit or dependency installation was performed.', '',
        f'Hidden command H: `{HIDDEN}`', '', f'Explicit regression command R: `{REGRESSION}`', '',
        '| Stage | Command | Exit codes by attempt | Seconds by attempt |', '| --- | --- | --- | --- |']
    for record in results:
        lines.append('| ' + record['stage'] + ' | ' + ('H' if record['command'] == HIDDEN else 'R') +
                     ' | ' + ', '.join(str(a['exit']) for a in record['attempts']) +
                     ' | ' + ', '.join(str(a['seconds']) for a in record['attempts']) + ' |')
    lines += ['', 'Nonzero commands were repeated once, matching the judging retry rule. Both failures were '
              'assertion failures, rather than runtime/setup failures. The starting regression also fails: '
              'the reported standalone four-tier case is already covered; the sibling cached batch case is not.', '',
              'Failing assertion evidence (the complete outputs and all attempts are in '
              '`evidence/a-update-offer-list-complaint/final/results.json`):', '']
    for record in results:
        attempt = record['attempts'][-1]
        for assertion in attempt['assertions']:
            if 'AssertionError:' in assertion['text']:
                lines.append(f"- {record['stage']}: `{attempt['log']}:{assertion['line']}` — {assertion['text']}")
    lines += ['', 'Both probes match exactly once on the reference tree. Probe 1 restores only the standalone '
              'cap and kills the direct-edit hidden case; probe 2 restores only the cached-batch cap and kills '
              'the spreadsheet hidden case.', '',
              'The first-obvious partial removes the reported standalone cap while leaving the independent '
              'cached batch cap. Its exact fault-relative diff is '
              '`evidence/a-update-offer-list-complaint/final/partial.patch`. Direct hidden cases pass, '
              'the five-tier spreadsheet fresh read returns only three tiers, and the same full explicit '
              'regression command passes. This is the required discriminating control.', '',
              'Earlier shared-clamp prototype logs under `evidence/a-update-offer-list-complaint/` '
              'are superseded; only the `final/` records describe the shipped fault and probes.', '']
    (audit.SUITE / 'VALIDATION-root.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    original = subprocess.run(['git', '-C', str(REPO), 'show', 'HEAD:src/worker/products.ts'],
                              capture_output=True, check=True).stdout.replace(b'\n', b'\r\n')
    SOURCE.write_bytes(original)
    assert original.count(FIND.encode()) == 1
    text = original.decode('utf-8')
    begin = text.index('export async function updateProduct(')
    end = text.index('export async function prepareProductDelete(', begin)
    fault_find = text[begin:end]
    fault_replace = fault_find.replace(WRAPPER, CLAMP_WRAPPER.replace('\n', '\r\n'), 1).replace(FIND, CLAMP_BATCH, 1)
    fault = {'file': 'src/worker/products.ts', 'find': fault_find, 'replace': fault_replace,
             'commit_message': 'test: reproduce fourth saved offer disappearing'}
    audit.replace_once(REPO, fault)
    audit.git(REPO, 'add', '--', fault['file'])
    fault_bytes = SOURCE.read_bytes()
    # Diff the corrected source against the staged synthetic fault, never commit.
    SOURCE.write_bytes(original)
    patch = subprocess.run(['git', '-C', str(REPO), 'diff', '--', fault['file']], capture_output=True, check=True).stdout
    assert patch
    (audit.SUITE / 'reference' / f'{IDENT}.patch').write_bytes(patch)
    probes = [
        {'name': 'standalone-save-drops-fourth-tier', 'file': fault['file'], 'find': WRAPPER,
         'replace': CLAMP_WRAPPER, 'command': REGRESSION},
        {'name': 'cached-batch-save-drops-fourth-tier', 'file': fault['file'], 'find': FIND,
         'replace': CLAMP_BATCH, 'command': REGRESSION},
    ]
    scenario = {
        'id': IDENT, 'area': 'Feedback', 'project': audit.PROJECTS[0].as_posix(),
        'ref': '984e4f646e08b75a8dfc4b9c62913670960c1659', 'links': ['node_modules'], 'budget_seconds': 1800,
        'prompt': '상품 가격 옵션을 네 개 이상 넣어 수정하면 네 번째부터 사라진다는 문의가 있습니다. 직접 수정과 일괄 가져오기를 포함해 상품 옵션을 수정하는 모든 저장에서 입력한 옵션을 전부 입력 순서대로 보존해 주세요. 정확히 10개까지 허용하고 11개는 HTTP 400 `validation_failed`로 거절해야 합니다. 같은 수량이 두 번 나온 옵션도 같은 오류로 거절하며, 거절 시 상품과 옵션 및 버전은 바뀌지 않아야 합니다. 한 개나 세 개만 넣은 수정도 정상 저장되어야 합니다. 옵션을 보내지 않은 설명 수정은 기존 옵션을 그대로 유지합니다. 오래된 버전으로 수정하면 HTTP 409 `product_conflict`로 거절하고 모든 데이터를 유지해야 합니다. 저장 후 다시 열어도 같은 옵션과 순서가 보여야 합니다.',
        'regression': REGRESSION, 'fault': fault, 'probes': probes,
        'hidden': [{'name': 'all-offer-tiers-persist-on-direct-and-batch-edits', 'expect': 'pass', 'command': HIDDEN,
                    'files': {'tests/zz-eval-offer-list-complaint.test.ts':
                              'hidden/a-update-offer-list-complaint/zz-eval-offer-list-complaint.test.ts'}}],
    }
    (audit.SUITE / 'scenarios-root.json').write_text(json.dumps({'scenarios': [scenario]}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    shutil.copyfile(audit.SUITE / next(iter(scenario['hidden'][0]['files'].values())), REPO / 'tests/zz-eval-offer-list-complaint.test.ts')
    if not resume:
        SOURCE.write_bytes(fault_bytes)
        run('a-start-hidden', HIDDEN, 1)
        run('a-start-regression', REGRESSION, 1)
    SOURCE.write_bytes(original)
    run('b-reference-regression', REGRESSION, 0)
    run('b-reference-hidden', HIDDEN, 0)
    for index, probe in enumerate(probes, 1):
        previous = audit.replace_once(REPO, probe)
        try:
            run(f'c-probe{index}-hidden', HIDDEN, 1)
        finally:
            SOURCE.write_bytes(previous)
    # Repair the reported standalone clamp; leave the independent batch clamp.
    partial = original.replace(FIND.encode(), CLAMP_BATCH.encode(), 1)
    SOURCE.write_bytes(partial)
    partial_patch = subprocess.run(['git', '-C', str(REPO), 'diff', '--', fault['file']], capture_output=True, check=True).stdout
    (EVIDENCE / 'partial.patch').write_bytes(partial_patch)
    try:
        run('d-partial-regression', REGRESSION, 0)
        run('d-partial-hidden', HIDDEN, 1)
    finally:
        SOURCE.write_bytes(original)
    report()
    print('ALL AUTHORING CONTROLS PASS', flush=True)


if __name__ == '__main__':
    main()
