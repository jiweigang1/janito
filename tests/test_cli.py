import subprocess
import sys
import os
import pytest
from unittest.mock import patch, MagicMock

def run_cli(args):
    CLI_PATH = os.path.join(os.path.dirname(__file__), '..', 'janito', 'cli.py')
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run([sys.executable, CLI_PATH] + args, capture_output=True, text=True, env=env)
    return result

def test_list_providers():
    result = run_cli(['--list-providers'])
    assert result.returncode == 0
    assert "openai" in result.stdout

def test_version():
    result = run_cli(['--version'])
    assert result.returncode == 0
    assert "0.1.0" in result.stdout
