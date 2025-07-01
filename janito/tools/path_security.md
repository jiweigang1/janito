# Path Security in Tools Adapter

This module provides security enforcement for file and directory arguments passed to tools. When a tool argument is a path (e.g., file, directory, path, etc.), the adapter checks that the path is within the allowed working directory (`workdir`) defined at startup (via `-W` or `--workdir`).

## How it works
- The `validate_paths_in_arguments` function scans tool arguments for any values that look like paths, either by schema or by heuristics (argument names like `path`, `file`, `dir`, etc.).
- If any such path is outside the allowed `workdir`, a `PathSecurityError` is raised and the tool call is blocked.
- This check is enforced in the `ToolsAdapterBase.execute_by_name` method before tool execution.

## Usage
- The enforcement is automatic for all tools executed via the adapter if a `workdir` is set.
- To disable path restriction, do not set a `workdir` (not recommended for production).

## Example
If `workdir` is `/home/user/project` and a tool is called with `{"path": "/etc/passwd"}`, the call will be rejected with a security error.

## See also
- `janito/tools/path_security.py` for implementation
- `janito/tools/tools_adapter.py` for integration
