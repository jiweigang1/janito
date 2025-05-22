from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "qwen-max": LLMModelInfo(
        name="qwen-max",
        context=32768,
        max_input=30720,
        max_cot=None,
        max_response=8192,
        thinking_supported=False,
        default_temp=0.2,
        open=False,
        driver="DashScopeModelDriver"
    ),
    "qwen-plus": LLMModelInfo(
        name="qwen-plus",
        context=131072,
        max_input=129024,
        max_cot=None,
        max_response=8192,
        thinking_supported=False,
        default_temp=0.2,
        open=False,
        driver="DashScopeModelDriver"
    ),
    "qwen-turbo": LLMModelInfo(
        name="qwen-turbo",
        context=1008192,
        max_input=1000000,
        max_cot=None,
        max_response=8192,
        thinking_supported=False,
        default_temp=0.2,
        open=False,
        driver="DashScopeModelDriver"
    ),
    "qwen-plus-2025-04-28": LLMModelInfo(
        name="qwen-plus-2025-04-28",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open=False,
        driver="DashScopeModelDriver"
    ),
    "qwen-turbo-2025-04-28": LLMModelInfo(
        name="qwen-turbo-2025-04-28",
        context=[1000000, 131072],
        max_input=[1000000, 129024],
        max_cot=38912,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=False,
        driver="DashScopeModelDriver"
    ),
    "qwen3-235b-a22b": LLMModelInfo(
        name="qwen3-235b-a22b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-32b": LLMModelInfo(
        name="qwen3-32b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-30b-a3b": LLMModelInfo(
        name="qwen3-30b-a3b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-14b": LLMModelInfo(
        name="qwen3-14b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-8b": LLMModelInfo(
        name="qwen3-8b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-4b": LLMModelInfo(
        name="qwen3-4b",
        context=131072,
        max_input=129024,
        max_cot=38912,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-1.7b": LLMModelInfo(
        name="qwen3-1.7b",
        context=32768,
        max_input=[30720, 28672],
        max_cot=30720,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
    "qwen3-0.6b": LLMModelInfo(
        name="qwen3-0.6b",
        context=30720,
        max_input=[30720, 28672],
        max_cot=30720,
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open=True,
        driver="DashScopeModelDriver"
    ),
}
