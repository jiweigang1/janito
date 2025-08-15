"""
Git repository analysis plugin for janito.
"""

import os
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime

from janito.plugins.base import Plugin, PluginMetadata
from janito.tools.tool_base import ToolBase, ToolPermissions


class GitStatusTool(ToolBase):
    """Tool to analyze git repository status."""

    tool_name = "git_status"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, path: str = ".") -> str:
        """
        Get git status for the repository.

        Args:
            path: Path to the git repository

        Returns:
            Git status information as string
        """
        try:
            os.chdir(path)
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                check=True,
            )

            if not result.stdout.strip():
                return "Working directory clean"

            lines = result.stdout.strip().split("\n")
            status_summary = {}

            for line in lines:
                if len(line) >= 2:
                    status = line[:2]
                    filename = line[3:]
                    if status not in status_summary:
                        status_summary[status] = []
                    status_summary[status].append(filename)

            output = []
            for status, files in status_summary.items():
                output.append(f"{status}: {len(files)} files")
                for f in files[:5]:  # Show first 5 files
                    output.append(f"  {f}")
                if len(files) > 5:
                    output.append(f"  ... and {len(files) - 5} more")

            return "\n".join(output)

        except subprocess.CalledProcessError as e:
            return f"Error getting git status: {e.stderr}"
        except FileNotFoundError:
            return "Git not found. Please install git."


class GitLogTool(ToolBase):
    """Tool to analyze git commit history."""

    tool_name = "git_log"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, path: str = ".", limit: int = 10) -> str:
        """
        Get recent git commits.

        Args:
            path: Path to the git repository
            limit: Number of commits to show

        Returns:
            Git log information as string
        """
        try:
            os.chdir(path)
            result = subprocess.run(
                ["git", "log", "--oneline", "--max-count", str(limit)],
                capture_output=True,
                text=True,
                check=True,
            )

            return result.stdout.strip()

        except subprocess.CalledProcessError as e:
            return f"Error getting git log: {e.stderr}"
        except FileNotFoundError:
            return "Git not found. Please install git."


class GitBranchTool(ToolBase):
    """Tool to analyze git branches."""

    tool_name = "git_branches"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, path: str = ".") -> str:
        """
        Get git branch information.

        Args:
            path: Path to the git repository

        Returns:
            Branch information as string
        """
        try:
            os.chdir(path)

            # Get current branch
            current_result = subprocess.run(
                ["git", "branch", "--show-current"],
                capture_output=True,
                text=True,
                check=True,
            )

            current_branch = current_result.stdout.strip()

            # Get all branches
            branches_result = subprocess.run(
                ["git", "branch", "-a"], capture_output=True, text=True, check=True
            )

            branches = branches_result.stdout.strip().split("\n")

            output = [f"Current branch: {current_branch}"]
            output.append("All branches:")

            for branch in branches:
                branch = branch.strip()
                if branch.startswith("*"):
                    branch = branch[2:]  # Remove asterisk
                    output.append(f"  * {branch} (current)")
                else:
                    output.append(f"  {branch}")

            return "\n".join(output)

        except subprocess.CalledProcessError as e:
            return f"Error getting git branches: {e.stderr}"
        except FileNotFoundError:
            return "Git not found. Please install git."


class GitStatsTool(ToolBase):
    """Tool to get git repository statistics."""

    tool_name = "git_stats"
    permissions = ToolPermissions(read=True, write=False, execute=True)

    def run(self, path: str = ".") -> str:
        """
        Get git repository statistics.

        Args:
            path: Path to the git repository

        Returns:
            Repository statistics as string
        """
        try:
            os.chdir(path)

            stats = {}

            # Total commits
            commits_result = subprocess.run(
                ["git", "rev-list", "--count", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            stats["total_commits"] = commits_result.stdout.strip()

            # Contributors
            contributors_result = subprocess.run(
                ["git", "shortlog", "-sn", "--all"],
                capture_output=True,
                text=True,
                check=True,
            )

            contributors = contributors_result.stdout.strip().split("\n")
            stats["total_contributors"] = len(contributors)
            stats["top_contributors"] = contributors[:5]

            # Files
            files_result = subprocess.run(
                ["git", "ls-files"], capture_output=True, text=True, check=True
            )

            files = files_result.stdout.strip().split("\n")
            stats["total_files"] = len(files)

            # Languages (approximate by file extension)
            extensions = {}
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext:
                    extensions[ext] = extensions.get(ext, 0) + 1

            top_languages = sorted(
                extensions.items(), key=lambda x: x[1], reverse=True
            )[:5]

            output = [
                f"Repository Statistics:",
                f"Total commits: {stats['total_commits']}",
                f"Total contributors: {stats['total_contributors']}",
                f"Total files: {stats['total_files']}",
                "",
                "Top contributors:",
            ]

            for contributor in stats["top_contributors"]:
                output.append(f"  {contributor.strip()}")

            output.extend(
                [
                    "",
                    "Top file types:",
                ]
            )

            for ext, count in top_languages:
                output.append(f"  {ext}: {count} files")

            return "\n".join(output)

        except subprocess.CalledProcessError as e:
            return f"Error getting git stats: {e.stderr}"
        except FileNotFoundError:
            return "Git not found. Please install git."


class GitAnalyzerPlugin(Plugin):
    """Plugin providing git repository analysis tools."""

    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="git_analyzer",
            version="1.0.0",
            description="Git repository analysis and insights",
            author="Janito Coder Team",
            license="MIT",
            homepage="https://github.com/ikignosis/janito-coder",
        )

    def get_tools(self):
        return [GitStatusTool, GitLogTool, GitBranchTool, GitStatsTool]

    def initialize(self):
        print("Git Analyzer plugin initialized!")

    def cleanup(self):
        print("Git Analyzer plugin cleaned up!")


# This makes the plugin discoverable
PLUGIN_CLASS = GitAnalyzerPlugin
