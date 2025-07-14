import importlib.resources
import re
import os
import sys
import time
import warnings
import threading
from pathlib import Path
from jinja2 import Template
from pathlib import Path
from queue import Queue
from rich import print as rich_print
from janito.tools import get_local_tools_adapter
from janito.llm.agent import LLMAgent
from janito.drivers.driver_registry import get_driver_class
from janito.platform_discovery import PlatformDiscovery
from janito.tools.tool_base import ToolPermissions
from janito.tools.permissions import get_global_allowed_permissions

def _load_template_content(profile, templates_dir):
    """
    Loads the template content for the given profile from the specified directory or package resources.
    If the profile template is not found in the default locations, tries to load from the user profiles directory ~/.janito/profiles.
    """


    template_filename = f"system_prompt_template_{profile}.txt.j2"
    template_path = templates_dir / template_filename
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as file:
            return file.read(), template_path
    # Try package import fallback
    try:
        with importlib.resources.files("janito.agent.templates.profiles").joinpath(
            template_filename
        ).open("r", encoding="utf-8") as file:
            return file.read(), template_path
    except (FileNotFoundError, ModuleNotFoundError, AttributeError):
        # Try user profiles directory
        user_profiles_dir = Path(os.path.expanduser("~/.janito/profiles"))
        user_template_path = user_profiles_dir / profile
        if user_template_path.exists():
            with open(user_template_path, "r", encoding="utf-8") as file:
                return file.read(), user_template_path
        raise FileNotFoundError(
            f"[janito] Could not find profile-specific template '{template_filename}' in {template_path} nor in janito.agent.templates.profiles package nor in user profiles directory {user_template_path}."
        )


def _prepare_template_context(role, profile, allowed_permissions):
    """
    Prepares the context dictionary for Jinja2 template rendering.
    """
    context = {}
    context["role"] = role or "developer"
    context["profile"] = profile
    if allowed_permissions is None:
        allowed_permissions = get_global_allowed_permissions()
    # Convert ToolPermissions -> string like "rwx"
    if isinstance(allowed_permissions, ToolPermissions):
        perm_str = ""
        if allowed_permissions.read:
            perm_str += "r"
        if allowed_permissions.write:
            perm_str += "w"
        if allowed_permissions.execute:
            perm_str += "x"
        allowed_permissions = perm_str or None
    context["allowed_permissions"] = allowed_permissions
    # Inject platform info if execute permission is present
    if allowed_permissions and 'x' in allowed_permissions:
        pd = PlatformDiscovery()
        context["platform"] = pd.get_platform_name()
        context["python_version"] = pd.get_python_version()
        context["shell_info"] = pd.detect_shell()
    return context


def _create_agent(provider_instance, tools_provider, role, system_prompt, input_queue, output_queue, verbose_agent, context, template_path, profile):
    """
    Creates and returns an LLMAgent instance with the provided parameters.
    """
    agent = LLMAgent(
        provider_instance,
        tools_provider,
        agent_name=role or "developer",
        system_prompt=system_prompt,
        input_queue=input_queue,
        output_queue=output_queue,
        verbose_agent=verbose_agent,
    )
    agent.template_vars["role"] = context["role"]
    agent.template_vars["profile"] = profile
    agent.system_prompt_template = str(template_path)
    agent._template_vars = context.copy()
    agent._original_template_vars = context.copy()
    return agent


def setup_agent(
    provider_instance,
    llm_driver_config,
    role=None,
    templates_dir=None,
    zero_mode=False,
    input_queue=None,
    output_queue=None,
    verbose_tools=False,
    verbose_agent=False,
    allowed_permissions=None,
    profile=None,
    profile_system_prompt=None,
):
    """
    Creates an agent. A system prompt is rendered from a template only when a profile is specified.
    """
    tools_provider = get_local_tools_adapter()
    tools_provider.set_verbose_tools(verbose_tools)

    # If zero_mode is enabled or no profile is given we skip the system prompt.
    if zero_mode or (profile is None and profile_system_prompt is None):
        agent = LLMAgent(
            provider_instance,
            tools_provider,
            agent_name=role or "developer",
            system_prompt=None,
            input_queue=input_queue,
            output_queue=output_queue,
            verbose_agent=verbose_agent,
        )
        if role:
            agent.template_vars["role"] = role
        return agent

    # If profile_system_prompt is set, use it directly
    if profile_system_prompt is not None:
        agent = LLMAgent(
            provider_instance,
            tools_provider,
            agent_name=role or "developer",
            system_prompt=profile_system_prompt,
            input_queue=input_queue,
            output_queue=output_queue,
            verbose_agent=verbose_agent,
        )
        agent.template_vars["role"] = role or "developer"
        agent.template_vars["profile"] = None
        agent.template_vars["profile_system_prompt"] = profile_system_prompt
        return agent

    # Normal flow (profile-specific system prompt)
    if templates_dir is None:
        templates_dir = Path(__file__).parent / "templates" / "profiles"
    template_content, template_path = _load_template_content(profile, templates_dir)

    template = Template(template_content)
    context = _prepare_template_context(role, profile, allowed_permissions)

    # Debug output if requested
    debug_flag = False
    try:
        debug_flag = (hasattr(sys, 'argv') and ('--debug' in sys.argv or '--verbose' in sys.argv or '-v' in sys.argv))
    except Exception:
        pass
    if debug_flag:
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Rendering system prompt template '[cyan]{template_path.name}[/cyan]' with allowed_permissions: [yellow]{context.get('allowed_permissions')}[/yellow]")
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Template context: [green]{context}[/green]")
    start_render = time.time()
    rendered_prompt = template.render(**context)
    end_render = time.time()
    # Merge multiple empty lines into a single empty line
    rendered_prompt = re.sub(r'\n{3,}', '\n\n', rendered_prompt)

    return _create_agent(
        provider_instance,
        tools_provider,
        role,
        rendered_prompt,
        input_queue,
        output_queue,
        verbose_agent,
        context,
        template_path,
        profile,
    )


def create_configured_agent(
    *,
    provider_instance=None,
    llm_driver_config=None,
    role=None,
    verbose_tools=False,
    verbose_agent=False,
    templates_dir=None,
    zero_mode=False,
    allowed_permissions=None,
    profile=None,
    profile_system_prompt=None,
):
    """
    Normalizes agent setup for all CLI modes.

    Args:
        provider_instance: Provider instance for the agent
        llm_driver_config: LLM driver configuration
        role: Optional role string
        verbose_tools: Optional, default False
        verbose_agent: Optional, default False
        templates_dir: Optional
        zero_mode: Optional, default False

    Returns:
        Configured agent instance
    """
    input_queue = None
    output_queue = None
    driver = None
    if hasattr(provider_instance, "create_driver"):
        driver = provider_instance.create_driver()
        driver.start()  # Ensure the driver background thread is started
        input_queue = getattr(driver, "input_queue", None)
        output_queue = getattr(driver, "output_queue", None)

    agent = setup_agent(
        provider_instance=provider_instance,
        llm_driver_config=llm_driver_config,
        role=role,
        templates_dir=templates_dir,
        zero_mode=zero_mode,
        input_queue=input_queue,
        output_queue=output_queue,
        verbose_tools=verbose_tools,
        verbose_agent=verbose_agent,
        allowed_permissions=allowed_permissions,
        profile=profile,
        profile_system_prompt=profile_system_prompt,
    )
    if driver is not None:
        agent.driver = driver  # Attach driver to agent for thread management
    return agent