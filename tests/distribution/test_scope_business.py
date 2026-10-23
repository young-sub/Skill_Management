"""Durable scope decisions, human business value and honest review-only cells."""
from copy import deepcopy
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / 'authoring/scripts/project_workflow.py'
ARCHITECTURE = {'flows': [{'owner': 'src/api.py', 'call': 'handler -> price', 'state': 'one price',
                           'data': 'price -> response', 'references': ['src/api.py']}],
                'boundaries': [{'kind': kind, 'analysis': 'Unchanged boundary', 'references': ['src/api.py']}
                               for kind in ('contract', 'dependency', 'failure')], 'findings': []}
DEFERRED = {'goal': 'Free-to-paid conversion from efficient label production', 'status': 'DEFERRED',
            'decided_by': 'user', 'decided_at': '2026-10-23', 'reconsider': 'first post-launch settlement'}


class ScopeBusinessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name, content in {'src/api.py': 'price = 10\n', 'src/cli.py': 'print(10)\n', 'docs/map.md': 'map\n',
                              'docs/req.md': 'price is ten\n', '.gitignore': '.work/\n'}.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        for argv in (['git', 'init', '-q'], ['git', 'add', '.'],
                     ['git', '-c', 'user.name=F', '-c', 'user.email=f@invalid', 'commit', '-qm', 'base']):
            subprocess.run(argv, cwd=self.root, check=True, capture_output=True)
        review_row = {'id': 'owner-review', 'requirement': 'docs/req.md', 'outcome': 'One price owner',
                      'perspectives': ['architecture'], 'areas': ['Domain'], 'kind': 'review'}
        self.project = {'commands': {'check': {'argv': ['python', '-V']}},
            'extensions': {'workflow': {'roots': ['src'], 'features': [
                {'id': 'api', 'partition': 'service', 'sources': ['src/api.py'], 'map': ['docs/map.md'],
                 'criteria': ['docs/req.md'], 'checks': ['check'], 'coverage': [review_row],
                 'scope': {'business:FE': {'status': 'NOT_REQUIRED', 'reason': 'No browser surface', 'decided_by': 'user'}}},
                {'id': 'cli', 'partition': 'operator', 'sources': ['src/cli.py'], 'map': ['docs/map.md'],
                 'criteria': ['docs/req.md'], 'checks': [], 'coverage': [dict(review_row)]}]}}}
        spec = importlib.util.spec_from_file_location('project_workflow', SCRIPT)
        self.runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.runtime)

    def cell(self, result, feature, key):
        perspective, area = key.split(':')
        return next(c for c in result['coverage']['matrix']
                    if (c['feature'], c['perspective'], c['area']) == (feature, perspective, area))

    def review(self, state, feature, analysis):
        basis = next(f['basis'] for f in self.runtime.inspect_project(self.root, self.project, state)['features']
                     if f['id'] == feature)
        return {'feature': feature, 'basis': basis, 'analysis': 'Owner reviewed', 'references': ['src/api.py'],
                'findings': [], 'scope_reviews': {
                    'architecture:Domain': {'status': 'REQUIRED', 'analysis': analysis, 'references': ['src/api.py'],
                                            'coverage': ['owner-review']},
                    'owner-review': {'status': 'PASS', 'analysis': analysis + ' (owner)', 'references': ['src/api.py'],
                                     'architecture': ARCHITECTURE}}}

    def test_durable_project_scope_decision_needs_no_task_review(self):
        result = self.runtime.inspect_project(self.root, self.project, None)
        cell = self.cell(result, 'api', 'business:FE')
        self.assertEqual((cell['status'], cell['origin']), ('NOT_REQUIRED', 'project'))
        self.assertEqual(self.cell(result, 'api', 'business:Domain')['status'], 'UNDECIDED')
        self.assertEqual(self.cell(result, 'cli', 'business:FE')['status'], 'UNDECIDED')
        applies = deepcopy(self.project)
        applies['extensions']['workflow']['features'][0]['scope']['business:Domain'] = {
            'status': 'APPLIES', 'reason': 'Every price change is a domain rule', 'decided_by': 'user'}
        result = self.runtime.inspect_project(self.root, applies, None)
        self.assertEqual(self.cell(result, 'api', 'business:Domain')['status'], 'APPLIES')
        self.assertFalse(any(q['kind'] == 'scope' and q.get('feature') == 'api' and 'business:Domain' in q['cells']
                             for q in self.runtime.open_questions(result)['items']))
        for bad in ({'status': 'REQUIRED', 'reason': 'x', 'decided_by': 'user'},
                    {'status': 'NOT_REQUIRED', 'reason': ' ', 'decided_by': 'user'},
                    {'status': 'NOT_REQUIRED', 'reason': 'x'}):
            project = deepcopy(self.project)
            project['extensions']['workflow']['features'][0]['scope'] = {'business:FE': bad}
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                self.runtime.configuration(project)
        project = deepcopy(self.project)
        project['extensions']['workflow']['features'][0]['scope'] = {'business:Mobile': self.project[
            'extensions']['workflow']['features'][0]['scope']['business:FE']}
        with self.assertRaises(ValueError):
            self.runtime.configuration(project)

    def test_business_value_is_a_human_decision_or_an_explicit_question(self):
        result = self.runtime.inspect_project(self.root, self.project, None)
        self.assertEqual({f['business_value']['status'] for f in result['features']}, {'QUESTION_REQUIRED'})
        questions = self.runtime.open_questions(result)
        business = [q for q in questions['items'] if q['kind'] == 'business_value']
        self.assertEqual(business[0]['features'], ['api', 'cli'])
        self.assertTrue(any(q['kind'] == 'scope' and q['feature'] == 'cli' and 'business:FE' in q['cells']
                            for q in questions['items']))
        project = deepcopy(self.project)
        project['extensions']['workflow']['business_value'] = DEFERRED
        result = self.runtime.inspect_project(self.root, project, None)
        self.assertEqual(result['features'][0]['business_value']['origin'], 'project')
        self.assertFalse([q for q in self.runtime.open_questions(result)['items'] if q['kind'] == 'business_value'])
        report = self.runtime.render_report(result)
        self.assertIn('Business value: DEFERRED (project) goal: Free-to-paid conversion', report)
        self.assertIn('reconsider: first post-launch settlement', report)
        self.assertIn('## Questions for the user', report)
        self.assertIn('not required (project, user): No browser surface', report)
        invalid = [dict(DEFERRED, reconsider=''), dict(DEFERRED, decided_by=''),
                   dict(DEFERRED, status='MEASURED'), dict(DEFERRED, status='PROXY', proxies=['unknown-row'])]
        for value in invalid:
            project['extensions']['workflow']['features'][0]['business_value'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.runtime.configuration(project)
        project['extensions']['workflow']['features'][0]['business_value'] = dict(
            DEFERRED, status='PROXY', proxies=['owner-review'])
        self.runtime.configuration(project)

    def test_review_only_cells_are_not_presented_as_executed_protection(self):
        state = self.runtime.begin(self.root, self.project, 'change', ['api'])
        state = self.runtime.record_review(self.root, self.project, state,
                                           self.review(state, 'api', 'Price is owned by src/api.py only'))
        result = self.runtime.inspect_project(self.root, self.project, state)
        cell = self.cell(result, 'api', 'architecture:Domain')
        self.assertEqual(cell['status'], 'REVIEW_ONLY')
        self.assertIn('no_executable_check_linked', cell['reasons'])
        self.assertNotEqual(result['coverage']['status'], 'COMPLETE')
        pending = [p['id'] for a in result['next_actions'] for p in a.get('pending', [])]
        self.assertNotIn('architecture:Domain', pending)

    def test_copied_judgment_from_another_feature_is_rejected(self):
        state = self.runtime.begin(self.root, self.project, 'change', ['api', 'cli'])
        analysis = 'App dispatch owns the price transition and the memory-only session'
        state = self.runtime.record_review(self.root, self.project, state, self.review(state, 'api', analysis))
        with self.assertRaisesRegex(ValueError, 'copied_review_analysis:cli:architecture:Domain:from:api'):
            self.runtime.record_review(self.root, self.project, state, self.review(state, 'cli', analysis))
        state = self.runtime.record_review(self.root, self.project, state,
                                           self.review(state, 'cli', 'CLI prints the constant without owning state'))
        self.assertIn('cli', state['reviews'])


if __name__ == '__main__':
    unittest.main()
