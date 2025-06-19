from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "mistral-medium-latest": LLMModelInfo(
        name="mistral-medium-latest",
        context=32000,
        max_input=32000,
        max_cot="N/A",
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open="mistralai",
        driver="MistralAIModelDriver",
    ),
    "mistral-large-latest": LLMModelInfo(
        name="mistral-large-latest",
        context=64000,
        max_input=64000,
        max_cot="N/A",
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open="mistralai",
        driver="MistralAIModelDriver",
    ),
    "mistral-small-latest": LLMModelInfo(
        name="mistral-small-latest",
        context=16000,
        max_input=16000,
        max_cot="N/A",
        max_response=4096,
        thinking_supported=False,
        default_temp=0.2,
        open="mistralai",
        driver="MistralAIModelDriver",
    ),
}
