## Providers

### Provider Parameters (`config`)

All LLM providers support an optional `config` dictionary for provider-specific settings. You can pass this dictionary to the provider constructor:

```python
provider = OpenAIProvider(model_name="gpt-4o", config={"base_url": "https://api.example.com/v1"})
```

- For `openai` and compatible providers, you can set `base_url` to use a custom endpoint.
- For Azure, additional options like `endpoint` and `api_version` may be supported as keys within `config`.

---

### azure_openai

**Description:** Azure-hosted OpenAI models (API-compatible, may require endpoint and version)

**Models:**
- azure-gpt-35-turbo: GPT-3.5 family turbo, hosted via Azure.
- azure-gpt-4: GPT-4 model, hosted via Azure.

**Auth:**
- Expects API key and Azure endpoint via credential manager or environment variables.

**Usage:**
- Use provider name `azure_openai` in CLI/config. Model selection as shown above.

---
