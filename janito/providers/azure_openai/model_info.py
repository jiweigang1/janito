from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "azure_openai_deployment": LLMModelInfo(
        name="azure_openai_deployment",
        context="N/A",
        max_input="N/A",
        max_cot="N/A",
        max_response="N/A",
        thinking_supported=False,
        default_temp=0.2,
        open="azure_openai",
        driver="AzureOpenAIModelDriver",
    )
}
