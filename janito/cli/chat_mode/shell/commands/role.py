from janito.cli.chat_mode.shell.commands.base import ShellCmdHandler

class RoleCommand(ShellCmdHandler):
    """Set or display the current role."""
    
    def __init__(self, shell_state, handler):
        super().__init__(shell_state, handler)
        self.name = "role"
        self.description = "Set or display the current role"
        self.usage = "role [new_role]"
        
    def execute(self, args):
        if not args:
            # Display current role
            current_role = self.handler.agent.template_vars.get('role', 'default')
            return f"Current role: {current_role}"
        else:
            # Set new role
            new_role = ' '.join(args)
            self.handler.agent.template_vars['role'] = new_role
            return f"Role set to: {new_role}"
            
    def get_completions(self, document, complete_event):
        # No completions for this command
        return []