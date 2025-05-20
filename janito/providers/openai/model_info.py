from janito.llm.model import ModelInfo

MODEL_SPECS = {
    "gpt-3.5-turbo": ModelInfo(name="gpt-3.5-turbo", context=16385, max_input=12289, max_cot="N/A", max_response=4096, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "gpt-4.1": ModelInfo(name="gpt-4.1", context=1047576, max_input=1014808, max_cot="N/A", max_response=32768, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "codex-mini-latest": ModelInfo(name="codex-mini-latest", context=1047576, max_input=1014808, max_cot="N/A", max_response=32768, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIResponsesModelDriver"}),
    "gpt-4.1-mini": ModelInfo(name="gpt-4.1-mini", context=1047576, max_input=1014808, max_cot="N/A", max_response=32768, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "gpt-4.1-nano": ModelInfo(name="gpt-4.1-nano", context=1047576, max_input=1014808, max_cot="N/A", max_response=32768, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "gpt-4-turbo": ModelInfo(name="gpt-4-turbo", context=128000, max_input="N/A", max_cot="N/A", max_response="N/A", thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "gpt-4o": ModelInfo(name="gpt-4o", context=128000, max_input=123904, max_cot="N/A", max_response=4096, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "gpt-4o-mini": ModelInfo(name="gpt-4o-mini", context=128000, max_input=111616, max_cot="N/A", max_response=16384, thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "o3-mini": ModelInfo(name="o3-mini", context=200000, max_input=100000, max_cot="N/A", max_response=100000, thinking_supported=True, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    "o4-mini": ModelInfo(name="o4-mini", context=200000, max_input=100000, max_cot="N/A", max_response=100000, thinking_supported=True, default_temp=1.0, open="openai", other={"driver": "OpenAIModelDriver"}),
    "o4-mini-high": ModelInfo(name="o4-mini-high", context=200000, max_input=100000, max_cot="N/A", max_response=100000, thinking_supported=True, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
    # duplicated codex-mini-latest and gpt-4-turbo with minimal properties for distinction
    "codex-mini-latest-alt": ModelInfo(name="codex-mini-latest", context=4096, max_input="N/A", max_cot="N/A", max_response="N/A", thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIResponsesModelDriver"}),
    "gpt-4-turbo-alt": ModelInfo(name="gpt-4-turbo", context=128000, max_input="N/A", max_cot="N/A", max_response="N/A", thinking_supported=False, default_temp=0.2, open="openai", other={"driver": "OpenAIModelDriver"}),
}
