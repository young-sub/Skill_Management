"""Repository entrypoint for project workflow obligations."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[1] / 'authoring/scripts/project_workflow.py'), run_name='__main__')
