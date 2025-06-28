"""
Key bindings for Janito Chat CLI.
"""

from prompt_toolkit.key_binding import KeyBindings
from janito.tools.permissions import get_global_allowed_permissions

class KeyBindingsFactory:
    @staticmethod
    def create():
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

        @bindings.add("f1")
        def _(event):
            buf = event.app.current_buffer
            buf.text = "/restart"
            buf.validate_and_handle()

        @bindings.add("f2")
        def _(event):
            buf = event.app.current_buffer
            # Toggle read permission based on current state
            current = get_global_allowed_permissions()
            next_state = "off" if getattr(current, "read", False) else "on"
            buf.text = f"/read {next_state}"
            buf.validate_and_handle()

        @bindings.add("f3")
        def _(event):
            buf = event.app.current_buffer
            current = get_global_allowed_permissions()
            next_state = "off" if getattr(current, "write", False) else "on"
            buf.text = f"/write {next_state}"
            buf.validate_and_handle()

        @bindings.add("f4")
        def _(event):
            buf = event.app.current_buffer
            current = get_global_allowed_permissions()
            next_state = "off" if getattr(current, "execute", False) else "on"
            buf.text = f"/execute {next_state}"
            buf.validate_and_handle()

        @bindings.add("f12")
        def _(event):
            buf = event.app.current_buffer
            buf.text = "Do It"
            buf.validate_and_handle()

        return bindings
