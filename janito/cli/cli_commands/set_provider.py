"""
CLI Command: Set the current LLM provider
"""

def handle_set_provider(args, mgr):
    mgr.set_default_provider(args.set_provider)
    print(f"Current provider set to '{args.set_provider}' in {mgr.get_config_path()}.")
