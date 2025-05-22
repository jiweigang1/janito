from pathlib import Path
from jinja2 import Template

def setup_agent(provider_instance, llm_driver_config, role=None, templates_dir=None, zero_mode=False):
    """
    Creates an agent using a rendered system prompt template, passing an explicit role.
    """
    if zero_mode:
        agent = provider_instance.create_agent(
            agent_name=role or "software developer",
            config=llm_driver_config.to_dict(),
            system_prompt=None,
            tools=[],
            temperature=getattr(llm_driver_config, 'temperature', None),
        )
        return agent
    # Normal flow
    if templates_dir is None:
        # Set default template directory
        templates_dir = Path(__file__).parent / "templates" / "profiles"
    template_path = templates_dir / "system_prompt_template_main.txt.j2"
    # Load and render template
    with open(template_path, "r", encoding="utf-8") as file:
        template = Template(file.read())
    # Prepare context for Jinja2 rendering from llm_driver_config
    context = llm_driver_config.to_dict()
    context['role'] = role or "software developer"
    # Inject current platform environment information
    from janito.platform_discovery import PlatformDiscovery
    pd = PlatformDiscovery()
    context['platform'] = pd.get_platform_name()
    context['python_version'] = pd.get_python_version()
    context['shell_info'] = pd.detect_shell()
    rendered_prompt = template.render(**context)
    # Create the agent as before, now passing the explicit role
    agent = provider_instance.create_agent(
        agent_name=role or "software developer",
        config=llm_driver_config.to_dict(),
        system_prompt=rendered_prompt,
        temperature=getattr(llm_driver_config, 'temperature', None),
    )
    agent.template_vars["role"] = context["role"]
    return agent
