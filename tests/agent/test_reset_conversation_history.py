import pytest
from janito.agent.agent import Agent

class DummyDriver:
    def __init__(self):
        self._history = ['user: hi', 'agent: hello']
        self.history_cleared = False
    def clear_history(self):
        self.history_cleared = True
        self._history.clear()
    def get_history(self):
        return self._history

@pytest.fixture
def agent():
    driver = DummyDriver()
    return Agent(driver)

def test_agent_resets_conversation_history(agent):
    # Simulate old history
    assert agent.driver.get_history() == ['user: hi', 'agent: hello']
    agent.reset_conversation_history()
    assert agent.driver.get_history() == []
    assert agent.driver.history_cleared
