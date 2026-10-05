"""Repository entrypoint for the canonical read-only result viewer."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'authoring/scripts/verification_results.py'), run_name='__main__')
