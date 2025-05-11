from janito.tool_registry import register_tool
import os
import fnmatch

@register_tool(name="list_files")
class ListFilesTool:
    """
    Lists files in the specified directory, optionally filtered by a pattern.

    Args:
        directory (str): The directory to list files from.
        pattern (str, optional): A Unix shell-style wildcard pattern (e.g., '*.txt'). If omitted, all files are listed.

    Returns:
        str: A newline-separated list of file names, or an error message if the directory does not exist.

    Note:
        When used by the Gemini driver, the result is returned as a dict with the key 'result', e.g., {"result": "file1.txt\nfile2.txt"}.
    """
    def run(self, directory: str, pattern: str = None) -> str:
        if not os.path.isdir(directory):
            return f"❗ Directory not found: {directory}"
        try:
            files = os.listdir(directory)
            if pattern:
                files = fnmatch.filter(files, pattern)
            return '\n'.join(files) if files else 'No files found.'
        except Exception as e:
            return f"❗ Failed to list files in {directory}: {e}"
