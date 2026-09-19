from dotenv import load_dotenv
load_dotenv()
"""LangGraph agent implementation for Planck AI"""
import os
import json
import asyncio
from typing import Dict, Any, AsyncGenerator, Literal, Optional, List
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import httpx

from .state import AgentState, StreamingChunk
from .prompts import SYSTEM_PROMPT
from .providers import LLMProvider, RateLimitError, create_provider, get_available_providers
from tools.web_search import web_search_tool, WEB_SEARCH_TOOL_DEF
from tools.code_executor import code_executor_tool, CODE_EXECUTOR_TOOL_DEF
from tools.image_analyzer import image_analyzer_tool, IMAGE_ANALYZER_TOOL_DEF
from tools.document_reader import document_reader_tool, DOCUMENT_READER_TOOL_DEF
from tools.thinking import thinking_tool


# Tool definitions for the model

# Tools allowed in Web Search Mode
# NOTE: thinking tool removed - it cost a full extra LLM round trip per question.
# The models reason natively; that reasoning is surfaced as the "thinking" step instead.
TOOLS = [
    WEB_SEARCH_TOOL_DEF,
    CODE_EXECUTOR_TOOL_DEF,
    IMAGE_ANALYZER_TOOL_DEF,
    DOCUMENT_READER_TOOL_DEF
]

# Tools allowed in Chat Mode (No Web Search)
CHAT_TOOLS = [
    CODE_EXECUTOR_TOOL_DEF,
    IMAGE_ANALYZER_TOOL_DEF,
    DOCUMENT_READER_TOOL_DEF
]


