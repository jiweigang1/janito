from janito.tool_base import ToolBase
from janito.tool_registry import register_tool

from rich import print as rich_print
from janito.i18n import tr
from rich.panel import Panel
from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.formatted_text import HTML
from janito.cli.chat_mode.prompt_style import prompt_style
from prompt_toolkit.styles import Style
toolbar_style = Style.from_dict({'bottom-toolbar': 'fg:yellow bg:darkred'})


@register_tool(name="ask_user")
class AskUserTool(ToolBase):
    """
    Request clarification or input from the user whenever there is uncertainty, ambiguity, missing information, or multiple valid options. Returns the user's response as a string.

    Args:
        question (str): The question to ask the user.
    Returns:
        str: The user's response as a string. Example:
            - "Yes"
            - "No"
            - "Some detailed answer..."
    """

    def run(self, question: str) -> str:

        rich_print(Panel.fit(question, title=tr("Question"), style="cyan"))

        bindings = KeyBindings()
        mode = {"multiline": False}

        @bindings.add("c-r")
        def _(event):
            pass

        # F12 instruction rotation
        _f12_instructions = [
            tr("proceed"),
            tr("go ahead"),
            tr("continue"),
            tr("next"),
            tr("okay"),
        ]
        _f12_index = {"value": 0}

        @bindings.add("f12")
        def _(event):
            """When F12 is pressed, rotate through a set of short instructions."""
            buf = event.app.current_buffer
            idx = _f12_index["value"]
            buf.text = _f12_instructions[idx]
            buf.validate_and_handle()
            _f12_index["value"] = (idx + 1) % len(_f12_instructions)

                # Use shared CLI styles
        # prompt_style contains the prompt area and input background
        # toolbar_style contains the bottom-toolbar styling

        # Compose the styles for use in this prompt
        from prompt_toolkit.styles import merge_styles
        style = merge_styles([
            prompt_style,
            toolbar_style
        ])

        def get_toolbar():
            f12_hint = ""
            if mode["multiline"]:
                return HTML(
                    f"<b>Multiline mode (Esc+Enter to submit). Type /single to switch.</b>{f12_hint}"
                )
            else:
                return HTML(
                    f"<b>Single-line mode (Enter to submit). Type /multi for multiline.</b>{f12_hint}"
                )

        session = PromptSession(
            multiline=False,
            key_bindings=bindings,
            editing_mode=EditingMode.EMACS,
            bottom_toolbar=get_toolbar,
            style=style,
        )

        prompt_icon = HTML("<prompt>💬 </prompt>")

        while True:
            response = session.prompt(prompt_icon)
            if not mode["multiline"] and response.strip() == "/multi":
                mode["multiline"] = True
                session.multiline = True
                continue
            elif mode["multiline"] and response.strip() == "/single":
                mode["multiline"] = False
                session.multiline = False
                continue
            else:
                return response
