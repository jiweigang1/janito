from janito.tool_registry import register_tool

@register_tool(name="create_file")
class CreateFileTool:
    """
    Creates a file at the specified path with the provided content.

    Args:
        file_path (str): The path where the file will be created.
        content (str): The content to write to the file.

    Returns:
        str: A status message indicating the result of the file creation.
    """
    def run(self, file_path: str, content: str) -> str:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"✅ Successfully created the file at {file_path}"
        except Exception as e:
            return f"❗ Failed to create file at {file_path}: {e}"
