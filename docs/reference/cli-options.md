# 🏁 Janito CLI Options

This page documents all command-line options for Janito, as shown by `janito --help`. These options temporarily override configuration for a single session and do not persist changes to config files.

## 💡 Overview

These options are useful for one-off runs, scripting, or experimentation. They take precedence over config files for the current invocation only.

## ⚙️ Options

| Option | Description |
|--------|-------------|
| `user_prompt` | Prompt to submit (positional argument) |
| `-h`, `--help` | Show this help message and exit |
| `--verbose-api` | Print API calls and responses of LLM driver APIs for debugging/tracing. |
| `--verbose-tools` | Print info messages for tool execution in tools adapter. |
| `--verbose-agent` | Print info messages for agent event and message part handling. |
| `-z`, `--zero` | IDE zero mode: disables system prompt & all tools for raw LLM interaction |
| `-u`, `--unrestricted-paths` | Disable path security: allow tool arguments to use any file/directory path (DANGEROUS). See [Security](../security.md) for details. |
| `-r`, `--read` | Enable tools that require read permissions (default: off) |
| `-w`, `--write` | Enable tools that require write permissions (default: off) |
| `-x`, `--exec` | Enable execution/run tools (allows running code or shell tools from the CLI). (default: off) |
| `--unset KEY` | Unset (remove) a config key |
| `--version` | Show program's version number and exit |
| `--list-tools` | List all registered tools |
| `--show-config` | Show the current config |
| `--list-providers` | List supported LLM providers |
| `-l`, `--list-models` | List all supported models |
| `--set-api-key API_KEY` | Set API key for the provider (requires -p PROVIDER) |
| `--set [PROVIDER_NAME.]KEY=VALUE` | Set a config key |
| `-s SYSTEM_PROMPT`, `--system SYSTEM_PROMPT` | Set a system prompt |
| `-S`, `--show-system` | Show the resolved system prompt for the main agent |

| `-p PROVIDER`, `--provider PROVIDER` | Select the provider |
| `-m MODEL`, `--model MODEL` | Select the model |
| `-t TEMPERATURE`, `--temperature TEMPERATURE` | Set the temperature |
| `-v`, `--verbose` | Print extra information before answering |
| `-R`, `--raw` | Print the raw JSON response from the OpenAI API (if applicable) |
| `--web` | Enable the builtin lightweight web file viewer for terminal links (disabled by default) |

| `--effort {low, medium, high, none}` | Set the reasoning effort for models that support it (low, medium, high, none) |
| `-e`, `--event-log` | Enable event logging to the system bus |
| `--event-debug` | Print debug info on event subscribe/submit methods |

## 👨‍💻 Usage Example

```sh
janito -p openai -m gpt-3.5-turbo "Your prompt here"
janito -p google -m gemini-2.5-flash "Your prompt here"
janito --list-tools
janito --web  # Enable clickable file links via web viewer
janito -u -x --read --write "Run a tool with unrestricted paths (DANGEROUS)"
```

### ⚠️ Enabling Execution Tools

By default, tools that can execute code or shell commands are **disabled** for safety. To enable these tools (such as code execution, shell commands, etc.), use the `--exec` or `-x` flag:

```sh
janito -x "Run this code: print('Hello, world!')"
```
> **Warning:** Enabling execution tools allows running arbitrary code or shell commands. Only use `--exec` if you trust your prompt and environment.

### ⚠️ Disabling Path Security

By default, all file and directory arguments to tools are restricted to the working directory (see `--workdir`). To disable this security and allow any path (including system files), use the `-u` or `--unrestricted-paths` flag:

```sh
janito -u "Do something with C:/Windows/System32/hosts"
```
> **Warning:** Disabling path security is extremely dangerous. Only use `--unrestricted-paths` if you trust your prompt, tools, and environment.

_This page is generated from the output of `janito --help`._

## 🧠 About `--effort`

The `--effort` option allows you to set the reasoning effort for models that support it. This can influence how much computational or logical effort the model applies to your prompt. The available values are:

- `low`: Minimal reasoning effort (faster, less detailed)
- `medium`: Moderate reasoning effort (default for some models)
- `high`: Maximum reasoning effort (slower, more detailed)
- `none`: Disables special reasoning effort (model default)

> **Note:** Not all models or providers support this option. If unsupported, the option may be ignored.
