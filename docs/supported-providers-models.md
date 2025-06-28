# Supported Providers & Models

> 🚀 **Janito is optimized and tested for the default model: `gpt-4.1`.**
> 🧪 Testing and feedback for other models is welcome!


## 🤖 Model Types

Janito is compatible with most OpenAI-compatible chat models, including but not limited to:

- `gpt-4.1` (default)
- Azure-hosted OpenAI models (with correct deployment name)
- Google Gemini models (e.g., `gemini-2.5-flash`)

## 🛠️ How to Select a Model

- Use the `--model` CLI option to specify the model for a session:
  ```
  janito "Prompt here" --model gpt-4.1
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

**Context window:** 200 k tokens  
**Max input:** 100 k tokens  
**Max CoT:** N/A  
**Max response:** 100 k tokens  
**Thinking:** 📖  
**Driver:** OpenAI

## ℹ️ Notes

- Some advanced features (like tool calling) require models that support OpenAI function calling.
- Model availability and pricing depend on your provider and API key.
- For the latest list of supported models, see your provider’s documentation or the [OpenAI models page](https://platform.openai.com/docs/models) and [Google Gemini documentation](https://ai.google.dev/gemini-api/docs/model-versions).
