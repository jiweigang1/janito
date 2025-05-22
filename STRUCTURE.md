# Project Structure: janito

- janito/providers/anthropic/model_info.py: Model information (MODEL_SPECS) for Anthropic models (Claude v3 family).
- janito/providers/anthropic/provider.py: AnthropicProvider implementation for Claude; registers itself in LLMProviderRegistry.
- janito/drivers/anthropic/driver.py: AnthropicModelDriver dummy - implements interface, plug in real Claude API as needed.

Other relevant artifacts:
- PROVIDERS.md: Provider documentation; now covers 'anthropic'.
