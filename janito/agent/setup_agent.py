from pathlib import Path
from jinja2 import Template
import importlib.resources
import sys
import warnings
from janito.tools import get_local_tools_adapter
from janito.llm.agent import LLMAgent
from janito.drivers.driver_registry import get_driver_class
from queue import Queue
from janito.platform_discovery import PlatformDiscovery


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
        # Pass provider to agent, let agent create driver
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
        # Set default template directory
        templates_dir = Path(__file__).parent / "templates" / "profiles"
    template_filename = f"system_prompt_template_{profile}.txt.j2"
    template_path = templates_dir / template_filename

    template_content = None
    if template_path.exists():
        with open(template_path, "r", encoding="utf-8") as file:
            template_content = file.read()
    else:
        # Try package import fallback: janito.agent.templates.profiles.system_prompt_template_<profile>.txt.j2
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
                warnings.warn(
                    f"[janito] Could not find {template_filename} in {template_path} nor in janito.agent.templates.profiles package."
                )
                raise FileNotFoundError(
                    f"Template file not found in either {template_path} or package resource."
                )

    import time
    template = Template(template_content)
    # Prepare context for Jinja2 rendering from llm_driver_config
    # Compose context for Jinja2 rendering without using to_dict or temperature
    context = {}
    context["role"] = role or "developer"
    context["profile"] = profile
    # Normalize and inject allowed tool permissions
    from janito.tools.tool_base import ToolPermissions
    from janito.tools.permissions import get_global_allowed_permissions

    if allowed_permissions is None:
        # Fallback to globally configured permissions if not explicitly provided
        allowed_permissions = get_global_allowed_permissions()

    # Convert ToolPermissions -> string like "rwx" so the Jinja template can use
    # membership checks such as `'r' in allowed_permissions`.
    if isinstance(allowed_permissions, ToolPermissions):
        perm_str = ""
        if allowed_permissions.read:
            perm_str += "r"
        if allowed_permissions.write:
            perm_str += "w"
        if allowed_permissions.execute:
            perm_str += "x"
        allowed_permissions = perm_str or None  # None if empty

    context["allowed_permissions"] = allowed_permissions

    # Inject platform information only when execute permission is granted
    if allowed_permissions and 'x' in allowed_permissions:
        pd = PlatformDiscovery()
        context["platform"] = pd.get_platform_name()
        context["python_version"] = pd.get_python_version()
        context["shell_info"] = pd.detect_shell()
    # DEBUG: Show permissions passed to template
        from rich import print as rich_print
    debug_flag = False
    try:
        debug_flag = (hasattr(sys, 'argv') and ('--debug' in sys.argv or '--verbose' in sys.argv or '-v' in sys.argv))
    except Exception:
        pass
    if debug_flag:
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Rendering system prompt template '[cyan]{template_filename}[/cyan]' with allowed_permissions: [yellow]{allowed_permissions}[/yellow]")
        rich_print(f"[bold magenta][DEBUG][/bold magenta] Template context: [green]{context}[/green]")
    start_render = time.time()
    rendered_prompt = template.render(**context)
    end_render = time.time()
    
    # Create the agent as before, now passing the explicit role
    # Do NOT pass temperature; do not depend on to_dict
    agent = LLMAgent(
        provider_instance,
        tools_provider,
        agent_name=role or "developer",
        system_prompt=rendered_prompt,
        input_queue=input_queue,
        output_queue=output_queue,
        verbose_agent=verbose_agent,
    )
    agent.template_vars["role"] = context["role"]
    agent.template_vars["profile"] = profile
    # Store template path and context for dynamic prompt refresh
    agent.system_prompt_template = str(template_path)
    agent._template_vars = context.copy()
    agent._original_template_vars = context.copy()
    return agent


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
    # If provider_instance has create_driver, wire queues (single-shot mode)
    input_queue = None
    output_queue = None
    driver = None
    if hasattr(provider_instance, "create_driver"):
        driver = provider_instance.create_driver()
        driver.start()  # Ensure the driver background thread is started
        input_queue = getattr(driver, "input_queue", None)
        output_queue = getattr(driver, "output_queue", None)

    # Automatically enable system prompt when a profile is specified

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
