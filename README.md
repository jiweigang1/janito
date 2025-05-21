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

### Advanced and Architectural Features

- ⚡ **Event-driven architecture**: Modular, decoupled system using a custom EventBus for extensibility and integration.
- 🧑‍💻 **Tool registry & dynamic tool execution**: Register new tools easily, execute them by name or call from automation pipelines.
- 🤖 **LLM Agent automation**: Supports agent-like workflows with the ability to chain tools or make decisions during LLM conversations.
- 🏗️ **Extensible provider management**: Add, configure, or switch between LLM providers and their models on the fly.
- 🧰 **Rich tool ecosystem**: Includes file operations, local/remote script and command execution, text processing, and internet access (fetching URLs), all reusable by LLM or user.
- 📝 **Comprehensive event & history reporting**: Detailed logs of prompts, events, tool usage, and responses for traceability and audit.
- 🖥️ **Enhanced terminal UI**: Colorful, informative real-time outputs and logs to improve productivity and insight during LLM usage.

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
  janito --set-api-key API_KEY [-p PROVIDER]
  ```

- **Set the Default Provider**
  ```bash
  janito --set default_provider=provider_name
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

## 🌟 CLI Options Reference

### Core CLI Options
| Option                  | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `--version`            | Show program version                                                        |
| `--list-tools`         | List all registered tools                                                   |
| `--list-providers`     | List all supported LLM providers                                            |
| `-l`, `--list-models`  | List models for current/selected provider                                   |
| `--set-api-key`        | Set API key for the current or selected provider (`API_KEY`). Use `-p PROVIDER` to set for a specific provider. |
| `--set default_provider=provider_name` | Set the current LLM provider (e.g., janito --set default_provider=provider_name)                                                |
| `--set PROVIDER.model=MODEL` or `--set model=MODEL` | Set default model for the current/selected provider. |
| `-s`, `--system`       | Set a system prompt                                                         |
| `-r`, `--role`         | Set the role for the agent (overrides config)                                |
| `-p`, `--provider`     | Select LLM provider (overrides config)                                      |
| `-m`, `--model`        | Select model for the provider                                               |
| `-v`, `--verbose`      | Print extra information before answering                                    |
| `-R`, `--raw`          | Print raw JSON response from API                                            |
| `-e`, `--event-log`    | Log events to console as they occur                                         |
| `[user_prompt]...`     | Prompt to submit (if no other command is used)                              |

### 🧩 Extended Chat Mode Commands
Once inside the interactive chat mode, you can use these slash commands:

#### 📲 Basic Interaction
| Command           | Description                                  |
|-------------------|----------------------------------------------|
| `/exit` or `exit` | Exit chat mode                               |
| `/help`           | Show available commands                      |
| `/multi`          | Activate multiline input mode                |
| `/clear`          | Clear the terminal screen                    |
| `/history`        | Show input history                           |
| `/view`           | Print current conversation history           |
| `/track`          | Show tool usage history                      |

#### 💬 Conversation Management
| Command             | Description                                  |
|---------------------|----------------------------------------------|
| `/restart` or `/start` | Start a new conversation (reset context)   |
| `/prompt`           | Show the current system prompt               |
| `/role <description>` | Change the system role                     |
| `/lang [code]`      | Change interface language (e.g., `/lang en`) |

#### 🛠️ Tool & Provider Interaction
| Command              | Description                                  |
|----------------------|----------------------------------------------|
| `/tools`             | List available tools                         |
| `/termweb-status`    | Show status of termweb server                |
| `/termweb-logs`      | Show last lines of termweb logs              |
| `/livelogs`          | Show live updates from server log file       |
| `/edit <filename>`   | Open file in browser-based editor            |

#### 📊 Output Control
| Command             | Description                                  |
|---------------------|----------------------------------------------|
| `/verbose`          | Show current verbose mode status             |
| `/verbose [on|off]` | Set verbose mode                             |

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

For more information, see the documentation in the `docs/` directory or run `janito --help`.