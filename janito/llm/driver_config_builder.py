from typing import Type, Dict, Any
from janito.llm.driver_info import LLMDriverInfo

def build_llm_driver_info(config: Dict[str, Any], driver_class: Type) -> LLMDriverInfo:
    """
    Build an LLMDriverInfo instance for the given driver class based on its declared driver_fields.
    Any config fields not in driver_fields or LLMDriverInfo fields go into .extra.
    """
    driver_fields = getattr(driver_class, "driver_fields", None)
    if driver_fields is None:
        # Default to all LLMDriverInfo fields except model
        driver_fields = set(LLMDriverInfo.__dataclass_fields__.keys()) - {'model', 'extra'}
    base_info = {}
    extra = {}
    for k, v in (config or {}).items():
        if k in driver_fields and k in LLMDriverInfo.__dataclass_fields__:
            base_info[k] = v
        else:
            extra[k] = v
    # Fill missing args as None
    for field in driver_fields:
        if field not in base_info and field in LLMDriverInfo.__dataclass_fields__:
            base_info[field] = None
    return LLMDriverInfo(
        model=config.get('model_name') or config.get('model') or None,
        extra=extra,
        **base_info
    )