class AgentRunner:
    """
    Runs the agent loop with tool execution and streaming.

    This class manages:
    1. Communication with the LLM API (Azure OpenAI / GitHub Models).
    2. Dynamic context window resizing based on model selection.
    3. Tool execution processing.
    4. Streaming responses back to the caller in chunks.
    """

    def __init__(self):
        # Providers in priority order: Groq first, then Gemini and NVIDIA as fallbacks.
        # Each is enabled by its <NAME>_API_KEY; <NAME>_MODEL optionally overrides the default model.
        self.providers: List[LLMProvider] = []
        self.provider_names: List[str] = []

        for name in get_available_providers():
            api_key = os.getenv(f"{name.upper()}_API_KEY")
            if not api_key:
                continue
            provider = create_provider(name, api_key, model=os.getenv(f"{name.upper()}_MODEL"))
            self.providers.append(provider)
            self.provider_names.append(name)
            print(f"DEBUG: Initialized {name} provider ({provider.model})")

        if not self.providers:
            raise Exception("No LLM providers configured. Please set at least one of: GROQ_API_KEY, GEMINI_API_KEY, NVIDIA_API_KEY")

    async def _call_llm_with_fallback(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Call providers in priority order, moving on to the next one immediately when one fails.

        Every call starts from the primary provider. If all of them fail we make one more pass,
        pausing first only when every provider was rate limited (capped so the user isn't
        left waiting for long).
        """
        last_error = None
        for attempt in range(2):
            retry_waits = []
            for provider, name in zip(self.providers, self.provider_names):
                try:
                    print(f"DEBUG: Attempting LLM call with {name} provider")
                    return await provider.generate(messages, tools=tools)
                except RateLimitError as e:
                    print(f"INFO: {name} hit rate limit, trying next provider...")
                    retry_waits.append(e.retry_after or 5)
                    last_error = e
                except Exception as e:
                    print(f"WARNING: {name} provider failed: {e}")
                    last_error = e

            all_rate_limited = len(retry_waits) == len(self.providers)
            if attempt == 0 and all_rate_limited:
                wait_time = min(min(retry_waits), 15)
                print(f"INFO: All providers rate limited, waiting {wait_time:.0f}s before retrying")
                await asyncio.sleep(wait_time)

        if all_rate_limited:
            raise Exception(f"All AI providers are rate limited. Please wait {min(retry_waits):.0f}s and try again.")
        raise Exception(f"All LLM providers failed. Last error: {last_error}")

    def _update_rate_limits(self, headers: Dict[str, str]):
        """Update cached rate limits from headers."""
        # Simple extraction for logging/debugging if needed
        # We focus on the 429 handling above for now
        pass

    async def _execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> str:
        """
        Execute a tool by name and return the string result.
        Maps the tool name string to the actual tool function.
        """
        if tool_name == "web_search":
            return await web_search_tool(**tool_input)
        elif tool_name == "code_executor":
            return code_executor_tool(**tool_input)
        elif tool_name == "image_analyzer":
            return await image_analyzer_tool(**tool_input)
        elif tool_name == "document_reader":
            return await document_reader_tool(**tool_input)
        elif tool_name == "thinking":
            return thinking_tool(**tool_input)
        else:
            return json.dumps({"error": f"Unknown tool: {tool_name}"})

    async def run(
        self,
        user_message: str,
        conversation_history: list = None,
        files: list = None,
        model_name: str = "gemini-3.6-flash",
        mode: str = "web",
        language: str = "English"
    ) -> AsyncGenerator[StreamingChunk, None]:
        """
        Run the agent loop (Thinking -> Tool Use -> Final Response).

        Args:
            user_message: The current query from the user.
            conversation_history: List of previous messages for context.
            files: List of uploaded files (images, PDFs) to process.
            model_name: The backend model to use ('gpt-4o' or 'gpt-4o-mini').
            mode: 'web' (default) or 'chat' (no tools).

        Yields:
            StreamingChunk objects representing partial updates (thinking, tool usage, tokens).
        """

        # Set model for this run — using Groq-hosted models with tool calling support
        if model_name in ["gpt-4o-mini", "mini", "gemini-3.6-flash", "openai/gpt-oss-20b"]:
            self.model = "openai/gpt-oss-20b"
        else:
            self.model = "openai/gpt-oss-120b"


        # Select prompt and tools based on mode
        if mode == "chat":
            from .prompts import CHAT_SYSTEM_PROMPT
            system_prompt = CHAT_SYSTEM_PROMPT
            active_tools = CHAT_TOOLS # Enable file tools only
        else:
            system_prompt = SYSTEM_PROMPT
            active_tools = TOOLS

        # Build messages
        formatted_system_prompt = system_prompt.format(
            current_date=datetime.now().strftime("%A, %B %d, %Y")
        )

        # Append Language Instruction
        if language and language != "English":
            formatted_system_prompt += f"\n\nIMPORTANT: You must respond in {language}. Translate your internal reasoning if necessary, but the final output must be in {language}."
            print(f"DEBUG: Injected Language Instruction for '{language}'")

        messages = [{"role": "system", "content": formatted_system_prompt}]

        # Smart Context Management
        # Dynamic limit based on model capacity
        # Github Models Free Tier has a strict 8k token limit for ALL models
        # 8k tokens ~= 32k chars. We use 30k to be safe.
        MAX_HISTORY_CHARS = 8000  # Keep context small to stay within 8000 TPM

        current_chars = 0
        selected_history = []

        if conversation_history:
            # Iterate backwards to keep most recent first
            for msg in reversed(conversation_history):
                content = msg.get("content") or ""

                # Truncate extremely long individual text messages
                if content and len(content) > 2000:
                    content = content[:2000] + "... [truncated]"

                # Estimate size (including tool call overhead)
                msg_len = len(content) + 200 # Buffer for metadata

                if current_chars + msg_len > MAX_HISTORY_CHARS:
                    # Soft limit hit - stop adding history
                    break

                # Reconstruct message preserving CRITICAL fields for API validity
                clean_msg = {
                    "role": msg["role"],
                    "content": content
                }
                if "tool_calls" in msg:
                    clean_msg["tool_calls"] = msg["tool_calls"]
                if "tool_call_id" in msg:
                    clean_msg["tool_call_id"] = msg["tool_call_id"]
                if "name" in msg:
                    clean_msg["name"] = msg["name"]

                selected_history.insert(0, clean_msg)
                current_chars += msg_len

        # SAFETY: Ensure history doesn't start with a 'tool' result (orphan)
        # API requires: User/System -> Assistant -> Tool -> Assistant ...
        # If we cut in the middle, we might start with 'tool'.
        while selected_history and selected_history[0].get("role") == "tool":
            selected_history.pop(0)

        # Add trimmed history to messages
        messages.extend(selected_history)

        # Add file context if any
        file_context = ""
        if files:
            for f in files:
                if f.get("type") == "image":
                    file_context += f"\n[Image uploaded: {f.get('name', 'image')}]"
                elif f.get("type") == "pdf":
                    file_context += f"\n[PDF uploaded: {f.get('name', 'document.pdf')} (Path: {f.get('path')})]"

        # Add user message
        full_message = user_message
        if file_context:
            full_message = f"{file_context}\n\n{user_message}"

        # Reinforce language instruction in the user message itself (for stronger adherence)
        if language and language != "English":
            full_message += f"\n\n(IMPORTANT: Please provide your final response in {language}. Ignore the language of search results.)"

        messages.append({"role": "user", "content": full_message})

        # No upfront "thinking" chunk: the frontend shows its own placeholder while loading,
        # and the model's real reasoning is emitted as the thinking step below (one row, not two)

        max_iterations = 8
        iteration = 0

        try:
            while iteration < max_iterations:
                iteration += 1

                # On the last step, withhold tools so the model answers with what it has
                # instead of searching forever and ending with no answer
                final_step = iteration == max_iterations
                if final_step:
                    messages.append({"role": "user", "content": "(Step limit reached. Answer now using only the information above.)"})

                # Call LLM
                response = await self._call_llm_with_fallback(messages, tools=None if final_step else active_tools)

                choice = response["choices"][0]
                message = choice["message"]

                # Show the model's native reasoning (gpt-oss returns it) as the thinking step
                reasoning = message.get("reasoning") or message.get("reasoning_content")
                if iteration == 1 and isinstance(reasoning, str) and reasoning.strip():
                    yield StreamingChunk(
                        type="tool_call",
                        content="Using thinking...",
                        metadata={"tool": "thinking", "input": {"thought": reasoning}}
                    )
                    yield StreamingChunk(
                        type="tool_result",
                        content="Thought logged.",
                        metadata={"tool": "thinking", "duration_ms": 0, "full_result": "Thought logged."}
                    )

                # Check for tool calls
                tool_calls = message.get("tool_calls") or []

                if tool_calls:
                    # Keep only fields every provider accepts (plus Gemini's thought_signature in
                    # extra_content) so a fallback provider can pick up this conversation mid-run
                    messages.append({
                        "role": "assistant",
                        "content": message.get("content"),
                        "tool_calls": [
                            {key: value for key, value in tool_call.items() if key in ("id", "type", "function", "extra_content")}
                            for tool_call in tool_calls
                        ]
                    })

                    # Process each tool call
                    for tool_call in tool_calls:
                        func = tool_call["function"]
                        tool_name = func["name"]
                        tool_input = json.loads(func["arguments"])

                        # Yield tool call info
                        yield StreamingChunk(
                            type="tool_call",
                            content=f"Using {tool_name}...",
                            metadata={
                                "tool": tool_name,
                                "input": tool_input
                            }
                        )

                        # Execute tool
                        start_time = datetime.now()
                        result = await self._execute_tool(tool_name, tool_input)
                        duration = (datetime.now() - start_time).total_seconds() * 1000

                        # Yield tool result
                        yield StreamingChunk(
                            type="tool_result",
                            content=result[:500] + "..." if len(result) > 500 else result,
                            metadata={
                                "tool": tool_name,
                                "duration_ms": int(duration),
                                "full_result": result
                            }
                        )

                        # Add tool result message
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": str(result)
                        })
                else:
                    # No tool calls, this is the final response
                    content = message.get("content", "")

                    yield StreamingChunk(
                        type="response",
                        content=content,
                        metadata={"finish_reason": choice.get("finish_reason")}
                    )
                    return

            # Max iterations reached
            yield StreamingChunk(
                type="response",
                content="I've reached the maximum number of steps. Here's what I found so far based on my analysis.",
                metadata={"max_iterations_reached": True}
            )

        except Exception as e:
            # Catch rate limit and other errors, yield as error chunk
            yield StreamingChunk(
                type="error",
                content=str(e),
                metadata={"error_type": type(e).__name__}
            )


# Singleton instance
agent_runner = AgentRunner()