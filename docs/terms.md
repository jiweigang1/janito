
---

## ✅ Comprehensive API Interaction Terminology

| Term                       | Description                                                                                                                                                                                                                                                       |
| -------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Model Provider**         | The company or project offering API access to a language model. Examples: **OpenAI**, **Azure OpenAI Service**, **Anthropic**, **Google (Gemini)**, **Mistral**, **Meta (LLaMA)**, **Cohere**, **Aleph Alpha**, **xAI (Grok)**, **AWS Bedrock (multi-provider)**. |
| **Model**                  | The specific language model you interact with. Examples: `gpt-4-turbo`, `claude-3-opus`, `gemini-pro`.                                                                                                                                                            |
| **System Prompt**          | A special instruction that sets the model’s behavior, role, or context before processing user prompts.                                                                                                                                                            |
| **Prompt**                 | The input message or instruction sent by the user to the model.                                                                                                                                                                                                   |
| **Completion / Response**  | The model's generated reply to the user prompt.                                                                                                                                                                                                                   |
| **Token**                  | The smallest unit of text processed for billing and context limits. Includes input and output tokens.                                                                                                                                                             |
| **Context Window**         | The maximum number of tokens the model can handle in a single request, combining prompt and response.                                                                                                                                                             |
| **Inference**              | The process of generating a model response from the provided input.                                                                                                                                                                                               |
| **Temperature**            | Controls output randomness. Lower = more deterministic, higher = more creative.                                                                                                                                                                                   |
| **Top-k / Top-p Sampling** | Controls randomness by limiting or filtering possible next tokens based on rank or probability.                                                                                                                                                                   |
| **Latency**                | The time taken to return a response after sending a request.                                                                                                                                                                                                      |
| **Rate Limit**             | The maximum number of allowed requests per unit of time, enforced by the provider.                                                                                                                                                                                |
| **API Key**                | A secret credential used to authenticate and authorize API access.                                                                                                                                                                                                |
| **Quota / Billing**        | Usage tracking or charges, usually based on token counts or request volume.                                                                                                                                                                                       |

---

## ✅ Interaction Types

| Term                        | Description                                                                                                           |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| **Single-Turn Interaction** | One user prompt and one final model response. May include **automatic tool use loops** before producing the response. |
| **Multi-Turn Conversation** | A sequence of user and model messages, maintaining conversational context across turns.                               |

---

## ✅ Tool-Calling and Automation Terms

| Term                          | Description                                                                                                                                                                                |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Tool Call / Function Call** | A structured API call generated by the model to invoke external functionality (e.g., weather lookup, database query).                                                                      |
| **Tool Call Response**        | The data or result returned by the external tool in response to the model’s tool call.                                                                                                     |
| **Tool Use Auto Loop**        | An automatic process where the model issues one or more tool calls, receives results, and continues reasoning until it produces a final response—all within a **single user interaction**. |

---


