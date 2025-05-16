from janito.llm_driver import LLMDriver
from janito.tool_registry import ToolRegistry
from typing import Any, Optional, List, Iterator, Union
import threading
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

class Agent:
    _event_lock: threading.Lock
    _latest_event: Optional[str]

    """
    Represents an agent that interacts with an LLM driver to generate responses.
    No longer manages conversation history; the driver is responsible for all history management.
    The chat method supports cooperative cancellation and yields events from the driver's stream_generate method.
    """

    def __init__(self, driver: LLMDriver, agent_name: Optional[str] = None, system_prompt: Optional[str] = None, tools: Optional[List[dict]] = None, temperature: Optional[float] = None, **kwargs: Any):
        self.temperature = temperature
        self._event_lock = threading.Lock()
        self._latest_event = None
        self.driver = driver
        self.agent_name = agent_name or driver.get_name()
        self.state = {}
        self.config = kwargs

        self.system_prompt = system_prompt
        self.template_vars = {}  # For template variable support
        self._system_prompt_template_file = None  # Store template file path
        if tools is None:
            self.tools = ToolRegistry().get_tool_classes()
        else:
            self.tools = tools

    def set_template_var(self, key: str, value: Any) -> None:
        """Set a variable for system prompt template rendering and refresh prompt if template is set."""
        self.template_vars[key] = value
        if self._system_prompt_template_file:
            self._refresh_system_prompt_from_template()

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def set_system_using_template(self, template_file: str, **vars) -> None:
        self._system_prompt_template_file = template_file
        # Merge self.template_vars with any vars passed directly
        self.template_vars.update(vars)
        self._refresh_system_prompt_from_template()

    def _refresh_system_prompt_from_template(self):
        template_path = Path(self._system_prompt_template_file)
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(["txt", "j2"]),
        )
        template = env.get_template(template_path.name)
        rendered_prompt = template.render(**self.template_vars)
        self.set_system_prompt(rendered_prompt)

    def get_system_prompt(self) -> Optional[str]:
        return self.system_prompt

    def chat(self, prompt_or_messages: Union[str, List[dict]], role: str = "user", **kwargs: Any) -> Iterator[Any]:
        from janito.event_bus.bus import event_bus as system_event_bus
        # Remove UI-only arguments
        kwargs.pop('raw', None)
        generate_kwargs = dict(
            system_prompt=self.system_prompt,
            **kwargs
        )
        if self.tools:
            generate_kwargs['tools'] = self.tools
        event_iterator = self.driver.stream_generate(prompt_or_messages, **generate_kwargs)
        for event in event_iterator:
            system_event_bus.publish(event)
            yield event

    def set_latest_event(self, event: str) -> None:
        with self._event_lock:
            self._latest_event = event

    def get_latest_event(self) -> Optional[str]:
        with self._event_lock:
            return self._latest_event

    def get_history(self):
        """Delegate to the driver's get_history method."""
        return self.driver.get_history()

    def reset_conversation_history(self) -> None:
        """
        Reset/clear the conversation history using the driver's method.
        """
        if hasattr(self.driver, "clear_history"):
            self.driver.clear_history()

    def get_name(self) -> str:
        return self.agent_name
