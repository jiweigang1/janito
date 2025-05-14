"""
Interactive chat shell using PromptHandler (one-shot handler) for each user prompt.
Features:
- prompt_toolkit input with history and toolbar
- persistent input history
- slash command handling (/exit, /help, /tools, ...)
- one-shot prompt submission via PromptHandler
"""
import sys
from janito.cli.one_shot_run.handler import PromptHandler
from janito.cli.one_shot_run.output import handle_exception
from rich.console import Console
from prompt_toolkit.history import InMemoryHistory
from janito.cli.shell.input_history import UserInputHistory
from janito.cli.shell.commands import handle_command
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings


def get_prompt_session(mem_history):
    style = Style.from_dict({
        "bottom-toolbar": "bg:#333333 #ffffff",
        "": "bg:#005fdd #ffffff",
        "input-field": "bg:#005fdd #ffffff",
        "inputline": "bg:#005fdd #ffffff",
    })
    bindings = KeyBindings()
    @bindings.add("c-y")
    def _(event):
        buf = event.app.current_buffer
        buf.text = "Yes"
        buf.validate_and_handle()
    @bindings.add("c-n")
    def _(event):
        buf = event.app.current_buffer
        buf.text = "No"
        buf.validate_and_handle()
    return PromptSession(
        bottom_toolbar=lambda: HTML("<b>/help</b> <b>/exit</b> <b>/tools</b>"),
        style=style,
        editing_mode=EditingMode.VI,
        key_bindings=bindings,
        history=mem_history,
    )


def main():
    console = Console()
    console.print("[bold green]Welcome to the Janito One-Shot Chat Shell! Type /exit or press Ctrl+C to quit.[/bold green]")
    # Persistent input history
    user_input_history = UserInputHistory()
    input_dicts = user_input_history.load()
    mem_history = InMemoryHistory()
    for item in input_dicts:
        if isinstance(item, dict) and "input" in item:
            mem_history.append_string(item["input"])
    session = get_prompt_session(mem_history)
    while True:
        try:
            user_prompt = session.prompt(HTML("<inputline>💬 </inputline>"), multiline=False)
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold red]Exiting chat shell.[/bold red]")
            break
        cmd_input = user_prompt.strip()
        if not cmd_input:
            continue
        if cmd_input.startswith("/") or cmd_input.lower() in {"exit", ":q", "quit"}:
            result = handle_command(cmd_input, console)
            if result == "exit":
                break
            continue
        # Save to persistent history
        user_input_history.append(cmd_input)
        # Prepare args object for PromptHandler
        class Args:
            pass
        args = Args()
        args.user_prompt = cmd_input
        args.raw = False  # Set to True if you want raw output
        try:
            handler = PromptHandler(args)
            handler.handle()
        except Exception as e:
            handle_exception(e, console)


if __name__ == "__main__":
    main()
