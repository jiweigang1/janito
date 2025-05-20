"""
CLI Command utility: System prompt defaults
"""
def set_default_system_prompt(args):
    if not getattr(args, 'system', None):
        args.system = "You are an LLM agent. Respond to the user prompt as best as you can."
