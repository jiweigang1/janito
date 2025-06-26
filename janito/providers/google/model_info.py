from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "gemini-2.5-flash": LLMModelInfo(
        name="gemini-2.5-flash",
        other={"description": "Google Gemini 2.5 Flash (OpenAI-compatible endpoint)"},
        open="google",
        driver="OpenAIModelDriver",
        max_response=8192,
        max_cot=24576,
        thinking_supported=True,
    ),
    # Add more Gemini models as needed
}
