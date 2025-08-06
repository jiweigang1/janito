# Configuring Janito for Cerebras

Janito supports Cerebras as an LLM provider. This guide explains how to configure Janito to use Cerebras models.

## 1. Obtain a Cerebras API Key

- Sign up or log in at [Cerebras AI Platform](https://cloud.cerebras.ai) to get your API key.
- Navigate to the API Keys section in your dashboard to create and manage your keys.

## 2. Set Your Cerebras API Key in Janito

You must specify both the API key and the provider name when configuring Janito for Cerebras:

```bash
janito --set-api-key YOUR_CEREBRAS_API_KEY -p cerebras
```

Replace `YOUR_CEREBRAS_API_KEY` with your actual Cerebras API key.

## 3. Select Cerebras as the Provider

You can set Cerebras as your default provider:

```bash
janito --set provider=cerebras
```

Or specify it per command:

```bash
janito -p cerebras "Your prompt here"
```

## 4. Choose a Cerebras Model

Janito supports the following Cerebras models:

**Production Models:**

- `llama-4-scout-17b-16e-instruct` - Llama 4 Scout (109B parameters, ~2600 tokens/s)
- `llama-3.3-70b` - Llama 3.3 70B (70B parameters, ~2100 tokens/s)
- `llama3.1-8b` - Llama 3.1 8B (8B parameters, ~2200 tokens/s)
- `qwen-3-32b` - Qwen 3 32B (32B parameters, ~2600 tokens/s)

**Preview Models:**

- `llama-4-maverick-17b-128e-instruct` - Llama 4 Maverick (400B parameters, ~2400 tokens/s)
- `qwen-3-235b-a22b-instruct-2507` - Qwen 3 235B Instruct (235B parameters, ~1400 tokens/s)
- `qwen-3-235b-a22b-thinking-2507` - Qwen 3 235B Thinking (235B parameters, ~1700 tokens/s)
- `qwen-3-coder-480b` - Qwen 3 480B Coder (480B parameters, ~2000 tokens/s)
- `gpt-oss-120b` - GPT-OSS 120B (120B parameters, ~3000 tokens/s)

**Note:** Preview models are intended for evaluation purposes only and may be discontinued with short notice. Production models are fully supported for production use.

To select a model:

```bash
janito -p cerebras -m llama-3.3-70b-instruct "Your prompt here"
```

## 5. Verify Your Configuration

Show your current configuration (the config file path will be shown at the top):

```bash
janito --show-config
```

## 6. API Endpoint Information

Cerebras uses an OpenAI-compatible API endpoint:

- **Base URL**: `https://api.cerebras.ai/v1`
- **Authentication**: Bearer token (API key)
- **Format**: OpenAI API format
- **Documentation**: [Cerebras Inference API Reference](https://inference-docs.cerebras.ai/api-reference)

## 7. Pricing Information

For the most current pricing information, please check the [Cerebras pricing page](https://cloud.cerebras.ai/pricing).

Cerebras offers competitive pricing for their high-speed inference service, with different rates for production and preview models. Pricing is typically based on:

- Input tokens per 1K
- Output tokens per 1K
- Model complexity and size

All models benefit from Cerebras' industry-leading inference speeds, providing excellent cost-performance ratios.

## 8. Troubleshooting

- Ensure your API key is correct and has sufficient credits.
- If you encounter issues, use `janito --list-providers` to verify Cerebras is available.
- Check your API key permissions and rate limits in the Cerebras AI Platform dashboard.
- For more help, see the main [Configuration Guide](guides/configuration.md) or run `janito --help`.

---

For more details on supported models and features, see [Supported Providers & Models](supported-providers-models.md).