# Simplify Complex Functions

The following functions and methods have been flagged by `ruff` (C901) as too complex (complexity > 10). Consider refactoring them to improve maintainability and readability.

## Locations of Complex Functions

| File                                                      | Function/Class                              | Complexity | Allowed | Fixed? |
|-----------------------------------------------------------|---------------------------------------------|------------|---------|--------|
| janito/agent/setup_agent.py                               | setup_agent                                 | 16         | 10      | ✅    |
| janito/cli/chat_mode/session.py                           | __init__ (ChatSession)                      | 11         | 10      | ✅    |
| janito/cli/chat_mode/session_profile_select.py            | select_profile                              | 12         | 10      | ✅    |
| janito/cli/chat_mode/shell/commands/tools.py              | run                                         | 17         | 10      | ✅    |
| janito/cli/chat_mode/toolbar.py                           | get_toolbar_func                            | 11         | 10      | ✅✅   |
| janito/cli/cli_commands/list_tools.py                     | handle_list_tools                           | 17         | 10      | ✅    |
| janito/cli/cli_commands/show_system_prompt.py             | handle_show_system_prompt                   | 13         | 10      | ✅    |
| janito/cli/core/setters.py                                | handle_set                                  | 12         | 10      | ✅    |
| janito/cli/prompt_core.py                                 | _handle_inner_event                         | 11         | 10      | ✅    |
| janito/drivers/openai/driver.py                           | _call_api                                   | 17         | 10      | ✅✅   |
| janito/drivers/openai/driver.py                           | convert_history_to_api_messages             | 12         | 10      | ✅✅   |
| janito/llm/agent.py                                       | chat                                        | 11         | 10      | ✅✅   |
| janito/llm/agent.py                                       | reset_driver_config_to_model_defaults       | 13         | 10      | ✅✅   |
| janito/tools/adapters/local/__init__.py                   | (import error: E402)                        | -          | -       | ✅    |
| janito/tools/tools_adapter.py                             | execute_by_name                             | 11         | 10      | ✅    |

## General Strategies for Simplification

- **Split large functions**: Break down large functions into smaller, focused helper functions.
- **Reduce nesting**: Minimize nested conditionals and loops.
- **Early returns**: Use early returns to reduce indentation.
- **Extract classes**: If a function manages a lot of state, consider extracting a class.
- **Remove unused code**: Delete dead code and redundant branches.

## Next Steps

- Refactor the above functions to reduce their complexity.
- Rerun `pre-commit` to verify improvements.

---
*This file was generated to help address code complexity issues detected by pre-commit hooks.*
