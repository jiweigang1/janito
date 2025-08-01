# Janito CLI

A powerful command-line tool for running LLM-powered workflows with built-in tool execution capabilities.

## Quick Start

### Installation

```bash
pip install janito
```

### First-Time Setup

1. **Get your API key**: Sign up at [Moonshot AI](https://platform.moonshot.cn/) and get your API key
2. **Set your API key**:
   ```bash
   janito --set-api-key YOUR_MOONSHOT_API_KEY -p moonshotai
   ```

### Basic Usage

**MoonshotAI (Recommended - Default Provider)**
```bash
# Using the default provider (moonshotai) and model
janito "Create a Python script that reads a CSV file"

# Using a specific MoonshotAI model
janito -m kimi-k1-8k "Explain quantum computing"
```

**Other Providers**
```bash
# OpenAI
janito -p openai -m gpt-4 "Write a React component"

# Anthropic
janito -p anthropic -m claude-3-5-sonnet-20241022 "Analyze this code"

# Google
janito -p google -m gemini-2.0-flash-exp "Generate unit tests"
```

### Interactive Chat Mode

Start an interactive session:
```bash
janito --chat
```

In chat mode, you can:

- Have multi-turn conversations
- Execute code and commands
- Read and write files
- Use built-in tools

### Available Commands

- `janito --list-providers` - List all supported providers
- `janito --list-models` - List all available models
- `janito --list-tools` - List available tools
- `janito --show-config` - Show current configuration

### Configuration

Set default provider and model:
```bash
janito --set provider=moonshotai
janito --set model=kimi-k1-8k
```

## Providers

### MoonshotAI (Recommended)

- **Models**: kimi-k1-8k, kimi-k1-32k, kimi-k1-128k, kimi-k2-turbo-preview
- **Strengths**: Excellent Chinese/English support, competitive pricing, fast responses
- **Setup**: Get API key from [Moonshot AI Platform](https://platform.moonshot.cn/)

### OpenAI

- **Models**: gpt-4, gpt-4-turbo, gpt-3.5-turbo
- **Setup**: Get API key from [OpenAI Platform](https://platform.openai.com/)

### Anthropic

- **Models**: claude-3-5-sonnet-20241022, claude-3-opus-20240229
- **Setup**: Get API key from [Anthropic Console](https://console.anthropic.com/)

### Google

- **Models**: gemini-2.0-flash-exp, gemini-1.5-pro
- **Setup**: Get API key from [Google AI Studio](https://makersuite.google.com/)

## Advanced Features

### Tool Usage

Janito includes powerful built-in tools for:

- File operations (read, write, search)
- Code execution
- Web scraping
- System commands
- And more...

### Profiles and Roles
Use predefined system prompts:
```bash
janito --profile developer "Create a REST API"
janito --role python-expert "Optimize this algorithm"
```

### Environment Variables
You can also configure via environment variables:
```bash
export MOONSHOTAI_API_KEY=your_key_here
export JANITO_PROVIDER=moonshotai
export JANITO_MODEL=kimi-k1-8k
```

## Examples

### Code Generation
```bash
janito "Create a Python FastAPI application with user authentication"
```

### File Analysis
```bash
janito "Analyze the performance bottlenecks in my_app.py"
```

### Data Processing
```bash
janito "Process this CSV file and generate summary statistics"
```

### Web Development
```bash
janito "Create a responsive landing page with Tailwind CSS"
```

## Support

- **Documentation**: Check individual provider directories for detailed setup guides
- **Issues**: Report bugs and feature requests on GitHub
- **Discord**: Join our community for help and discussions