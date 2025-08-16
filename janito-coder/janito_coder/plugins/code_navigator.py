"""
Code navigation and analysis plugin using tree-sitter.
"""

import os
import re
from typing import Dict, List, Optional, Any
from pathlib import Path

try:
    from tree_sitter import Language, Parser
    from tree_sitter_languages import get_language, get_parser

    TREESITTER_AVAILABLE = True
except ImportError:
    TREESITTER_AVAILABLE = False

from janito.plugins.base import Plugin, PluginMetadata
from janito.tools.tool_base import ToolBase, ToolPermissions


class FindDefinitionTool(ToolBase):
    """Tool to find function/class definitions in code."""

    tool_name = "find_definition"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, symbol: str, path: str = ".", language: str = None) -> str:
        """
        Find definitions of functions, classes, or variables.

        Args:
            symbol: Name of the symbol to find
            path: Directory or file to search in
            language: Specific language to search (python, javascript, etc.)

        Returns:
            Definition locations as string
        """
        if not TREESITTER_AVAILABLE:
            return "Tree-sitter not available. Please install janito-coder with tree-sitter support."

        try:
            results = []
            search_path = Path(path)

            if search_path.is_file():
                files = [search_path]
            else:
                # Find all source files
                extensions = {
                    "python": [".py"],
                    "javascript": [".js", ".jsx"],
                    "typescript": [".ts", ".tsx"],
                    "java": [".java"],
                    "c": [".c", ".h"],
                    "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
                    "rust": [".rs"],
                    "go": [".go"],
                    "ruby": [".rb"],
                    "php": [".php"],
                    "swift": [".swift"],
                    "kotlin": [".kt"],
                    "scala": [".scala"],
                    "csharp": [".cs"],
                }

                if language:
                    extensions_to_search = extensions.get(language.lower(), [])
                else:
                    extensions_to_search = [
                        ext for exts in extensions.values() for ext in exts
                    ]

                files = []
                for ext in extensions_to_search:
                    files.extend(search_path.rglob(f"*{ext}"))

            for file_path in files:
                if file_path.is_file():
                    definitions = self._find_definitions_in_file(file_path, symbol)
                    results.extend(definitions)

            if not results:
                return f"No definitions found for '{symbol}'"

            output = [f"Found {len(results)} definitions for '{symbol}':"]
            for result in results:
                output.append(f"  {result}")

            return "\n".join(output)

        except Exception as e:
            return f"Error finding definitions: {str(e)}"

    def _find_definitions_in_file(self, file_path: Path, symbol: str) -> List[str]:
        """Find definitions in a single file."""
        results = []

        try:
            # Determine language from file extension
            ext = file_path.suffix.lower()
            language_map = {
                ".py": "python",
                ".js": "javascript",
                ".jsx": "javascript",
                ".ts": "typescript",
                ".tsx": "typescript",
                ".java": "java",
                ".c": "c",
                ".h": "c",
                ".cpp": "cpp",
                ".cc": "cpp",
                ".cxx": "cpp",
                ".hpp": "cpp",
                ".rs": "rust",
                ".go": "go",
                ".rb": "ruby",
                ".php": "php",
                ".swift": "swift",
                ".kt": "kotlin",
                ".scala": "scala",
                ".cs": "csharp",
            }

            language_name = language_map.get(ext)
            if not language_name:
                return results

            # Get parser for the language
            try:
                parser = get_parser(language_name)
                language = get_language(language_name)
            except:
                return results

            # Parse the file
            with open(file_path, "r", encoding="utf-8") as f:
                source_code = f.read()

            tree = parser.parse(bytes(source_code, "utf8"))

            # Find definitions based on language
            if language_name == "python":
                results.extend(
                    self._find_python_definitions(tree, source_code, symbol, file_path)
                )
            elif language_name in ["javascript", "typescript"]:
                results.extend(
                    self._find_js_definitions(tree, source_code, symbol, file_path)
                )
            elif language_name == "java":
                results.extend(
                    self._find_java_definitions(tree, source_code, symbol, file_path)
                )
            elif language_name in ["c", "cpp"]:
                results.extend(
                    self._find_cpp_definitions(tree, source_code, symbol, file_path)
                )
            elif language_name == "rust":
                results.extend(
                    self._find_rust_definitions(tree, source_code, symbol, file_path)
                )
            elif language_name == "go":
                results.extend(
                    self._find_go_definitions(tree, source_code, symbol, file_path)
                )

        except Exception:
            pass  # Skip files that can't be parsed

        return results

    def _find_python_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find Python function/class definitions."""
        results = []
        lines = source_code.split("\n")

        def find_nodes(node, type_name):
            if node.type in ["function_definition", "class_definition"]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results

    def _find_js_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find JavaScript/TypeScript function/class definitions."""
        results = []

        def find_nodes(node, type_name):
            if node.type in [
                "function_declaration",
                "class_declaration",
                "method_definition",
            ]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results

    def _find_java_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find Java class/method definitions."""
        results = []

        def find_nodes(node, type_name):
            if node.type in ["class_declaration", "method_declaration"]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results

    def _find_cpp_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find C++ function/class definitions."""
        results = []

        def find_nodes(node, type_name):
            if node.type in [
                "function_definition",
                "class_specifier",
                "struct_specifier",
            ]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results

    def _find_rust_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find Rust function/struct definitions."""
        results = []

        def find_nodes(node, type_name):
            if node.type in ["function_item", "struct_item", "enum_item", "trait_item"]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results

    def _find_go_definitions(
        self, tree, source_code: str, symbol: str, file_path: Path
    ) -> List[str]:
        """Find Go function/type definitions."""
        results = []

        def find_nodes(node, type_name):
            if node.type in ["function_declaration", "type_declaration"]:
                for child in node.children:
                    if (
                        child.type == "identifier"
                        and child.text.decode("utf8") == symbol
                    ):
                        start_line = node.start_point[0] + 1
                        results.append(
                            f"{file_path}:{start_line}: {node.type} '{symbol}'"
                        )
                        break

            for child in node.children:
                find_nodes(child, type_name)

        find_nodes(tree.root_node, symbol)
        return results


class FindReferencesTool(ToolBase):
    """Tool to find references to symbols in code."""

    tool_name = "find_references"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, symbol: str, path: str = ".", language: str = None) -> str:
        """
        Find all references to a symbol.

        Args:
            symbol: Name of the symbol to find references for
            path: Directory or file to search in
            language: Specific language to search

        Returns:
            Reference locations as string
        """
        if not TREESITTER_AVAILABLE:
            return "Tree-sitter not available. Please install janito-coder with tree-sitter support."

        try:
            results = []
            search_path = Path(path)

            if search_path.is_file():
                files = [search_path]
            else:
                # Find all source files
                extensions = {
                    "python": [".py"],
                    "javascript": [".js", ".jsx"],
                    "typescript": [".ts", ".tsx"],
                    "java": [".java"],
                    "c": [".c", ".h"],
                    "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
                    "rust": [".rs"],
                    "go": [".go"],
                    "ruby": [".rb"],
                    "php": [".php"],
                    "swift": [".swift"],
                    "kotlin": [".kt"],
                    "scala": [".scala"],
                    "csharp": [".cs"],
                }

                if language:
                    extensions_to_search = extensions.get(language.lower(), [])
                else:
                    extensions_to_search = [
                        ext for exts in extensions.values() for ext in exts
                    ]

                files = []
                for ext in extensions_to_search:
                    files.extend(search_path.rglob(f"*{ext}"))

            for file_path in files:
                if file_path.is_file():
                    references = self._find_references_in_file(file_path, symbol)
                    results.extend(references)

            if not results:
                return f"No references found for '{symbol}'"

            output = [f"Found {len(results)} references to '{symbol}':"]
            for result in results:
                output.append(f"  {result}")

            return "\n".join(output)

        except Exception as e:
            return f"Error finding references: {str(e)}"

    def _find_references_in_file(self, file_path: Path, symbol: str) -> List[str]:
        """Find references in a single file."""
        results = []

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Simple regex-based reference finding
            # This is a basic implementation - a more sophisticated approach
            # would use tree-sitter queries
            lines = content.split("\n")

            for i, line in enumerate(lines, 1):
                # Skip comments and strings (basic filtering)
                stripped_line = line.strip()
                if (
                    stripped_line.startswith("#")
                    or stripped_line.startswith("//")
                    or stripped_line.startswith("/*")
                    or stripped_line.startswith("*")
                ):
                    continue

                # Find symbol usage (basic pattern matching)
                pattern = r"\b" + re.escape(symbol) + r"\b"
                matches = re.finditer(pattern, line)

                for match in matches:
                    # Get context around the match
                    start = max(0, match.start() - 20)
                    end = min(len(line), match.end() + 20)
                    context = line[start:end].strip()

                    results.append(f"{file_path}:{i}: {context}")

        except Exception:
            pass  # Skip files that can't be read

        return results


class CodeStructureTool(ToolBase):
    """Tool to analyze code structure and complexity."""

    tool_name = "code_structure"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, path: str = ".", language: str = None) -> str:
        """
        Analyze code structure and provide overview.

        Args:
            path: Directory or file to analyze
            language: Specific language to analyze

        Returns:
            Code structure analysis as string
        """
        try:
            search_path = Path(path)

            if search_path.is_file():
                files = [search_path]
            else:
                # Find all source files
                extensions = {
                    "python": [".py"],
                    "javascript": [".js", ".jsx"],
                    "typescript": [".ts", ".tsx"],
                    "java": [".java"],
                    "c": [".c", ".h"],
                    "cpp": [".cpp", ".cc", ".cxx", ".hpp"],
                    "rust": [".rs"],
                    "go": [".go"],
                    "ruby": [".rb"],
                    "php": [".php"],
                    "swift": [".swift"],
                    "kotlin": [".kt"],
                    "scala": [".scala"],
                    "csharp": [".cs"],
                }

                if language:
                    extensions_to_search = extensions.get(language.lower(), [])
                else:
                    extensions_to_search = [
                        ext for exts in extensions.values() for ext in exts
                    ]

                files = []
                for ext in extensions_to_search:
                    files.extend(search_path.rglob(f"*{ext}"))

            analysis = {
                "total_files": len(files),
                "languages": {},
                "total_lines": 0,
                "total_size": 0,
                "file_details": [],
            }

            for file_path in files:
                if file_path.is_file():
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()

                        lines = len(content.split("\n"))
                        size = file_path.stat().st_size

                        ext = file_path.suffix.lower()
                        language_name = {
                            ".py": "Python",
                            ".js": "JavaScript",
                            ".jsx": "JavaScript",
                            ".ts": "TypeScript",
                            ".tsx": "TypeScript",
                            ".java": "Java",
                            ".c": "C",
                            ".h": "C",
                            ".cpp": "C++",
                            ".cc": "C++",
                            ".cxx": "C++",
                            ".hpp": "C++",
                            ".rs": "Rust",
                            ".go": "Go",
                            ".rb": "Ruby",
                            ".php": "PHP",
                            ".swift": "Swift",
                            ".kt": "Kotlin",
                            ".scala": "Scala",
                            ".cs": "C#",
                        }.get(ext, "Unknown")

                        analysis["languages"][language_name] = (
                            analysis["languages"].get(language_name, 0) + 1
                        )
                        analysis["total_lines"] += lines
                        analysis["total_size"] += size

                        analysis["file_details"].append(
                            {
                                "path": str(file_path),
                                "language": language_name,
                                "lines": lines,
                                "size": size,
                            }
                        )

                    except Exception:
                        continue

            # Generate report
            output = [
                "Code Structure Analysis",
                "=" * 30,
                f"Total files: {analysis['total_files']}",
                f"Total lines: {analysis['total_lines']:,}",
                f"Total size: {analysis['total_size']:,} bytes",
                "",
                "Languages:",
            ]

            for lang, count in sorted(
                analysis["languages"].items(), key=lambda x: x[1], reverse=True
            ):
                output.append(f"  {lang}: {count} files")

            output.extend(["", "Largest files:"])

            # Sort by size and show top 10
            sorted_files = sorted(
                analysis["file_details"], key=lambda x: x["size"], reverse=True
            )[:10]
            for file_info in sorted_files:
                output.append(
                    f"  {file_info['path']}: {file_info['lines']} lines, {file_info['size']} bytes"
                )

            return "\n".join(output)

        except Exception as e:
            return f"Error analyzing code structure: {str(e)}"


class CodeNavigatorPlugin(Plugin):
    """Plugin providing code navigation and analysis tools."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="code_navigator",
            version="1.0.0",
            description="Code navigation and static analysis tools",
            author="Janito Coder Team",
            license="MIT",
            homepage="https://github.com/ikignosis/janito-coder",
        )

    def get_tools(self):
        return [FindDefinitionTool, FindReferencesTool, CodeStructureTool]

    def initialize(self):
        print("Code Navigator plugin initialized!")

    def cleanup(self):
        print("Code Navigator plugin cleaned up!")


# This makes the plugin discoverable
PLUGIN_CLASS = CodeNavigatorPlugin
