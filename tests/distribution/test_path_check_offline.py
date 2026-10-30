"""Offline path-check assets: the write-path inventory and verdict scoring, without any model."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / 'evals/path-check-offline/tools'
sys.dont_write_bytecode = True
_spec = importlib.util.spec_from_file_location('path_inventory', TOOLS / 'inventory.py')
inventory = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(inventory)

SCHEMA = 'import { z } from "zod";\nexport const itemSchema = z.object({\n  noteText: z.string().max(500),\n});\n'
SAVE = '''import { itemSchema } from "../shared/schema";
async function prepareInsert(db, input) {
  return db.prepare(`INSERT INTO items (id, note_text) VALUES (?, ?)`).bind(input.id, input.noteText);
}
export async function createItem(db, raw) {
  return prepareInsert(db, itemSchema.parse(raw));
}
export async function copyItem(db, current) {
  return prepareInsert(db, { id: "copy", noteText: current.noteText });
}
export async function purgeItems(db) {
  return db.prepare(`DELETE FROM items WHERE id = ?`).bind("x");
}
'''


def git(repo, *args):
    subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.repo = Path(self.temp.name)
        (self.repo / 'src/shared').mkdir(parents=True)
        (self.repo / 'src/worker').mkdir(parents=True)
        (self.repo / 'src/shared/schema.ts').write_text(SCHEMA, encoding='utf-8')
        (self.repo / 'src/worker/items.ts').write_text(SAVE, encoding='utf-8')
        git(self.repo, 'init', '-q')
        git(self.repo, 'add', '.')
        git(self.repo, '-c', 'user.name=t', '-c', 'user.email=t@invalid', 'commit', '-q', '-m', 'base')

    def tearDown(self):
        self.temp.cleanup()

    def test_schema_only_change_reports_the_path_that_skips_the_schema(self):
        (self.repo / 'src/shared/schema.ts').write_text(SCHEMA.replace('500', '300'), encoding='utf-8')
        result = inventory.inventory(self.repo)
        self.assertTrue(result['applicable'])
        paths = [[k.split(' ')[-1] for k in path] for c in result['candidates'] for path in c['paths']]
        self.assertIn(['prepareInsert', 'copyItem'], paths)
        # The schema-parsing caller is covered; the delete writes no changed column.
        self.assertFalse(any('createItem' in path or 'purgeItems' in path for path in paths))
        self.assertIn('copyItem', inventory.render(result))

    def test_a_guard_at_the_writer_covers_every_caller(self):
        guarded = SAVE.replace('async function prepareInsert(db, input) {',
                               'async function prepareInsert(db, input) {\n  input = itemSchema.parse(input);')
        (self.repo / 'src/worker/items.ts').write_text(guarded, encoding='utf-8')
        (self.repo / 'src/shared/schema.ts').write_text(SCHEMA.replace('500', '300'), encoding='utf-8')
        result = inventory.inventory(self.repo)
        self.assertEqual(result['candidates'], [])
        self.assertIn('후보 없음', inventory.render(result))

    def test_changes_without_a_matching_sql_column_are_not_applicable(self):
        (self.repo / 'src/shared/schema.ts').write_text(SCHEMA + 'export const LABEL = "x";\n', encoding='utf-8')
        self.assertFalse(inventory.inventory(self.repo)['applicable'])

    def test_written_columns_reads_insert_lists_and_update_assignments(self):
        self.assertEqual(inventory.written_columns('INSERT INTO t (a, b_c) VALUES (?, ?)'), {'a', 'b_c'})
        self.assertEqual(inventory.written_columns('UPDATE t SET a = ?, b = b + 1 WHERE id = ?'), {'a', 'b'})
        self.assertEqual(inventory.written_columns('DELETE FROM t WHERE id = ?'), set())


class VerdictTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('path_run', TOOLS / 'run.py')
        cls.tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.tool)

    def test_last_json_verdict_line_wins_and_prose_is_ignored(self):
        text = 'notes {"verdict": "complete"} inline\n{"verdict": "complete", "violations": []}\n' \
               '```\n{"verdict": "incomplete", "violations": [{"path": "copy"}]}\n```'
        self.assertEqual(self.tool.verdict_from(text)['verdict'], 'incomplete')
        self.assertIsNone(self.tool.verdict_from('done, all good'))

    def test_score_applies_the_pre_registered_thresholds(self):
        def cell(item, variant, verdict, **extra):
            return {'item': item, 'variant': variant, 'verifier': 'v', 'valid': True, 'errors': [],
                    'verdict': {'verdict': verdict} if verdict else None, 'session': {'wall_seconds': 1}, **extra}
        partials = [cell(f'p{i}', 'partial', 'incomplete') for i in range(3)] + [cell('p3', 'partial', None)]
        references = [cell('r0', 'reference', 'incomplete'), cell('r1', 'reference', 'complete')]
        result = self.tool.score(partials + references, 'v')
        self.assertEqual((result['detected'], result['needed'], result['false_alarms']), (3, 3, 1))
        self.assertTrue(result['passes'])
        result = self.tool.score(partials + references + [cell('r2', 'reference', 'incomplete')], 'v')
        self.assertFalse(result['passes'])
        contaminated = self.tool.score(partials + [cell('p4', 'partial', 'incomplete', contamination=['zz-eval'])], 'v')
        self.assertEqual((contaminated['valid_partials'], contaminated['contaminated']), (4, ['p4']))


if __name__ == '__main__':
    unittest.main()
