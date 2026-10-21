"""Repository access to the canonical native unittest evidence reader."""
from pathlib import Path
import runpy

_reader = runpy.run_path(str(Path(__file__).resolve().parents[1] / 'authoring/scripts/unittest_evidence.py'))
git_identity = _reader['git_identity']
assess = _reader['assess']
verification_inputs = _reader['verification_inputs']
