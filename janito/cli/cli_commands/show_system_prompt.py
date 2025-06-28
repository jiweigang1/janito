"""
CLI Command: Show the resolved system prompt for the main agent (single-shot mode)
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
    context["role"] = agent_role or "software developer"
    pd = PlatformDiscovery()
    context["platform"] = pd.get_platform_name()
    context["python_version"] = pd.get_python_version()
    context["shell_info"] = pd.detect_shell()

    # Locate and load the system prompt template
    templates_dir = (
        Path(__file__).parent.parent.parent / "agent" / "templates" / "profiles"
    )
    template_path = templates_dir / "system_prompt_template_main.txt.j2"
    template_content = None
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()
    else:
        # Try package import fallback
        try:
            with importlib.resources.files("janito.agent.templates.profiles").joinpath(
                "system_prompt_template_main.txt.j2"
            ).open("r", encoding="utf-8") as file:
                template_content = file.read()
        except (FileNotFoundError, ModuleNotFoundError, AttributeError):
            print(
                f"[janito] Could not find system_prompt_template_main.txt.j2 in {template_path} nor in janito.agent.templates.profiles package."
            )
            print("No system prompt is set or resolved for this configuration.")
            return

    template = Template(template_content)
    system_prompt = template.render(**context)

    print("\n--- System Prompt (resolved) ---\n")
    print(system_prompt)
    print("\n-------------------------------\n")
    if agent_role:
        print(f"[Role: {agent_role}]")
