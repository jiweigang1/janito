# Janito

Janito is a command-line interface (CLI) tool for managing and interacting with Large Language Model (LLM) providers. It enables you to configure API keys, select providers and models, and submit prompts to various LLMs from your terminal. Janito is designed for extensibility, supporting multiple providers and a wide range of tools for automation and productivity.

## Features

- 🔑 Manage API keys and provider configurations
- 🤖 Interact with multiple LLM providers (OpenAI, Google, Mistral, DashScope, and more)
- 🛠️ List and use a variety of registered tools
- 📝 Submit prompts and receive responses directly from the CLI
- 📋 List available models for each provider
- 🧩 Extensible architecture for adding new providers and tools
- 🎛️ Rich terminal output and event logging

## Installation

Janito is a Python package. Install it using pip:

```bash
pip install janito
```

## Usage

After installation, use the `janito` command in your terminal.

### Basic Commands

- **Set API Key for a Provider**
  ```bash
  janito --set-api-key PROVIDER API_KEY
  ```

- **Set the Default Provider**
  ```bash
  janito --set-provider PROVIDER
  ```

- **List Supported Providers**
  ```bash
  janito --list-providers
  ```

- **List Registered Tools**
  ```bash
  janito --list-tools
  ```

- **List Models for a Provider**
  ```bash
  janito --provider PROVIDER --list-models
  ```

- **Submit a Prompt**
  ```bash
  janito What is the capital of France?
  ```

- **Start Interactive Chat Shell**
  ```bash
  janito
  ```

### Advanced Options

- **Set a System Prompt**
  ```bash
  janito -s path/to/system_prompt.txt "Your prompt here"
  ```
- **Select Model and Provider Temporarily**
  ```bash
  janito -p openai -m gpt-3.5-turbo "Your prompt here"
  ```
- **Set Provider-Specific Config**
  ```bash
  janito --set-config PROVIDER KEY VALUE
  ```
- **Enable Event Logging**
  ```bash
  janito -e "Your prompt here"
  ```

## Extending Janito

Janito is built to be extensible. You can add new LLM providers or tools by implementing new modules in the `janito/providers` or `janito/tools` directories, respectively. See the source code and developer documentation for more details.

## Supported Providers

- OpenAI
- Google Gemini
- Mistral
- DashScope
- (And more via plugins)

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` (if available) or open an issue to get started.

## License

This project is licensed under the terms of the MIT license.

---

For more information, see the documentation in the `docs/` directory or run `janito --help`.
