"""
CLI Command: Show the resolved system prompt for the main agent (single-shot mode)

Supports --profile to select a profile-specific system prompt template.
"""

from janito.cli.core.runner import prepare_llm_driver_config
from janito.platform_discovery import PlatformDiscovery
from pathlib import Path
from jinja2 import Template
import importlib.resources


def handle_show_system_prompt(args):
    # Collect modifiers as in JanitoCLI
    from janito.cli.main_cli import MODIFIER_KEYS

    modifiers = {
        k: getattr(args, k) for k in MODIFIER_KEYS if getattr(args, k, None) is not None
    }
    provider, llm_driver_config, agent_role = prepare_llm_driver_config(args, modifiers)
    if provider is None or llm_driver_config is None:
        print("Error: Could not resolve provider or LLM driver config.")
        return

    # Prepare context for Jinja2 rendering
    context = {}
    context["role"] = agent_role or "developer"
    context["profile"] = getattr(args, "profile", None)
    # Compute allowed_permissions from CLI args (as in agent setup)
    from janito.tools.tool_base import ToolPermissions
    read = getattr(args, "read", False)
    write = getattr(args, "write", False)
    execute = getattr(args, "exec", False)
    allowed = ToolPermissions(read=read, write=write, execute=execute)
    perm_str = ""
    if allowed.read:
        perm_str += "r"
    if allowed.write:
        perm_str += "w"
    if allowed.execute:
        perm_str += "x"
    allowed_permissions = perm_str or None
    context["allowed_permissions"] = allowed_permissions
    # DEBUG: Show permissions/context before rendering
    from rich import print as rich_print
    debug_flag = False
    import sys
    try:
        debug_flag = (hasattr(sys, 'argv') and ('--debug' in sys.argv or '--verbose' in sys.argv or '-v' in sys.argv))
    except Exception:
        pass
    if debug_flag:
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Rendering system prompt template '[cyan]{template_filename}[/cyan]' with allowed_permissions: [yellow]{allowed_permissions}[/yellow]")
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Template context: [green]{context}[/green]")
    if allowed_permissions and 'x' in allowed_permissions:
        pd = PlatformDiscovery()
        context["platform"] = pd.get_platform_name()
        context["python_version"] = pd.get_python_version()
        context["shell_info"] = pd.detect_shell()

    # Locate and load the system prompt template
    templates_dir = (
        Path(__file__).parent.parent.parent / "agent" / "templates" / "profiles"
    )
    profile = getattr(args, "profile", None)
    if profile:
        template_filename = f"system_prompt_template_{profile}.txt.j2"
        template_path = templates_dir / template_filename
    else:
        # No profile specified means the main agent has no dedicated system prompt template.
        print("[janito] No profile specified. The main agent runs without a system prompt template.\n"
              "Use --profile PROFILE to view a profile-specific system prompt.")
        return
    template_content = None
    if template_path and template_path.exists():
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()
    else:
        # Try package import fallback
        try:
            with importlib.resources.files("janito.agent.templates.profiles").joinpath(
                template_filename
            ).open("r", encoding="utf-8") as file:
                template_content = file.read()
        except (FileNotFoundError, ModuleNotFoundError, AttributeError):
            if profile:
                raise FileNotFoundError(
                    f"[janito] Could not find profile-specific template '{template_filename}' in {template_path} nor in janito.agent.templates.profiles package."
                )
            else:
                print(
                    f"[janito] Could not find {template_filename} in {template_path} nor in janito.agent.templates.profiles package."
                )
                print("No system prompt is set or resolved for this configuration.")
                return

    template = Template(template_content)
    system_prompt = template.render(**context)

    print(f"\n--- System Prompt (resolved, profile: {getattr(args, 'profile', 'main')}) ---\n")
    print(system_prompt)
    print("\n-------------------------------\n")
    if agent_role:
        print(f"[Role: {agent_role}]")
