from janito.llm.model import ModelInfo

MODEL_SPECS = {
    "azure-gpt-35-turbo": ModelInfo(
        name="azure-gpt-35-turbo",
        context=16385,
        max_input=12289,
        max_cot="N/A",
        max_response=4096,
        thinking_supported=False,
        default_temp=0.2,
        open="azure_openai",
        other={"driver": "AzureOpenAIModelDriver"}
    ),
    "azure-gpt-4": ModelInfo(
        name="azure-gpt-4",
        context=128000,
        max_input=123904,
        max_cot="N/A",
        max_response=4096,
        thinking_supported=False,
        default_temp=0.2,
        open="azure_openai",
        other={"driver": "AzureOpenAIModelDriver"}
    )
}
