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
    exec_enabled=False,
    allowed_permissions=None,
    profile=None,
):
    """
    Creates an agent. A system prompt is rendered from a template only when a profile is specified.
    """
    tools_provider = get_local_tools_adapter()
    tools_provider.set_verbose_tools(verbose_tools)

    # If zero_mode is enabled or no profile is given we skip the system prompt.
    if zero_mode or profile is None:
        # Pass provider to agent, let agent create driver
        agent = LLMAgent(
            provider_instance,
            tools_provider,
            agent_name=role or "software developer",
            system_prompt=None,
            input_queue=input_queue,
            output_queue=output_queue,
            verbose_agent=verbose_agent,
        )
        if role:
            agent.template_vars["role"] = role
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
    context["role"] = role or "software developer"
    context["profile"] = profile
    # Inject current platform environment information only if exec_enabled
    context["exec_enabled"] = bool(exec_enabled)
    if exec_enabled:
        pd = PlatformDiscovery()
        context["platform"] = pd.get_platform_name()
        context["python_version"] = pd.get_python_version()
        context["shell_info"] = pd.detect_shell()
    start_render = time.time()
    rendered_prompt = template.render(**context)
    end_render = time.time()
    
    # Create the agent as before, now passing the explicit role
    # Do NOT pass temperature; do not depend on to_dict
    agent = LLMAgent(
        provider_instance,
        tools_provider,
        agent_name=role or "software developer",
        system_prompt=rendered_prompt,
        input_queue=input_queue,
        output_queue=output_queue,
        verbose_agent=verbose_agent,
    )
    agent.template_vars["role"] = context["role"]
    agent.template_vars["profile"] = profile
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
    exec_enabled=False,
    allowed_permissions=None,

    profile=None,
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
        exec_enabled=exec_enabled,
        profile=profile,
    )
    if driver is not None:
        agent.driver = driver  # Attach driver to agent for thread management
    return agent
