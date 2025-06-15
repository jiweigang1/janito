# Supported Providers & Models

> 🚀 **Janito is optimized and tested for the default model: `gpt-4.1`.**
> 🧪 Testing and feedback for other models is welcome!


## 🤖 Model Types

Janito is compatible with most OpenAI-compatible chat models, including but not limited to:

- `gpt-4.1` (default)
- Azure-hosted OpenAI models (with correct deployment name)

## 🛠️ How to Select a Model

- Use the `--model` CLI option to specify the model for a session:
  ```
  janito "Prompt here" --model gpt-4.1
  ```
- Configure your API key and endpoint in the configuration file or via CLI options.

## ℹ️ Notes

- Some advanced features (like tool calling) require models that support OpenAI function calling.
- Model availability and pricing depend on your provider and API key.
- For the latest list of supported models, see your provider’s documentation or the [OpenAI models page](https://platform.openai.com/docs/models).
