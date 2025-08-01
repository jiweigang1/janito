# Provider Configuration Guide

This guide covers how to configure and use different LLM providers with Janito.

## MoonshotAI (Recommended)

**MoonshotAI** is the recommended default provider for Janito, offering excellent performance and competitive pricing.

### Setup
```bash
# Set API key
janito --set-api-key YOUR_API_KEY -p moonshotai

# Set as default provider
janito --set provider=moonshotai
janito --set model=kimi-k1-8k
```

### Available Models

- **kimi-k1-8k**: Fast, general-purpose model (8k context)
- **kimi-k1-32k**: Extended context model (32k context)
- **kimi-k1-128k**: Long context model (128k context)
- **kimi-k2-turbo-preview**: Latest enhanced model

### Environment Variables
```bash
export MOONSHOTAI_API_KEY=your_key_here
```

## OpenAI

### Setup
```bash
# Set API key
janito --set-api-key YOUR_API_KEY -p openai

# Use specific model
janito -p openai -m gpt-4 "Your prompt"
```

### Available Models

- **gpt-4**: Most capable model
- **gpt-4-turbo**: Faster, more efficient
- **gpt-3.5-turbo**: Cost-effective option

### Environment Variables
```bash
export OPENAI_API_KEY=your_key_here
```

## Anthropic

### Setup
```bash
# Set API key
janito --set-api-key YOUR_API_KEY -p anthropic

# Use Claude models
janito -p anthropic -m claude-3-5-sonnet-20241022 "Your prompt"
```

### Available Models

- **claude-3-5-sonnet-20241022**: Most capable
- **claude-3-opus-20240229**: High performance
- **claude-3-haiku-20240307**: Fast and cost-effective

### Environment Variables
```bash
export ANTHROPIC_API_KEY=your_key_here
```

## Google

### Setup
```bash
# Set API key
janito --set-api-key YOUR_API_KEY -p google

# Use Gemini models
janito -p google -m gemini-2.0-flash-exp "Your prompt"
```

### Available Models

- **gemini-2.0-flash-exp**: Latest experimental model
- **gemini-1.5-pro**: Production-ready
- **gemini-1.5-flash**: Fast and efficient

### Environment Variables
```bash
export GOOGLE_API_KEY=your_key_here
```

## Azure OpenAI

### Setup
```bash
# Set configuration
janito --set-api-key YOUR_API_KEY -p azure-openai
janito --set azure_deployment_name=your_deployment_name -p azure-openai
```

### Configuration

Requires both API key and deployment name:

- **API Key**: Your Azure OpenAI key
- **Deployment Name**: Your Azure deployment name
- **Base URL**: Your Azure endpoint URL

### Environment Variables
```bash
export AZURE_OPENAI_API_KEY=your_key_here
export AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
```

## Other Providers

Janito also supports these providers through OpenAI-compatible APIs:

### Alibaba Cloud
```bash
janito --set-api-key YOUR_KEY -p alibaba
```

### DeepSeek
```bash
janito --set-api-key YOUR_KEY -p deepseek
```

### Groq
```bash
janito --set-api-key YOUR_KEY -p groq
```

### Mistral
```bash
janito --set-api-key YOUR_KEY -p mistral
```

## Configuration Management

### Check Current Configuration
```bash
janito --show-config
```

### List All Providers
```bash
janito --list-providers
```

### List Models for a Provider
```bash
janito -p moonshotai --list-models
janito -p openai --list-models
```

### Switch Providers
```bash
# Temporarily for one command
janito -p openai -m gpt-4 "Your prompt"

# Permanently as default
janito --set provider=openai
janito --set model=gpt-4
```

## Advanced Configuration

### Custom Base URLs
For OpenAI-compatible providers, you can set custom base URLs:

```bash
janito --set base_url=https://your-custom-endpoint.com -p openai
```

### Provider-Specific Settings
Each provider can have custom settings:

```bash
# Set temperature for a specific provider/model
janito --set temperature=0.7 -p moonshotai -m kimi-k1-8k

# Set max tokens
janito --set max_tokens=2000 -p openai -m gpt-4
```

## Troubleshooting

### Provider Not Found
```bash
# Check if provider is registered
janito --list-providers

# Re-register provider
janito --set-api-key YOUR_KEY -p PROVIDER_NAME
```

### API Key Issues
```bash
# Check current API key
janito --show-config

# Reset API key
janito --set-api-key NEW_KEY -p PROVIDER_NAME
```

### Model Not Available
```bash
# List available models for provider
janito -p PROVIDER_NAME --list-models
```

## Best Practices

1. **Start with MoonshotAI**: It's the recommended default for good reason
2. **Use environment variables**: For CI/CD and containerized environments
3. **Test different models**: Each has different strengths and pricing
4. **Monitor usage**: Keep track of API costs and rate limits
5. **Use profiles**: Set up different configurations for different use cases