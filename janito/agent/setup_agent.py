from pathlib import Path
from jinja2 import Template

def setup_agent(provider_instance, llm_driver_config, templates_dir=None):
    """
    Creates an agent using a rendered system prompt template.
    """
    if templates_dir is None:
        # Set default template directory
        templates_dir = Path(__file__).parent / "templates" / "profiles"
    template_path = templates_dir / "system_prompt_template_main.txt.j2"
    # Load and render template
    with open(template_path, "r", encoding="utf-8") as file:
        template = Template(file.read())
    # Prepare context for Jinja2 rendering from llm_driver_config
    context = llm_driver_config.to_dict()
    rendered_prompt = template.render(**context)
    # Create the agent as before, but now using the rendered prompt
    agent = provider_instance.create_agent(
        agent_name=getattr(llm_driver_config, 'role', None),
        config=llm_driver_config.to_dict(),
        system_prompt=rendered_prompt,
        temperature=getattr(llm_driver_config, 'temperature', None),
    )
    return agent
