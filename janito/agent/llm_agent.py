from janito.llm_driver import LLMDriver
from janito.conversation_history import LLMConversationHistory
from janito.tool_registry import ToolRegistry
import queue
from typing import Any, Optional, List, Iterator
import threading
import logging

from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path

class LLMAgent:
    _event_lock: threading.Lock
    _latest_event: Optional[str]

    """
    Represents an agent that interacts with an LLM driver to generate responses and manage conversation state.
    Only supports streaming/event-driven chat via the chat() method, which returns an iterator of events as they are produced.
    The chat method supports cooperative cancellation and yields events from the driver's stream_generate method.
    """

    def __init__(self, driver: LLMDriver, agent_name: Optional[str] = None, history: Optional[LLMConversationHistory] = None, system_prompt: Optional[str] = None, tools: Optional[List[dict]] = None, **kwargs: Any):
        self._event_lock = threading.Lock()
        self._latest_event = None
        self.driver = driver
        self.agent_name = agent_name or driver.get_name()
        self.state = {}
        self.config = kwargs
        self.history = history if history is not None else LLMConversationHistory()
        self.system_prompt = system_prompt
        if self.system_prompt:
            history_messages = self.history.get_history()
            if not history_messages or history_messages[0].get('role') != 'system':
                self.history.add_message('system', self.system_prompt)
        if tools is None:
            self.tools = ToolRegistry().get_tool_classes()
        else:
            self.tools = tools

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def set_system_using_template(self, template_file: str, **vars) -> None:
        template_path = Path(template_file)
        env = Environment(
            loader=FileSystemLoader(str(template_path.parent)),
            autoescape=select_autoescape(["txt", "j2"]),
        )
        template = env.get_template(template_path.name)
        rendered_prompt = template.render(**vars)
        self.set_system_prompt(rendered_prompt)

    def get_system_prompt(self) -> Optional[str]:
        return self.system_prompt

    def chat(self, prompt: str, role: str = "user", **kwargs: Any) -> Iterator[Any]:
        """
        Start a streaming chat with the LLM driver.
        Returns an iterator that yields events from the driver's stream_generate method as they are produced.
        Supports cooperative cancellation via a threading.Event passed as 'cancel_event' in kwargs.
        The agent's conversation history is updated as events are received.
        """
        from janito.event_bus.queue_bus import QueueEventBus, QueueEventBusSentinel
        from janito.event_bus.bus import event_bus as system_event_bus
        self.history.add_message(role, prompt)
        kwargs.pop('raw', None)
        generate_kwargs = dict(
            conversation_history=self.history,
            system_prompt=self.system_prompt,
            **kwargs
        )
        if self.tools:
            generate_kwargs['tools'] = self.tools
        cancel_event = generate_kwargs.get('cancel_event', None)
        event_iterator = self.driver.stream_generate(**generate_kwargs)
        from janito.driver_events import ContentPartFound
        for event in event_iterator:
            system_event_bus.publish(event)
            # Update conversation history for ContentPartFound
            if isinstance(event, ContentPartFound):
                self.history.add_message("assistant", event.content_part)
            yield event

    def set_latest_event(self, event: str) -> None:
        with self._event_lock:
            self._latest_event = event

    def get_latest_event(self) -> Optional[str]:
        with self._event_lock:
            return self._latest_event

    def get_name(self) -> str:
        return self.agent_name
