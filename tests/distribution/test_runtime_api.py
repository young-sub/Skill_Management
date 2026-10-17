"""Statically check runtime calls, including names and argument contracts."""
import ast
import inspect
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2] / 'authoring/scripts'


def boundary_errors(source, modules):
    errors = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name) and node.value.id in modules:
            errors.append('Use a public module function, not a runtime result dict')
        if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
            continue
        alias = node.func.value
        if not isinstance(alias, ast.Name):
            continue
        if alias.id == 'runpy':
            errors.append('Use explicit imports for runtime dependencies')
        if alias.id not in modules:
            continue
        module = modules[alias.id]
        name = node.func.attr
        target = next((n for n in module.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == name), None)
        if name.startswith('_') or target is None:
            errors.append(f'Unknown or private public API: {alias.id}.{name}')
        elif isinstance(target, ast.FunctionDef) and not any(isinstance(a, ast.Starred) for a in node.args) and all(k.arg for k in node.keywords):
            args = target.args
            parameters = []
            positional = args.posonlyargs + args.args
            for index, arg in enumerate(positional):
                default = None if index >= len(positional) - len(args.defaults) else inspect.Parameter.empty
                parameters.append(inspect.Parameter(arg.arg, inspect.Parameter.POSITIONAL_OR_KEYWORD, default=default))
            if args.vararg:
                parameters.append(inspect.Parameter(args.vararg.arg, inspect.Parameter.VAR_POSITIONAL))
            for arg, default in zip(args.kwonlyargs, args.kw_defaults):
                parameters.append(inspect.Parameter(arg.arg, inspect.Parameter.KEYWORD_ONLY,
                    default=None if default is not None else inspect.Parameter.empty))
            if args.kwarg:
                parameters.append(inspect.Parameter(args.kwarg.arg, inspect.Parameter.VAR_KEYWORD))
            try:
                inspect.Signature(parameters).bind(*[None for _ in node.args], **{k.arg: None for k in node.keywords})
            except TypeError as error:
                errors.append(f'{alias.id}.{name}: {error}')
    return errors


class RuntimeApiTests(unittest.TestCase):
    def test_runtime_uses_public_statically_resolvable_calls(self):
        modules = {alias: ast.parse((ROOT / name).read_text(encoding='utf-8')) for alias, name in
            [('viewer', 'verification_results.py'), ('workflow', 'project_workflow.py'), ('reader', 'unittest_evidence.py')]}
        for name in ('project_workflow.py', 'verification_results.py'):
            with self.subTest(name=name):
                self.assertEqual(boundary_errors((ROOT / name).read_text(encoding='utf-8'), modules), [])
        for name in ('workflow_context.py', 'core_harness.py'):
            self.assertEqual(boundary_errors((ROOT / name).read_text(encoding='utf-8'),
                {('workflow_api' if name == 'core_harness.py' else 'runtime'): modules['workflow']}), [])

    def test_workflow_does_not_bypass_the_task_store(self):
        tree = ast.parse((ROOT / 'project_workflow.py').read_text(encoding='utf-8'))
        forbidden = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if (node.func.attr in {'write_text', 'write_bytes', 'dump'} or
                        node.func.attr == 'replace' and isinstance(node.func.value, ast.Name)
                        and node.func.value.id in {'path', 'state_path', 'temporary', 'os'}):
                    forbidden.append((node.lineno, node.func.attr))
        self.assertEqual(forbidden, [], 'Task persistence belongs to TaskStore')

    def test_checker_detects_real_old_boundary_and_bad_argument_but_allows_public_call(self):
        modules = {'viewer': ast.parse('def view_bundle(bundle, *, include_scope=True): pass')}
        for source in ("viewer['_view_bundle'](path)", 'viewer._view_bundle(path)',
                       'viewer.missing(path)', 'viewer.view_bundle(path, made_up=True)', 'viewer.view_bundle()'):
            self.assertTrue(boundary_errors(source, modules), source)
        self.assertEqual(boundary_errors('viewer.view_bundle(path, include_scope=False)', modules), [])
