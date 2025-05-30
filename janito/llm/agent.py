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

    @property
    def template_vars(self):
        if not hasattr(self, '_template_vars'):
            self._template_vars = {}
        return self._template_vars

    """
    Represents an agent that interacts with an LLM driver to generate responses.
    Maintains conversation history as required by the new driver interface.
    """

    def __init__(self, llm_provider, tools_adapter: ToolsAdapterBase, agent_name: Optional[str] = None, system_prompt: Optional[str] = None, temperature: Optional[float] = None, conversation_history: Optional[LLMConversationHistory] = None, input_queue: Queue = None, output_queue: Queue = None, verbose_agent: bool = False, **kwargs: Any):
        self.llm_provider = llm_provider
        self.tools_adapter = tools_adapter
        self.agent_name = agent_name
        self.system_prompt = system_prompt
        self.temperature = temperature
        self.conversation_history = conversation_history or LLMConversationHistory()
        self.input_queue = input_queue if input_queue is not None else Queue()
        self.output_queue = output_queue if output_queue is not None else Queue()
        self._event_lock = threading.Lock()
        self._latest_event = None
        self.verbose_agent = verbose_agent

    def set_template_var(self, key: str, value: str) -> None:
        """Set a variable for system prompt templating."""
        if not hasattr(self, '_template_vars'):
            self._template_vars = {}
        self._template_vars[key] = value

    def set_system_prompt(self, prompt: str) -> None:
        self.system_prompt = prompt

    def set_system_using_template(self, template_path: str, **kwargs) -> None:
        env = Environment(
            loader=FileSystemLoader(Path(template_path).parent),
            autoescape=select_autoescape()
        )
        template = env.get_template(Path(template_path).name)
        self.system_prompt = template.render(**kwargs)

    def _refresh_system_prompt_from_template(self):
        if hasattr(self, '_template_vars') and hasattr(self, 'system_prompt_template'):
            env = Environment(
                loader=FileSystemLoader(Path(self.system_prompt_template).parent),
                autoescape=select_autoescape()
            )
            template = env.get_template(Path(self.system_prompt_template).name)
            self.system_prompt = template.render(**self._template_vars)

    def get_system_prompt(self) -> str:
        return self.system_prompt

    def _add_prompt_to_history(self, prompt_or_messages, role):
        if isinstance(prompt_or_messages, str):
            self.conversation_history.add_message(role, prompt_or_messages)
        elif isinstance(prompt_or_messages, list):
            for msg in prompt_or_messages:
                self.conversation_history.add_message(msg.get('role', role), msg.get('content', ''))

    def _ensure_system_prompt(self):
        if self.system_prompt and (not self.conversation_history._history or self.conversation_history._history[0]['role'] != 'system'):
            self.conversation_history._history.insert(0, {'role': 'system', 'content': self.system_prompt})

    def _validate_and_update_history(self, prompt: str = None, messages: Optional[List[dict]] = None, role: str = "user"):
        if prompt is None and not messages:
            raise ValueError("Either prompt or messages must be provided to Agent.chat.")
        if prompt is not None:
            self._add_prompt_to_history(prompt, role)
        elif messages:
            self._add_prompt_to_history(messages, role)

    def _log_event_verbose(self, event):
        if getattr(self, 'verbose_agent', False):
            if hasattr(event, 'parts'):
                for i, part in enumerate(getattr(event, 'parts', [])):
                    pass  # Add detailed logging here if needed
            else:
                pass  # Add detailed logging here if needed

    def _handle_event_type(self, event, bus):
        event_class = getattr(event, '__class__', None)
        if event_class is not None and event_class.__name__ == 'ResponseReceived':
            should_continue = self._handle_response_received(event)
            return event, should_continue
        elif getattr(event, '__class__', None) is not None and event.__class__.__name__ in ('RequestError', 'EmptyResponseEvent'):
            return event, False
        return None

    def _prepare_driver_input(self, config):
        return DriverInput(
            config=config,
            conversation_history=self.conversation_history
        )

    def _process_events(self, bus: Queue = None, poll_timeout: float = 1.0, max_wait_time: float = 30.0):
        """
        Wait for events from the output queue with a small polling timeout to allow KeyboardInterrupt interception.
        Tracks elapsed time and returns an error if no events are received within max_wait_time seconds.
        """
        elapsed = 0.0
        try:
            while True:
                try:
                    event = self.output_queue.get(timeout=poll_timeout)
                except Empty:
                    elapsed += poll_timeout
                    if elapsed >= max_wait_time:
                        error_msg = f"[ERROR] No output from driver in agent.chat() after {max_wait_time} seconds"
                        if bus:
                            bus.put(error_msg)
                        print(error_msg)
                        return None
                    continue
                # Reset elapsed time on successful event
                elapsed = 0.0
                # Publish every event to the bus if provided
                if bus:
                    bus.put(event)
                self._log_event_verbose(event)
                result = self._handle_event_type(event, bus)
                if result is not None:
                    return result
        except KeyboardInterrupt:
            print("[INFO] KeyboardInterrupt received. Exiting event loop.")
            if bus:
                bus.put("[INFO] KeyboardInterrupt received. Exiting event loop.")
            return None

    def _handle_response_received(self, event) -> bool:
        """
        Handle a ResponseReceived event: execute tool calls if present, update history.
        Returns True if the agent loop should continue (tool calls found), False otherwise.
        """
        if getattr(self, 'verbose_agent', False):
            print("[agent] [INFO] Handling ResponseReceived event.")
        from janito.llm.message_parts import FunctionCallMessagePart
        tool_calls = []
        tool_results = []
        for part in event.parts:
            if isinstance(part, FunctionCallMessagePart):
                tool_calls.append(part)
                result = self.tools_adapter.execute_function_call_message_part(part)
                tool_results.append(result)
        if tool_calls:
            # For each tool call, add a function message with the tool result
            for call, result in zip(tool_calls, tool_results):
                function_name = getattr(call, 'name', 'function')
                # Add as role 'function' with name in metadata if available
                self.conversation_history.add_message('function', str(result), metadata={'name': function_name})
            return True  # Continue the loop
        else:
            return False  # No tool calls, return event

    def chat(self, prompt: str = None, messages: Optional[List[dict]] = None, role: str = "user", bus: Queue = None, config=None):
        """
        Main agent conversation loop supporting function/tool calls and conversation history extension, now as a blocking event-driven loop with event publishing.

        Args:
            prompt: The user prompt as a string (optional if messages is provided).
            messages: A list of message dicts (optional if prompt is provided).
            role: The role for the prompt (default: 'user').
            bus: Optional Queue to which all events will be published.
            config: Optional driver config (defaults to provider config).

        Returns:
            The final ResponseReceived event (or error event) when the conversation is complete.
        """
        self._validate_and_update_history(prompt, messages, role)
        self._ensure_system_prompt()
        if config is None:
            config = self.llm_provider.driver_config
        loop_count = 1
        while True:
            # DEBUG: Print conversation history before sending to driver
            if getattr(self, 'verbose_agent', False):
                for msg in self.conversation_history.get_history():
                    print("   ", msg)
            driver_input = self._prepare_driver_input(config)
            self.input_queue.put(driver_input)
            result, should_continue = self._process_events(bus)
            if result is None:
                return None
            if not should_continue:
                return result
            # Otherwise, continue loop (for tool calls)
            loop_count += 1

    def set_latest_event(self, event: str) -> None:
        with self._event_lock:
            self._latest_event = event

    def get_latest_event(self) -> Optional[str]:
        with self._event_lock:
            return self._latest_event

    def get_history(self) -> LLMConversationHistory:
        """Get the agent's interaction history."""
        return self.conversation_history

    def reset_conversation_history(self) -> None:
        """Reset/clear the interaction history."""
        self.conversation_history = LLMConversationHistory()

    def get_name(self) -> Optional[str]:
        return self.agent_name
