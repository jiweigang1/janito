# LLM Drivers Architecture

## Overview

The driver layer in this project provides a unified, event-driven interface for interacting with various Large Language Model (LLM) providers (such as OpenAI, Google Gemini, MistralAI, etc.). Each driver encapsulates the provider-specific logic and exposes a standardized streaming API for generating model outputs.

## Key Concepts

### Streaming, Event-Driven Interface

- All drivers implement the `stream_generate()` method, which yields events as the LLM generates output.
- Drivers emit standardized events (e.g., `GenerationStarted`, `ContentPartFound`, `GenerationFinished`, `RequestError`, etc.) as the generation progresses.

### Threading and Cancellation

- The generation process runs in a background thread, ensuring that the main application/UI remains responsive.
- Cooperative cancellation is supported via a `threading.Event` passed to `stream_generate()`. Consumers can set this event to abort generation early.
- Once cancellation is received (i.e., the event is set), drivers will not execute any new tools or send any new requests to the LLM provider. Ongoing operations will be stopped as soon as possible, ensuring prompt and safe cancellation.

### Consistency and Extensibility

- All drivers inherit from the `LLMDriver` abstract base class and follow the same event and threading conventions.
- Each driver handles provider-specific API calls, tool/function execution, and event emission internally, but always exposes the same external interface.

## Example Usage

```python
import threading
from janito.driver_events import ContentPartFound, GenerationFinished, RequestError

cancel_event = threading.Event()
for event in driver.stream_generate(
    prompt="Tell me a joke.",
    system_prompt="You are a witty assistant.",
    cancel_event=cancel_event
):
    if isinstance(event, ContentPartFound):
        print(event.content_part, end="", flush=True)
    elif isinstance(event, GenerationFinished):
        print("\n[Generation complete]")
    elif isinstance(event, RequestError):
        print(f"\n[Error: {event.error}]")
```

## Supported Events

- `GenerationStarted`: Generation process has begun.
- `ContentPartFound`: A new part (token, sentence, etc.) of the generated content is available.
- `GenerationFinished`: Generation process is complete.
- `RequestStarted`, `RequestFinished`: API request lifecycle events.
- `RequestError`: An error occurred during generation.
- (Provider-specific events may also be emitted.)

## Adding a New Driver

To add support for a new LLM provider:

1. Subclass `LLMDriver`.
2. Implement the `stream_generate()` method, following the event-driven, threaded, and cancellable pattern.
3. Emit standardized events as output is generated.

## Provider-Specific Notes

### Google Gemini (genai) Driver

The Google Gemini driver preserves the exact order of content and tool/function calls as returned by the Gemini API. Events such as `ToolCallStarted`, `ToolCallFinished`, and `ContentPartFound` are published in the sequence they appear in the API response, ensuring that downstream consumers receive events in the true conversational order. This is essential for correct conversational flow and tool execution, especially when tool calls and content are interleaved.

## Design Philosophy

- **Responsiveness:** All generation is non-blocking and can be cancelled at any time.
- **Observability:** Consumers can react to fine-grained events for real-time UIs, logging, or chaining.
- **Simplicity:** A single, modern interface for all drivers.
