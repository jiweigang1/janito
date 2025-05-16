import os
import tempfile
import json
import pytest
from janito.llm_auth_manager import LLMAuthManager

def test_set_and_get_credentials():
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_path = os.path.join(tmpdir, 'auth.json')
        manager = LLMAuthManager(auth_file=auth_path)
        manager.set_credentials('openai', 'key1')
        assert manager.get_credentials('openai') == 'key1'

def test_remove_credentials():
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_path = os.path.join(tmpdir, 'auth.json')
        manager = LLMAuthManager(auth_file=auth_path)
        manager.set_credentials('openai', 'key2')
        manager.remove_credentials('openai')
        assert manager.get_credentials('openai') is None

def test_set_credentials_unknown_provider():
    from janito.llm_auth_manager import LLMAuthManager
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_path = os.path.join(tmpdir, 'auth.json')
        manager = LLMAuthManager(auth_file=auth_path)
        with pytest.raises(ValueError) as excinfo:
            manager.set_credentials('unknown_provider', 'some_key')
        assert 'Unknown provider' in str(excinfo.value)

def test_persistence():
    with tempfile.TemporaryDirectory() as tmpdir:
        auth_path = os.path.join(tmpdir, 'auth.json')
        manager = LLMAuthManager(auth_file=auth_path)
        manager.set_credentials('openai', 'key3')
        # Create a new manager to check loading from disk
        manager2 = LLMAuthManager(auth_file=auth_path)
        assert manager2.get_credentials('openai') == 'key3'
