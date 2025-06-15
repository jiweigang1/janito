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
| `-r ROLE`, `--role ROLE` | Set the role for the agent |
| `-p PROVIDER`, `--provider PROVIDER` | Select the provider |
| `-m MODEL`, `--model MODEL` | Select the model |
| `-t TEMPERATURE`, `--temperature TEMPERATURE` | Set the temperature |
| `-v`, `--verbose` | Print extra information before answering |
| `-R`, `--raw` | Print the raw JSON response from the OpenAI API (if applicable) |
| `--no-termweb` | Disable the builtin lightweight web file viewer for terminal links (enabled by default) |
| `--termweb-port TERMWEB_PORT` | Port for the termweb server (default: 8088) |
| `-e`, `--event-log` | Enable event logging to the system bus |
| `--event-debug` | Print debug info on event subscribe/submit methods |

## 👨‍💻 Usage Example

```sh
janito -p openai -m gpt-3.5-turbo "Your prompt here"
janito --list-tools
janito "Prompt" --system "You are a helpful assistant." --no-termweb
```

_This page is generated from the output of `janito --help`._
