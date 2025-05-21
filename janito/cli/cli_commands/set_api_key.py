"""
CLI Command: Set API key for the current or selected provider
"""

_provider_instance = None

def get_provider_instance():
    global _provider_instance
    if _provider_instance is None:
        _provider_instance = setup_provider()
    return _provider_instance

def handle_set_api_key(args, mgr):
    api_key = args.set_api_key
    provider_instance = get_provider_instance()
    try:
        provider = getattr(provider_instance, 'name', None)

        if not provider:
            print("Error: No provider could be determined from setup_provider.")
            return
    except Exception as ex:
        import traceback; traceback.print_exc()
        print(f"[janito EXCEPTION] Exception when getting provider_instance.name: {ex!r}")
        return
    mgr.set_api_key(provider, api_key)
    print(f"API key set for provider '{provider}'.")
