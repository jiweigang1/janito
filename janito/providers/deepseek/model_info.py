MODEL_SPECS = {
    "deepseek-chat": {
        "description": "DeepSeek Chat Model (OpenAI-compatible)",
        "context_window": 8192,
        "max_tokens": 4096,
        "family": "deepseek",
        "default": True,
    },
    "deepseek-coder": {
        "description": "DeepSeek Coder Model (OpenAI-compatible)",
        "context_window": 8192,
        "max_tokens": 4096,
        "family": "deepseek",
        "default": False,
    },
}
