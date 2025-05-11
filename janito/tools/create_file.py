import os
from janito.tool_registry import register_tool

# from janito.agent.tools_utils.expand_path import expand_path
from janito.tool_utils import display_path
from janito.tool_base import ToolBase
from janito.report_events import ReportAction
from janito.i18n import tr


from janito.tools.validate_file_syntax.core import validate_file_syntax


@register_tool(name="create_file")
class CreateFileTool(ToolBase):
    """
    Create a new file with the given content.
    Args:
        file_path (str): Path to the file to create.
        content (str): Content to write to the file.
    Returns:
        str: Status message indicating the result. Example:
            - "✅ Successfully created the file at ..."

    Note: Syntax validation is automatically performed after this operation.
    """

    def run(self, file_path: str, content: str) -> str:
        expanded_file_path = file_path  # Using file_path as is
        disp_path = display_path(expanded_file_path)
        file_path = expanded_file_path
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    existing_content = f.read()
            except Exception as e:
                existing_content = f"[Error reading file: {e}]"
            return tr(
                "❗ Cannot create file: file already exists at '{disp_path}'.\n--- Current file content ---\n{existing_content}",
                disp_path=disp_path,
                existing_content=existing_content,
            )
        dir_name = os.path.dirname(file_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        self.report_info(
            tr("📝 Create file '{disp_path}' ...", disp_path=disp_path),
            ReportAction.WRITE,
        )
        with open(file_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(content)
        new_lines = content.count("\n") + 1 if content else 0
        self.report_success(tr("✅ {new_lines} lines", new_lines=new_lines), ReportAction.WRITE)
        # Perform syntax validation and append result
        validation_result = validate_file_syntax(file_path)
        return (
            tr("✅ Created file {new_lines} lines.", new_lines=new_lines)
            + f"\n{validation_result}"
        )
