import pytest
from janito.drivers.azure_openai.driver import AzureOpenAIModelDriver
from janito.llm_provider import LLMProvider

# Dummy provider for test purposes
class DummyProvider(LLMProvider):
    PROVIDER_NAME = 'azure_openai'
    MODEL_SPECS = {
        'azure-model': {'driver': 'AzureOpenAIModelDriver'}
    }
    def __init__(self, api_key='testkey'):  # pragma: allowlist secret
        self._api_key = api_key
        self._tool_registry = None
    @property
    def driver(self):
        return self.get_driver_for_model(config={"model_name": "azure-model"})

def test_missing_required_config():
    provider = DummyProvider()
    with pytest.raises(ValueError) as exc:
        provider.get_driver_for_model(config={"model_name": "azure-model"})
    assert 'Missing required config' in str(exc.value)
    assert 'azure_endpoint' in str(exc.value)

def test_present_required_config():
    provider = DummyProvider()
    driver = provider.get_driver_for_model(config={"model_name": "azure-model", 'azure_endpoint': 'http://example'})
    assert isinstance(driver, AzureOpenAIModelDriver)
