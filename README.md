# Janito

Janito is a command-line interface (CLI) tool for managing and interacting with Large Language Model (LLM) providers. It enables you to configure API keys, select providers and models, and submit prompts to various LLMs from your terminal. Janito is designed for extensibility, supporting multiple providers and a wide range of tools for automation and productivity.

## Features

- 🔑 Manage API keys and provider configurations
- 🤖 Interact with multiple LLM providers (OpenAI, Google, Mistral, , and more)
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

Janito is a Python package. Since this is a development version, install it directly from GitHub:

```bash
pip install git+https://github.com/janito-dev/janito.git
```

## Usage

After installation, use the `janito` command in your terminal.

### Basic Commands

- **Set API Key for a Provider (requires -p PROVIDER)**
  ```bash
  janito --set-api-key API_KEY -p PROVIDER
  ```
  > **Note:** The `-p PROVIDER` argument is required when setting an API key. For example:
  > ```bash
  > janito --set-api-key sk-xxxxxxx -p openai
  > ```

- **Set the Provider**
  ```bash
  janito --set provider=provider_name
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
  janito -p PROVIDER --list-models
  ```

- **Submit a Prompt**
  ```bash
  janito "What is the capital of France?"
  ```

- **Start Interactive Chat Shell**
  ```bash
  janito
  ```

### Advanced Options

- **Enable Inline Web File Viewer for Clickable Links**
  
  By default, Janito can open referenced files in a browser-based viewer when you click on file links in supported terminals. To enable this feature for your session, use the `-w` or `--web` flag:
  
  ```bash
  janito -w
  ```
  This starts the lightweight web file viewer (termweb) in the background, allowing you to inspect files referenced in responses directly in your browser. Combine with interactive mode or prompts as needed.
  
  > **Tip:** Use with the interactive shell for the best experience with clickable file links.


- **Enable Execution Tools (Code/Shell Execution)**
  
  By default, tools that can execute code or shell commands are **disabled** for safety. To enable these tools (such as code execution, shell commands, etc.), use the `--exec` or `-x` flag:
  
  ```bash
  janito -x "Run this code: print('Hello, world!')"
  ```
  > **Warning:** Enabling execution tools allows running arbitrary code or shell commands. Only use `--exec` if you trust your prompt and environment.

- **Set a System Prompt**
  ```bash
  janito -s path/to/system_prompt.txt "Your prompt here"
  ```

- **Select Model and Provider Temporarily**
  ```bash
  janito -p openai -m gpt-3.5-turbo "Your prompt here"
  ```

- **Set Provider-Specific Config (for the selected provider)**
  ```bash
  # syntax: janito --set PROVIDER.KEY=VALUE
  # example: set the default model for openai provider
  janito --set openai.model=gpt-4o

  ```
  > **Note:** Use `--set PROVIDER.key=value` for provider-specific settings (e.g., `openai.max_tokens`, `openai.base_url`).

- **Enable Event Logging**
  ```bash
  janito -e "Your prompt here"
  ```

## 🌟 CLI Options Reference

### Core CLI Options
| Option                  | Description                                                                 |
|------------------------|-----------------------------------------------------------------------------|
| `-w`, `--web`          | Enable the builtin lightweight web file viewer for clickable file links (termweb). |

|------------------------|-----------------------------------------------------------------------------|
| `--version`            | Show program version                                                        |
| `--list-tools`         | List all registered tools                                                   |
| `--list-providers`     | List all supported LLM providers                                            |
| `-l`, `--list-models`  | List models for current/selected provider                                   |
| `--set-api-key`        | Set API key for a provider. **Requires** `-p PROVIDER` to specify the provider. |
| `--set provider=name` | Set the current LLM provider (e.g., `janito --set provider=openai`)                                                |
| `--set PROVIDER.model=MODEL` or `--set model=MODEL` | Set the default model for the current/selected provider, or globally. (e.g., `janito --set openai.model=gpt-3.5-turbo`) |
| `-s`, `--system`       | Set a system prompt (e.g., `janito -s path/to/system_prompt.txt "Your prompt here"`) |
| `-r`, `--role`         | Set the role for the agent (overrides config) (e.g., `janito -r "assistant" "Your prompt here"`) |
| `-p`, `--provider`     | Select LLM provider (overrides config) (e.g., `janito -p openai "Your prompt here"`) |
| `-m`, `--model`        | Select model for the provider (e.g., `janito -m gpt-3.5-turbo "Your prompt here"`) |
| `-v`, `--verbose`      | Print extra information before answering                                    |
| `-R`, `--raw`          | Print raw JSON response from API                                            |
| `-e`, `--event-log`    | Log events to console as they occur                                         |
| `["user_prompt"]...`     | Prompt to submit (if no other command is used) (e.g., `janito "What is the capital of France?"`) |

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
- DeepSeek

## Contributing

Contributions are welcome! Please see the `CONTRIBUTING.md` (if available) or open an issue to get started.

## License

This project is licensed under the terms of the MIT license.

For more information, see the documentation in the `docs/` directory or run `janito --help`.

---

## 📖 Detailed Documentation

Full and up-to-date documentation is available at: https://janito-dev.github.io/janito/

---

## FAQ: Setting API Keys

To set an API key for a provider, you **must** specify both the API key and the provider name:

```bash
janito --set-api-key YOUR_API_KEY -p PROVIDER_NAME
```

Replace `YOUR_API_KEY` with your actual key and `PROVIDER_NAME` with the provider (e.g., `openai`, `google`, etc.).

If you omit the `-p PROVIDER_NAME` argument, Janito will show an error and not set the key.