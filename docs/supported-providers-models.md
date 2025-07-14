# Supported Providers & Models

> 🚀 **Janito is optimized and tested for the default model: `gpt-4.1`.**
> 🧪 Testing and feedback for other models is welcome!


## 🤖 Model Types

Janito is compatible with most OpenAI-compatible chat models, including but not limited to:

- OpenAI models like `gpt-4.1` (default)
- Azure-hosted OpenAI models (with correct deployment name)
- Google Gemini models (e.g., `gemini-2.5-flash`)
- Anthropic Claude models
- Moonshot AI models (e.g., `kimi-k2-0711-preview`)

## 🛠️ How to Select a Model

- Use the `--model` CLI option to specify the model for a session:
  ```
  janito "Prompt here" --model gpt-4.1 --provider openai
  ```
- Configure your API key and endpoint in the configuration file or via CLI options.


## 📋 Supported Models Table

| Model           | Status    | Context     | Max Input  | Max CoT | Max Response | Thinking | Provider | Reference |
|-----------------|-----------|-------------|------------|---------|--------------|----------|----------|-----------|
| gpt-3.5-turbo   | Supported | 16385       | 12289      | N/A     | 4096         |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4.1         | Supported | 1047576     | 1014808    | N/A     | 32768        |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4.1-mini    | Supported | 1047576     | 1014808    | N/A     | 32768        |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4.1-nano    | Supported | 1047576     | 1014808    | N/A     | 32768        |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4-turbo     | Supported | 128000      | N/A        | N/A     | N/A          |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4o          | Supported | 128000      | 123904     | N/A     | 4096         |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gpt-4o-mini     | Supported | 128000      | 111616     | N/A     | 16384        |          | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| o3-mini         | Supported | 200000      | 100000     | N/A     | 100000       | 📖       | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| o3              | Supported | 200000      | 100000     | N/A     | 100000       | 📖       | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| o4-mini         | Supported | 200000      | 100000     | N/A     | 100000       | 📖       | OpenAI   | [source](../janito/providers/openai/model_info.py) |
| gemini-2.5-flash | Supported | N/A         | N/A        | 24576   | 8192         | ✔️        | Google   | [source](../janito/providers/google/model_info.py) |
| gemini-2.5-pro   | Supported | N/A         | N/A        | 196608  | 65536        | ✔️        | Google   | [source](../janito/providers/google/model_info.py) |
| claude-opus-4-20250514 | Supported | N/A         | N/A        | N/A     | 32000        |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| claude-sonnet-4-20250514 | Supported | N/A         | N/A        | N/A     | 64000        |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| claude-3-7-sonnet-20250219 | Supported | N/A         | N/A        | N/A     | 64000        |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| claude-3-5-haiku-20241022 | Supported | N/A         | N/A        | N/A     | 8192         |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| claude-3-5-sonnet-20241022 | Supported | N/A         | N/A        | N/A     | 8192         |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| claude-3-haiku-20240307 | Supported | N/A         | N/A        | N/A     | 4096         |          | Anthropic| [source](../janito/providers/anthropic/model_info.py) |
| kimi-k2-0711-preview    | Supported | 128000      | 127000     | N/A     | 8000         |          | MoonshotAI| [source](../janito/providers/moonshotai/model_info.py) |
| kimi-k1-8k              | Supported | 8000        | 6000       | N/A     | 2000         |          | MoonshotAI| [source](../janito/providers/moonshotai/model_info.py) |
| kimi-k1-32k             | Supported | 32000       | 28000      | N/A     | 4000         |          | MoonshotAI| [source](../janito/providers/moonshotai/model_info.py) |
| kimi-k1-128k            | Supported | 128000      | 120000     | N/A     | 8000         |          | MoonshotAI| [source](../janito/providers/moonshotai/model_info.py) |

**Context window:** 200 k tokens  
**Max input:** 100 k tokens  
**Max CoT:** N/A  
**Max response:** 100 k tokens  
**Thinking:** 📖  
**Driver:** OpenAI

## ℹ️ Notes

- Some advanced features (like tool calling) require models that support OpenAI function calling.
- Model availability and pricing depend on your provider and API key.
- For the latest list of supported models, see your provider’s documentation or the [OpenAI models page](https://platform.openai.com/docs/models), [Google Gemini documentation](https://ai.google.dev/gemini-api/docs/model-versions), and [Anthropic Claude documentation](https://www.anthropic.com/docs/api/reference).

---

# Provider Details

### Provider Parameters (`config`)

All LLM providers support an optional `config` dictionary for provider-specific settings. You can pass this dictionary to the provider constructor:

```python
provider = OpenAIProvider(model_name="gpt-4o", config={"base_url": "https://api.example.com/v1"})
```

- For `openai` and compatible providers, you can set `base_url` to use a custom endpoint.
- For Azure, additional options like `endpoint` and `api_version` may be supported as keys within `config`.

---

### anthropic

**Description:** Anthropic Claude v3 (Opus, Sonnet, Haiku), via official Anthropic API.

**Models:**
- claude-3-opus-20240229: Most advanced, very high context and reasoning.
- claude-3-sonnet-20240229: Fast, large-context, good for chat.
- claude-3-haiku-20240307: Fastest, cheap, smaller context.

**Auth:**
- Expects official Claude API key via credential system only (environment variables are not supported).

**Usage:**
- Use provider name `anthropic` in CLI/config. Model selection applies as above.

---

### azure_openai

**Description:** Azure-hosted OpenAI models (API-compatible, may require endpoint and version)

**Models:**
- azure-gpt-35-turbo: GPT-3.5 family turbo, hosted via Azure.
- azure-gpt-4: GPT-4 model, hosted via Azure.

**Auth:**
- Expects API key and Azure endpoint via credential manager only (environment variables are not supported).

**Usage:**
- Use provider name `azure_openai` in CLI/config. Model selection as shown above.

---

### google

**Description:** Google Gemini models via OpenAI-compatible API endpoint.

**Models:**
- gemini-2.5-flash: Flash model, suitable for chat and general use.
- gemini-2.5-pro: Pro model, larger context and higher throughput.
- gemini-2.5-flash-lite-preview-06-17: Flash Lite preview model.

**Auth:**
- Uses API key via credential manager.

**Usage:**
- Use provider name `google` in CLI/config. Model selection as shown above.

---

### moonshotai

**Description:** Moonshot AI models via OpenAI-compatible API endpoint.

**Models:**
- kimi-k2-0711-preview: Advanced reasoning model with 128k context window
- kimi-k1-8k: Standard model with 8k context window
- kimi-k1-32k: Standard model with 32k context window  
- kimi-k1-128k: Standard model with 128k context window

**Auth:**
- Uses API key via credential manager.

**Usage:**
- Use provider name `moonshotai` in CLI/config. Model selection as shown above.

---
