"""
Profile selection logic for Janito Chat CLI using questionary.
"""
import questionary
from questionary import Style

def select_profile():
    choices = [
        "helpful assistant",
        "developer",
        "using role...",
        "full custom system prompt..."
    ]
    custom_style = Style([
        ("highlighted", "bg:#00aaff #ffffff"),  # background for item under cursor
        ("question", "fg:#00aaff bold"),
    ])
    answer = questionary.select(
        "Select a profile to use:",
        choices=choices,
        default=None,
        style=custom_style
    ).ask()
    if answer == "helpful assistant":
        return {"profile": "assistant", "profile_system_prompt": None}
    if answer == "using role...":
        role_name = questionary.text("Enter the role name:").ask()
        return f"role:{role_name}"
    elif answer == "full custom system prompt...":
        from prompt_toolkit import PromptSession
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.enums import EditingMode
        from prompt_toolkit.formatted_text import HTML
        from .prompt_style import chat_shell_style

        mode = {"multiline": False}
        bindings = KeyBindings()

        @bindings.add("c-r")
        def _(event):
            pass

        @bindings.add("f12")
        def _(event):
            buf = event.app.current_buffer
            buf.text = "Do It"
            buf.validate_and_handle()

        def get_toolbar():
            if mode["multiline"]:
                return HTML("<b>Multiline mode (Esc+Enter to submit). Type /single to switch.</b>")
            else:
                return HTML("<b>Single-line mode (Enter to submit). Type /multi for multiline.</b>")

        session = PromptSession(
            multiline=False,
            key_bindings=bindings,
            editing_mode=EditingMode.EMACS,
            bottom_toolbar=get_toolbar,
            style=chat_shell_style,
        )
        prompt_icon = HTML("<inputline>📝 </inputline>")
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
                sanitized = response.strip()
                try:
                    sanitized.encode("utf-8")
                except UnicodeEncodeError:
                    sanitized = sanitized.encode("utf-8", errors="replace").decode("utf-8")
                return {"profile": None, "profile_system_prompt": sanitized}
    return answer
