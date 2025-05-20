import os
import sys
import json
from janito.provider_config import get_provider_config, set_provider_config, set_provider_model_config, get_provider_model_config
import pytest
import subprocess

def run_cli(args):
    CLI_PATH = os.path.join(os.path.dirname(__file__), '..', 'janito', 'cli.py')
    env = os.environ.copy()
    env['PYTHONPATH'] = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    result = subprocess.run([sys.executable, CLI_PATH] + args, capture_output=True, text=True, env=env)
    return result

def test_set_provider_key_value_explicit(tmp_path, monkeypatch):
    config_path = tmp_path / 'config.json'
    monkeypatch.setenv('JANITO_CONFIG', str(config_path))
    provider = 'openaitest'
    key = 'base_url'
    value = 'https://api.test'
    args = ['--set', f'{provider}.{key}={value}']
    result = run_cli(args)
    assert result.returncode == 0
    assert f"Set config for provider '{provider}': {key} = {value}" in result.stdout
    cfg = get_provider_config(provider)
    assert cfg.get(key) == value

def test_set_provider_key_value_via_cli_provider(tmp_path, monkeypatch):
    config_path = tmp_path / 'config.json'
    monkeypatch.setenv('JANITO_CONFIG', str(config_path))
    provider = 'openaitest'
    key = 'envkey'
    value = 'foo'
    args = ['--provider', provider, '--set', f'{key}={value}']
    result = run_cli(args)
    assert result.returncode == 0
    assert f"Set config for provider '{provider}': {key} = {value}" in result.stdout
    cfg = get_provider_config(provider)
    assert cfg.get(key) == value

def test_set_provider_key_value_no_provider(tmp_path, monkeypatch):
    config_path = tmp_path / 'config.json'
    monkeypatch.setenv('JANITO_CONFIG', str(config_path))
    key = 'xkey'
    value = 'xval'
    result = run_cli(['--set', f'{key}={value}'])
    assert result.returncode == 0
    assert 'Error: No provider specified' in result.stdout

def test_set_provider_model_key_value_explicit(tmp_path, monkeypatch):
    config_path = tmp_path / 'config.json'
    monkeypatch.setenv('JANITO_CONFIG', str(config_path))
    provider = 'openaitest'
    model = 'gpt-test1'
    key = 'max_tokens'
    value = '123'
    args = ['--set', f'{provider}.{model}.{key}={value}']
    result = run_cli(args)
    assert result.returncode == 0
    assert f"Set config for provider '{provider}', model '{model}': {key} = {value}" in result.stdout
    cfg_model = get_provider_model_config(provider, model)
    assert cfg_model.get(key) == value

def test_set_provider_key_value_missing_equals():
    result = run_cli(['--set', 'nonsense'])
    assert result.returncode == 0
    assert 'Error: --set requires argument in the form [PROVIDER_NAME.]KEY=VALUE' in result.stdout
