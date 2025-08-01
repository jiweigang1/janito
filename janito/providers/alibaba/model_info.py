from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "qwen-turbo": LLMModelInfo(
        name="qwen-turbo",
        context=1008192,
        max_response=8192,
        category="Alibaba Qwen Turbo Model (OpenAI-compatible)",
        driver="OpenAIModelDriver",
    ),
    "qwen-plus": LLMModelInfo(
        name="qwen-plus", 
        context=131072,
        max_response=8192,
        category="Alibaba Qwen Plus Model (OpenAI-compatible)",
        driver="OpenAIModelDriver",
    ),
    "qwen-max": LLMModelInfo(
        name="qwen-max",
        context=32768, 
        max_response=8192,
        category="Alibaba Qwen Max Model (OpenAI-compatible)",
        driver="OpenAIModelDriver",
    ),

    "qwen3-coder-plus": LLMModelInfo(
        name="qwen3-coder-plus",
        context=1048576,
        max_response=65536,
        category="Alibaba Qwen3 Coder Plus Model (OpenAI-compatible)",
        driver="OpenAIModelDriver",
    ),
    "qwen3-coder-480b-a35b-instruct": LLMModelInfo(
        name="qwen3-coder-480b-a35b-instruct",
        context=262144,
        max_response=65536,
        category="Alibaba Qwen3 Coder 480B A35B Instruct Model (OpenAI-compatible)",
        driver="OpenAIModelDriver",
    ),
}