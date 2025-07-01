# Changelog

All notable changes to this project will be documented in this file.

## [2.5.0] - 2025-07-01
### Added
- Show working directory in chat mode startup message.
- Bang (`!`) shell command handler for direct shell access from the chat interface.
- Elapsed time reporting to token usage summary and improved terminal output styling.
- CLI support for reading prompt from stdin and suppressing token usage summary in non-interactive mode.

### Changed
- Import `os` in help command handler for future extensibility.
- Refactored `ChatSession._chat_loop` to reduce complexity by extracting command and prompt handling methods.
- Refactored profile selection, removed `ProfileShellHandler`, and improved terminal reporter output for STDOUT/STDERR.
- Refactored to remove `exec_enabled` argument from agent and CLI setup; now uses `args.exec` directly.
- Improved terminal output: added `delete_current_line` to `RichTerminalReporter` for cleaner UI.
- Refactored and cleaned up: removed redundant import of `handle_command`, removed backup, structure, and test strategy files, and added `.vscode/settings.json` for VSCode excludes.

### Removed
- MistralAI provider and driver references and related files.
- Conversation history persistence and updated input history path.

### Documentation
- Removed inline web file viewer documentation from `README.md` for clarity and focus on core options.

## [2.4.0]

### Changed
- Refactored tool permission management: migrated to a permission-based model (read/write/execute), updated CLI and docs, removed legacy execution toggling.
- Enhanced tool permissions: tools are now grouped by permission, config supports tool_permissions, ask_user is read-only, and permissions are applied at startup.
- Refined permission and tool output messages in shell commands; improved tool listing by permission class in tools.py.
- Refactored agent and prompt handler setup, improved model switching, and enhanced user interrupt handling. Includes new /model shell command and fixes for provider registry ASCII fallback.
- Refactored agent system prompt and permissions logic, switched to profile-based template selection, removed unused templates, and added --profile CLI support.
- Refactored chat mode startup messages and permission reset handling for improved clarity.
- Refactored ChatSession and ChatShellState: removed allow_execution logic and related assignments, use exec_enabled directly for execution control.
- Refactored tool system to use latest git tag for version detection in release script.
- Refined release script to recommend creating a new git tag if version exists on PyPI.
- Removed termweb: web file viewer and related CLI/editor features, updated docs and config accordingly.
- Removed temporary file x.txt.
- Restored tool permissions to CLI defaults on /restart; store and retrieve default tool permissions in AllowedPermissionsState. Runner now sets and saves default permissions for restoration. Updated conversation_restart to restore or fallback to all-off permissions.
- Updated disabled execution tools message for clarity.
- Docs and UX: clarified permissions (read/write/exec), added profiles doc links, and removed localhost references from UI/toolbar.

### Added
- Agent/driver: drain driver's input queue before sending new messages in chat() to prevent stale DriverInput processing.

### Fixed
- Ensure tools adapter is always available in provider classes, even if driver is missing. Prevents AttributeError in generic code paths relying on execute_tool().

## [2.3.1] - 2025-06-25
### Changed
- Bumped version to 2.3.1 in `version.py`, `pyproject.toml`, and `__init__.py`.

## [2.3.0] - 2025-06-25
### Added
- requirements-dev.txt with development dependencies (pytest, pre-commit, ruff, detect-secrets, codespell, black) for code quality and testing
- Java outline support to get_file_outline tool, including package-private methods
- create_driver method to AzureOpenAIProvider for driver instantiation
- CLI --version test and suppress pytest-asyncio deprecation warning
- New dependencies: prompt_toolkit, lxml, requests, bs4 to requirements.txt

### Changed
- Improved error messages and documentation
- Refined error handling in open_html_in_browser.py and open_url.py
- Refactor remove_file tool: use ReportAction.DELETE for all file removal actions
- Remove redundant _prepare_api_kwargs override in AzureOpenAIModelDriver
- Refactor(azure_openai): use 'model' directly in API kwargs, remove deployment_name remapping
- Add public read-only driver_config property to AzureOpenAIProvider
- Add _prepare_api_kwargs to support deployment_name for Azure OpenAI API compatibility
- Update toolbar bindings: add CTRL-C for interrupt/exit, clarify F1 usage
- Update pyproject.toml optional-dependencies section for setuptools compatibility
- Remove references to max_results in FindFilesTool docstring
- Refactor: use .jsonl extension for input history files instead of .log
- Refactor get_file_outline core logic to remove duplication and add tests
- Test CLI: Ensure error on missing provider and validate supported models output for each provider
- Configure dynamic dependencies in pyproject.toml
- Define dependencies in requirements.txt: attrs, rich, pathspec, setuptools, pyyaml, jinja2
- Add workdir support to LocalToolsAdapter and CLI; improve Python tool adapters
- Friendly error message when the provider is not present from the available ones

### Fixed
- Ensure error on missing provider and validate supported models output for each provider
- Update supported models table; remove o4-mini-high model from code and docs

## [2.1.1] - 2024-06-23
### Changed
- Bumped version to 2.1.1 in `version.py`, `pyproject.toml`, and `__init__.py`.
- docs: add DeepSeek setup guide, update navigation and references
    - Add docs/deepseek-setup.md with setup instructions for DeepSeek provider
    - Link DeepSeek setup in docs/index.md and mkdocs.yml navigation
    - Fix model name: change 'deepseek-coder' to 'deepseek-reasoner' in DeepSeek provider and model_info
    - Update DeepSeek provider docstrings and options to match supported models

## [2.1.0] - 2024-06-09
### Added

### Changed
- Bumped version to 2.1.0 in `version.py`, `pyproject.toml`, and `__init__.py`.

---

*Older changes may not be listed.*
