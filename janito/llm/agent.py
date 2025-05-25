from janito.llm.driver_input import DriverInput
from janito.llm.driver_config import LLMDriverConfig
from janito.conversation_history import LLMConversationHistory
from janito.tools.tools_adapter import ToolsAdapterBase
from queue import Queue, Empty
from typing import Any, Optional, List, Iterator, Union
import threading
import logging
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pathlib import Path
import time

class LLMAgent:
    _event_lock: threading.Lock
    _latest_event: Optional[str]

    """
    Represents an agent that interacts with an LLM driver to generate responses.
    Maintains conversation history as required by the new driver interface.
    """

    def __init__(self, llm_provider, tools_adapter: ToolsAdapterBase, agent_name: Optional[str] = None, system_prompt: Optional[str] = None, temperature: Optional[float] = None, conversation_history: Optional[LLMConversationHistory] = None, **kwargs: Any):
        self.temperature = temperature
        self._event_lock = threading.Lock()
        self._latest_event = None

        self.llm_provider = llm_provider  # now a provider, not a driver
        self.tools_adapter = tools_adapter
        self.agent_name = agent_name or getattr(llm_provider, 'name', None)
        self.state = {}
        self.config = kwargs

        self.system_prompt = system_prompt
        self.template_vars = {}
        self._system_prompt_template_file = None
        self.tools = self.tools_adapter.get_tools() if self.tools_adapter else []
        # Allow injecting conversation history, default to LLMConversationHistory
        self.conversation_history = conversation_history if conversation_history else LLMConversationHistory()
        # Create driver from provider
        self.driver = self.llm_provider.create_driver()
        self.driver.start()  # Start the driver's input processing thread
        self.input_queue = getattr(self.driver, 'input_queue', None)
        self.output_queue = getattr(self.driver, 'output_queue', None)

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

    def _add_prompt_to_history(self, prompt_or_messages, role):
        if isinstance(prompt_or_messages, str):
            self.conversation_history.add_message(role, prompt_or_messages)
        elif isinstance(prompt_or_messages, list):
            for msg in prompt_or_messages:
                self.conversation_history.add_message(
                    msg.get("role", "user"),
                    msg.get("content", ""),
                    msg.get("metadata", None)
                )

    def _ensure_system_prompt(self):
        if self.system_prompt:
            hist = self.conversation_history.get_history()
            if not hist or hist[0].get('role') != 'system':
                self.conversation_history._history.insert(0, {'role': 'system', 'content': self.system_prompt})

    def _handle_tool_calls(self, tool_calls):
        tool_results = []
        for call in tool_calls:
            tool_name = call['name'] if isinstance(call, dict) and 'name' in call else getattr(call, 'name', None)
            tool_args = call['arguments'] if isinstance(call, dict) and 'arguments' in call else getattr(call, 'arguments', None)
            tool_result = self.tools_adapter.execute_by_name(tool_name, arguments=tool_args)
            tool_results.append({'name': tool_name, 'arguments': tool_args, 'result': tool_result})
            # Extend history with tool call and result
            self.conversation_history.add_message('tool', str({'name': tool_name, 'arguments': tool_args}))
            self.conversation_history.add_message('tool_result', str({'name': tool_name, 'result': tool_result}))
        return tool_results

    def chat(self, prompt_or_messages: Union[str, List[dict]], role: str = "user", **kwargs: Any) -> Iterator[Any]:
        """
        Main agent conversation loop supporting function/tool calls and conversation history extension, matching the latest Janito design:

        - On first user input, sends prompt to the driver, waits for a `ResponseReceived` event.
        - If tool calls are present in the event, executes them using the `tools_adapter` and updates conversation history,
          then sends an updated request to the driver, continuing this process until a response with no tool calls remains.
        - Only yields the final `ResponseReceived` event to downstream consumers (CLI, API, etc.), enabling seamless automation of LLM+tool workflows.
        """
        assert prompt_or_messages is not None, "[ERROR] prompt_or_messages is None in Agent.chat, which is not expected!"
        self._add_prompt_to_history(prompt_or_messages, role)
        self._ensure_system_prompt()
        config = kwargs.get('config')
        if config is None:
            config = self.llm_provider.driver_config
        tool_schema = kwargs.get('tool_schema', None)
        while True:
            driver_input = DriverInput(
                config=config,
                conversation_history=self.conversation_history,
                tool_schema=tool_schema
            )
            self.input_queue.put(driver_input)
            while True:
                try:
                    event = self.output_queue.get(timeout=30)
                except Empty:
                    print("[ERROR] No output from driver in agent.chat()"); return
                # Only respond to ResponseReceived or errors
                event_class = getattr(event, '__class__', None)
                if event_class is not None and event_class.__name__ == 'ResponseReceived':
                    tool_calls = getattr(event, 'tool_calls', [])
                    if tool_calls:
                        self._handle_tool_calls(tool_calls)
                        break
                    else:
                        yield event
                        return
                elif getattr(event, '__class__', None) is not None and event.__class__.__name__ in ('RequestError', 'EmptyResponseEvent'):
                    yield event
                    return

    def set_latest_event(self, event: str) -> None:
        with self._event_lock:
            self._latest_event = event

    def get_latest_event(self) -> Optional[str]:
        with self._event_lock:
            return self._latest_event

    def get_history(self):
        """Get the agent's internal conversation history."""
        return self.conversation_history.get_history()

    def reset_conversation_history(self) -> None:
        """
        Reset/clear the internal conversation history.
        """
        self.conversation_history.clear()

    def get_name(self) -> str:
        return self.agent_name
