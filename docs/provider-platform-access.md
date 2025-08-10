# Provider Platform and Documentation Access

This table shows the accessibility status of each provider's platform/dashboard and API documentation.

| Provider | Platform Access | Documentation | API Docs | Status |
|----------|-----------------|---------------|----------|--------|
| **Alibaba** | [Alibaba Cloud Console](https://account.alibabacloud.com) | [Model Studio Help](https://www.alibabacloud.com/help/en/model-studio) | [API Reference](https://www.alibabacloud.com/help/en/model-studio/api-reference) | ✅ Full Access |
| **Anthropic** | [Console](https://console.anthropic.com) | [API Docs](https://docs.anthropic.com/en/api/getting-started) | [API Reference](https://docs.anthropic.com/en/api/messages) | ⚠️ Console Blocked |
| **Cerebras** | [API Dashboard](https://api.cerebras.ai) | [Inference Docs](https://cerebras.ai/inference) | [API Docs](https://cerebras.ai/inference) | ✅ Full Access |
| **DeepSeek** | [Platform](https://platform.deepseek.com) | [API Docs](https://platform.deepseek.com/api-docs) | [API Reference](https://platform.deepseek.com/api-docs) | ❌ All Blocked |
| **Google** | [AI Studio](https://aistudio.google.com) | [Gemini API Docs](https://ai.google.dev/gemini-api/docs) | [API Reference](https://ai.google.dev/gemini-api/docs) | ✅ Full Access |
| **MoonshotAI** | [Platform](https://platform.moonshot.ai) | [API Docs](https://platform.moonshot.ai/docs) | [API Reference](https://platform.moonshot.ai/docs) | ✅ Full Access |
| **OpenAI** | [Platform](https://platform.openai.com) | [API Docs](https://platform.openai.com/docs) | [API Reference](https://platform.openai.com/docs/api-reference) | ❌ All Blocked |
| **Z.ai** | [API Management](https://z.ai/manage-apikey/apikey-list) | [Model API Docs](https://z.ai/model-api) | [API Reference](https://z.ai/model-api) | ✅ Full Access |

## Status Legend

- ✅ **Full Access**: Both platform and documentation are publicly accessible
- ⚠️ **Partial Access**: Documentation available but platform/dashboard blocked
- ❌ **Blocked**: Both platform and documentation are inaccessible (403 errors)

## Notes

- **API Endpoints**: All API base URLs return 404 when accessed directly without authentication (expected behavior)
- **Authentication**: All providers require valid API keys for actual API usage
- **Regional Restrictions**: Some providers may have additional access restrictions based on geographic location