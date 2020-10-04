import os
from pathlib import Path
import subprocess


DOIT_CONFIG = {'backend': 'sqlite3',
               'default_tasks': ['dist'],
               'verbosity': 2}

os.environ['PYTHONPATH'] = str(Path(__file__).parent)


def task_test():
    """Run all tests"""
    def run(args):
        args = args or []
        subprocess.run(
            ['python', '-m', 'pytest', '-s', '-p', 'no:cacheprovider', *args],
            cwd='test', check=True)

    return {'actions': [run], 'pos_arg': 'args'}


def task_lint():
    """Check linting"""
    def run(args):
        args = args or []
        subprocess.run(
            ['flake8', 'ruly', 'test', 'setup.py', 'dodo.py', *args])
    return {'actions': [run], 'pos_arg': 'args'}


def task_check():
    """Pre-deployment check"""
    return {'actions': [], 'task_dep': ['test', 'lint']}


def task_docs():
    """Build docs"""
    def run(args):
        args = args or []
        subprocess.run(
            ['sphinx-build', 'docs', 'build/docs', *args])
    return {'actions': [run], 'pos_arg': 'args'}
