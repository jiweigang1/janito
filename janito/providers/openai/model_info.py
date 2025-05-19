MODEL_SPECS = {
    "gpt-3.5-turbo": {
        "context": 16385,
        "max_input": 12289,
        "max_cot": "N/A",
        "max_response": 4096,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "gpt-4.1": {
        "context": 1047576,
        "max_input": 1014808,
        "max_cot": "N/A",
        "max_response": 32768,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "codex-mini-latest": {
        "context": 1047576,
        "max_input": 1014808,
        "max_cot": "N/A",
        "max_response": 32768,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIResponsesModelDriver"
    },
    "gpt-4.1-mini": {
        "context": 1047576,
        "max_input": 1014808,
        "max_cot": "N/A",
        "max_response": 32768,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "gpt-4.1-nano": {
        "context": 1047576,
        "max_input": 1014808,
        "max_cot": "N/A",
        "max_response": 32768,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "gpt-4-turbo": {
        "context": 128000,
        "driver": "OpenAIModelDriver"
    },
    "gpt-4o": {
        "context": 128000,
        "max_input": 123904,
        "max_cot": "N/A",
        "max_response": 4096,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "gpt-4o-mini": {
        "context": 128000,
        "max_input": 111616,
        "max_cot": "N/A",
        "max_response": 16384,
        "thinking_supported": False,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "o3-mini": {
        "context": 200000,
        "max_input": 100000,
        "max_cot": "N/A",
        "max_response": 100000,
        "thinking_supported": True,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "o4-mini": {
        "context": 200000,
        "max_input": 100000,
        "max_cot": "N/A",
        "max_response": 100000,
        "thinking_supported": True,
        "default_temp": 1.0,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "o4-mini-high": {
        "context": 200000,
        "max_input": 100000,
        "max_cot": "N/A",
        "max_response": 100000,
        "thinking_supported": True,
        "default_temp": 0.2,
        "open": "openai",
        "driver": "OpenAIModelDriver"
    },
    "codex-mini-latest": {
        "context": 4096,
        "driver": "OpenAIResponsesModelDriver"
    },
    "gpt-4-turbo": {
        "context": 128000,
        "driver": "OpenAIModelDriver"
    }
}
