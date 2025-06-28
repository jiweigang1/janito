from janito.llm.model import LLMModelInfo

MODEL_SPECS = {
    "claude-3-opus-20240229": LLMModelInfo(
        name="claude-3-opus-20240229",
        max_response=200000,
        default_temp=0.7,
        driver="AnthropicModelDriver",
    ),
    "claude-3-sonnet-20240229": LLMModelInfo(
        name="claude-3-sonnet-20240229",
        max_response=200000,
        default_temp=0.7,
        driver="AnthropicModelDriver",
    ),
    "claude-3-haiku-20240307": LLMModelInfo(
        name="claude-3-haiku-20240307",
        max_response=200000,
        default_temp=0.7,
        driver="AnthropicModelDriver",
    ),
}
