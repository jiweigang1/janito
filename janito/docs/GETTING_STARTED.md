# Getting Started with Janito

This guide will help you set up Janito CLI quickly and start using it with MoonshotAI as your default provider.

## Quick Setup (2 minutes)

### 1. Install Janito
```bash
pip install janito
```

### 2. Get Your MoonshotAI API Key

1. Go to [Moonshot AI Platform](https://platform.moonshot.cn/)
2. Sign up for an account
3. Navigate to API Keys section
4. Create a new API key

### 3. Configure Janito
```bash
# Set MoonshotAI as your default provider
janito --set-api-key YOUR_API_KEY -p moonshotai

# Verify it's working
janito "Hello, can you introduce yourself?"
```

## Your First Commands

### Basic Usage
```bash
# Simple prompt
janito "Create a Python script to calculate fibonacci numbers"

# With specific model
janito -m kimi-k1-8k "Explain machine learning in simple terms"

# Interactive chat mode
janito --chat
```

### Working with Files
```bash
# Analyze a file
janito "Analyze the performance of my_app.py" < my_app.py

# Generate code in a specific directory
janito -W ./my_project "Create a REST API with FastAPI"
```

## Configuration Options

### Set as Default Provider
```bash
# Make MoonshotAI your permanent default
janito --set provider=moonshotai
janito --set model=kimi-k1-8k
```

### Environment Variables
You can also use environment variables:
```bash
export MOONSHOTAI_API_KEY=your_key_here
export JANITO_PROVIDER=moonshotai
export JANITO_MODEL=kimi-k1-8k
```

## MoonshotAI Models

Janito supports these MoonshotAI models:

- **kimi-k1-8k**: Fast responses, good for general tasks
- **kimi-k1-32k**: Better for longer contexts
- **kimi-k1-128k**: Best for very long documents
- **kimi-k2-turbo-preview**: Latest model with enhanced capabilities
- **kimi-k2-turbo-preview**: Turbo version of the advanced reasoning model

## Next Steps

1. **Explore tools**: Run `janito --list-tools` to see available tools
2. **Try chat mode**: Run `janito --chat` for interactive sessions
3. **Check examples**: Look at the main README.md for more usage examples
4. **Join community**: Get help and share tips with other users

## Troubleshooting

### Common Issues

**"Provider not found" error**
```bash
# Check available providers
janito --list-providers

# Re-register MoonshotAI
janito --set-api-key YOUR_KEY -p moonshotai
```

**"Model not available" error**
```bash
# List available MoonshotAI models
janito -p moonshotai --list-models
```

**API key issues**
```bash
# Check current configuration
janito --show-config

# Reset API key
janito --set-api-key NEW_KEY -p moonshotai
```

### Getting Help

- Check the main README.md for comprehensive documentation
- Use `janito --help` for command-line options
- Visit our GitHub repository for issues and discussions