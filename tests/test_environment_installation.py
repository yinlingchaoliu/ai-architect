"""Exercise installed local packages from outside the checkout without credentials or network."""

import os
from pathlib import Path
import subprocess
import sys


def test_installed_sdk_and_root_demo_import_without_provider_or_tokenizer_setup(tmp_path):
    root = Path(__file__).resolve().parents[1]
    code = """
import importlib.util
import sys
from unittest.mock import patch

with patch('socket.socket.connect', side_effect=AssertionError('network during import')), \\
     patch('openai.OpenAI', side_effect=AssertionError('client during import')), \\
     patch('tiktoken.encoding_for_model', side_effect=AssertionError('tokenizer during import')):
    from lib_graph import build_agent
    from lib_request import OpenAIAssistantClient, count_tokens
    spec = importlib.util.spec_from_file_location('root_demo', sys.argv[1])
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    assert callable(build_agent)
    assert callable(OpenAIAssistantClient)
    assert callable(count_tokens)
    assert callable(demo.search_openai)
"""
    env = {key: value for key, value in os.environ.items()
           if key not in ('OPENAI_API_KEY', 'OPENAI_ADMIN_KEY')}
    result = subprocess.run([sys.executable, '-I', '-c', code, str(root / 'main.py')],
                            cwd=tmp_path, env=env, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
