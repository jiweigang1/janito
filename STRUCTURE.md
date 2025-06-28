# Project Structure: janito

- pyproject.toml: Project configuration (defines build system, metadata, and scripts; 'janito' CLI entry point)

- janito/providers/anthropic/model_info.py: Model information (MODEL_SPECS) for Anthropic models (Claude v3 family).
- janito/providers/anthropic/provider.py: AnthropicProvider implementation for Claude; registers itself in LLMProviderRegistry.
- janito/drivers/anthropic/driver.py: AnthropicModelDriver dummy - implements interface, plug in real Claude API as needed.

Tool execution & management:
- janito/tools/tools_adapter.py: ToolsAdapterBase (now includes execution logic previously in ToolExecutor)
- janito/tools/adapters/local/adapter.py: LocalToolsAdapter (concrete tool registry, now includes execution implementation)

Other relevant artifacts:
- PROVIDERS.md: Provider documentation; now covers 'anthropic'.
