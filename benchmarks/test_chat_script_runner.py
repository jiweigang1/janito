"""Regression tests for the *ChatScriptRunner* utility."""
from janito.cli.chat_mode.script_runner import ChatScriptRunner


def test_script_runner_stubbed():
    inputs = ["Hello there!", "/exit"]
    runner = ChatScriptRunner(inputs)
    transcript = runner.run()

    # Basic sanity checks
    assert "Hello there!" in transcript

