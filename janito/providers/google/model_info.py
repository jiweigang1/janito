from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "gemini-pro": LLMModelInfo(
        name="gemini-pro",
        context=32768,
        max_input=32768,
        max_cot="N/A",
        max_response=8192,
        thinking_supported=True,
        default_temp=0.2,
        open="google",
        other={"driver": "GoogleGenaiModelDriver"}
    ),
    "gemini-1.5-pro-latest": LLMModelInfo(
        name="gemini-1.5-pro-latest",
        context=65536,
        max_input=65536,
        max_cot="N/A",
        max_response=16384,
        thinking_supported=True,
        default_temp=0.2,
        open="google",
        other={"driver": "GoogleGenaiModelDriver"}
    )
}
