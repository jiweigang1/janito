"""
Command dispatcher for janito CLI
"""
from janito.cli.cli_commands.list_tools import handle_list_tools
from janito.cli.cli_commands.set_api_key import handle_set_api_key
from janito.cli.cli_commands.set_provider import handle_set_provider
from janito.cli.cli_commands.set_provider_kv import handle_set_provider_kv
from janito.cli.cli_commands.list_providers import handle_list_providers
from janito.cli.cli_commands.list_models import handle_list_models
from janito.cli.cli_commands.model_selection import handle_model_selection

from janito.cli.cli_commands.show_config import handle_show_config

def dispatch_command(args, mgr, parser):
    if getattr(args, 'show_config', False):
        handle_show_config(mgr)
    elif args.list_tools:
        handle_list_tools()
    elif args.set_api_key:
        handle_set_api_key(args, mgr)
    elif args.set_provider:
        handle_set_provider(args, mgr)
    elif args.set:
        handle_set_provider_kv(args, mgr)
    elif args.list_providers:
        handle_list_providers()
    elif args.user_prompt:
        from janito.cli.single_shot_mode.handler import PromptHandler as SingleShotPromptHandler
        handler = SingleShotPromptHandler(args)
        handler.handle()
        ret = True
        if not ret:
            parser.print_help()
    else:
        from janito.cli.cli_commands.handle_chat_mode import handle_chat_mode
        handle_chat_mode(args, parser)
