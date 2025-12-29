"""LangGraph agent implementation for Planck AI"""
import os
import json
import asyncio
from typing import Dict, Any, AsyncGenerator, Literal
from datetime import datetime

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import httpx
import google.generativeai as genai

from .state import AgentState, StreamingChunk
from .prompts import SYSTEM_PROMPT
from tools.web_search import web_search_tool, WEB_SEARCH_TOOL_DEF
from tools.code_executor import code_executor_tool, CODE_EXECUTOR_TOOL_DEF
from tools.image_analyzer import image_analyzer_tool, IMAGE_ANALYZER_TOOL_DEF
from tools.document_reader import document_reader_tool, DOCUMENT_READER_TOOL_DEF
from tools.thinking import thinking_tool, THINKING_TOOL_DEF


# Tool definitions for the model

# Tools allowed in Web Search Mode
TOOLS = [
    THINKING_TOOL_DEF,
    WEB_SEARCH_TOOL_DEF,
    CODE_EXECUTOR_TOOL_DEF,
    IMAGE_ANALYZER_TOOL_DEF,
    DOCUMENT_READER_TOOL_DEF
]

# Tools allowed in Chat Mode (No Web Search)
CHAT_TOOLS = [
    THINKING_TOOL_DEF,
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
        self.token = os.getenv("GITHUB_TOKEN")
        # Upgrade to GPT-4o for larger context (128k) and better reasoning
        self.model = "gpt-4o-mini" 
        self.api_url = "https://models.inference.ai.azure.com/chat/completions"
        
        # Google Gemini Setup
        self.google_api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if self.google_api_key:
            genai.configure(api_key=self.google_api_key)
        
    async def _call_google_llm(
        self,
        messages: list,
        tools: list = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Call Google Gemini API via SDK.
        Adapts the OpenAI-style messages to Gemini format.
        """
        if not self.google_api_key:
             raise Exception("GEMINI_API_KEY not found in environment variables.")

        # Map model name
        # User asks for "Gemini 2.5 Flash Lite" -> we map to "gemini-2.0-flash-exp" or "gemini-1.5-flash"
        # Ideally, use the model name passed or a default safe one.
        target_model = self.model if "gemini" in self.model else "gemini-2.0-flash-exp"
        
        # Configure model
        # Google tools format is different, but the SDK handles FunctionDeclaration if we convert.
        # However, for simplicity and robustness, we will use the SDK's automatic conversion if possible,
        # or just pass the tools if they are compatible.
        # The 'tools' argument here is a list of dicts (OpenAI format).
        # We need to convert OpenAI tool definitions to Google's.
        
        google_tools = []
        if tools:
            # Simple conversion or just pass the function if we had the raw function.
            # Since we only have the JSON schema here, we might need a converter.
            # OPTION: For this specific agent, we have the functions imported!
            # We can re-bind them.
            # But the 'tools' arg passed to _call_llm is the JSON schema list.
            # Let's import the actual tool functions to bind them if needed OR use the schema.
            # Google SDK genai.GenerativeModel(tools=[...]) accepts functions.
            
            # Re-map known tools from the schemas passed
            # This is a bit hacky but ensures compatibility without writing a schema converter.
            from tools.web_search import web_search_tool
            from tools.code_executor import code_executor_tool
            from tools.image_analyzer import image_analyzer_tool
            from tools.document_reader import document_reader_tool
            from tools.thinking import thinking_tool
            
            known_tools_map = {
                "web_search": web_search_tool,
                "code_executor": code_executor_tool,
                "image_analyzer": image_analyzer_tool,
                "document_reader": document_reader_tool,
                "thinking": thinking_tool
            }
            
            for t in tools:
                name = t["function"]["name"]
                if name in known_tools_map:
                    google_tools.append(known_tools_map[name])
        
        # Helper to convert messages
        gemini_history = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg.get("content")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                gemini_history.append({"role": "user", "parts": [content]})
            elif role == "assistant":
                # Handle tool calls in history if present (complex)
                # For now, simplistic text history
                if content:
                    gemini_history.append({"role": "model", "parts": [content]})
            elif role == "tool":
                 # Gemini handles tool results differently in history
                 # ignoring purely text based reconstruction for now to avoid errors
                 pass

        model = genai.GenerativeModel(
            model_name=target_model,
            system_instruction=system_instruction,
            tools=google_tools if google_tools else None
        )
        
        # Start chat session
        chat = model.start_chat(history=gemini_history[:-1] if gemini_history else [])
        
        # Send last message
        last_msg = gemini_history[-1]["parts"][0] if gemini_history else "Hello"
        
        # Generation config
        generation_config = genai.types.GenerationConfig(
            candidate_count=1,
            max_output_tokens=60000, # User requested exactly 60k limit
            temperature=0.7
        )
        
        try:
            response = await chat.send_message_async(last_msg, stream=True, generation_config=generation_config)
            
            async for chunk in response:
                # Check for function calls
                # Gemini chunks might contain function calls OR text
                
                # Map to OpenAI format for the frontend/agent loop to consume consistently
                # 1. Text
                if chunk.text:
                     yield {
                         "choices": [{
                             "delta": {"content": chunk.text},
                             "finish_reason": None
                         }]
                     }
                
                # 2. Function calls
                for part in chunk.parts:
                    if fn := part.function_call:
                        call_id = f"call_{uuid.uuid4().hex[:8]}"
                        yield {
                            "choices": [{
                                "delta": {
                                    "tool_calls": [{
                                        "index": 0,
                                        "id": call_id,
                                        "type": "function",
                                        "function": {
                                            "name": fn.name,
                                            "arguments": json.dumps(dict(fn.args))
                                        }
                                    }]
                                },
                                 "finish_reason": "tool_calls"
                            }]
                        }
        except Exception as e:
            # Check for Rate Limit (ResourceExhausted 429)
            if "429" in str(e) or "ResourceExhausted" in str(e) or "quota" in str(e).lower():
                 # Default to 60s wait if we can't parse it, as Google often doesn't give a retry-after header in the exception message
                 raise Exception(f"API Rate Limit Hit. Retrying allowed in: 60s")
            raise e

    async def _call_llm(
        self,
        messages: list,
        tools: list = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Call the LLM API.
        
        Supports both streaming and non-streaming requests.
        Handles API authentication, payload construction, and rate limit errors (429).
        """
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            # GPT-4o supports 128k context. We can be generous.
            # But the output token limit is still 4096.
            "max_tokens": 4096,
            "temperature": 0.7,
        }
        
        if tools:
            payload["tools"] = [{"type": "function", "function": t} for t in tools]
            payload["tool_choice"] = "auto"
            
        if stream:
            payload["stream"] = True
            
        async with httpx.AsyncClient(timeout=120.0) as client:
            if stream:
                async with client.stream("POST", self.api_url, headers=headers, json=payload) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            data = line[6:]
                            if data == "[DONE]":
                                break
                            try:
                                yield json.loads(data)
                            except json.JSONDecodeError:
                                continue
                                
                    # Check final headers if available (httpx stream context)
                    # Note: httpx stream() context manager handles response.
                    if response.status_code == 429:
                         retry_after = response.headers.get("Retry-After")
                         wait_time = int(retry_after) if retry_after else 60
                         raise Exception(f"API Rate Limit Hit. Retrying allowed in: {wait_time}s")

            else:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                # Check for rate limit headers
                self._update_rate_limits(response.headers)
                
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    reset_time = response.headers.get("x-ratelimit-reset-requests")
                    
                    wait_time = 0
                    if retry_after:
                        wait_time = int(retry_after)
                    elif reset_time:
                        try:
                            wait_time = float(reset_time)
                        except (ValueError, TypeError):
                            wait_time = 60 # Default fallback
                            
                    # Format for frontend parsing
                    raise Exception(f"API Rate Limit Hit. Retrying allowed in: {wait_time}s")
                    
                if response.status_code != 200:
                    raise Exception(f"API error: {response.status_code} - {response.text}")
                yield response.json()

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
        model_name: str = "gpt-4o-mini",
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
        
        # Set model for this run
        self.model = model_name
        

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
        # 8k tokens ~= 32k chars. We use 30k to be safe for Azure/Github.
        # Gemini 2.0 Flash supports 1M, but user requested limit to 100k tokens.
        # 100k tokens ~= 400,000 chars.
        if "gemini" in self.model:
            MAX_HISTORY_CHARS = 400000 
        else:
            MAX_HISTORY_CHARS = 30000
            
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
        
        # Yield thinking start
        yield StreamingChunk(
            type="thinking",
            content="Analyzing your request...",
            metadata={"step": "start"}
        )
        
        max_iterations = 15
        iteration = 0
        
        try:
            while iteration < max_iterations:
                iteration += 1
                
                # Call LLM
                response = None
                
                if "gemini" in self.model.lower():
                     # Use Google Gemini
                     # Note: Our _call_google_llm is a generator yielding chunks (OpenAI stream style)
                     # But the logic below expects a single response object because stream=False was passed originally
                     # or it iterates if stream=True. 
                     # The original code here used stream=False for _call_llm but the architecture is chunk-based yield?
                     # Wait, line 293 says stream=False.
                     # But _call_llm implementation uses aiter_lines if stream=True.
                     # The loop "async for chunk in self._call_llm... break" suggests it gets one chunk and breaks? 
                     # No, stream=False returns a generator yielding one JSON? 
                     # Let's look at lines 114 and 134 in original: yields response.json() once.
                     
                     # We need to adapt Gemini connection to this
                     # For simplicity, let's just create a non-streaming wrapper or adapter here if needed.
                     # Actually, let's just branch logic.
                     
                     # Implementation detail: The original agent loop expects "response" = full JSON object
                     # OR it expects chunks? 
                     # "async for chunk in ... break" -> It takes the FIRST chunk and treats it as the full response?
                     # Line 301: choice = response["choices"][0]
                     # So it expects a full completion object.
                     
                     # Let's make a synced_call_google equivalent
                     # Or just gather the stream.
                     
                     final_content = ""
                     final_tool_calls = []
                     
                     async for chunk in self._call_google_llm(messages, active_tools):
                         # Aggregate
                         choice = chunk["choices"][0]
                         delta = choice.get("delta", {})
                         if "content" in delta and delta["content"]:
                             final_content += delta["content"]
                         if "tool_calls" in delta:
                             # OpenAI streams tool calls in parts, typically
                             # My Google adapter yields full tool calls at once for simplicity
                             final_tool_calls.extend(delta["tool_calls"])
                             
                     # Construct pseudo-response object
                     message_obj = {"role": "assistant"}
                     if final_content:
                         message_obj["content"] = final_content
                     if final_tool_calls:
                         message_obj["tool_calls"] = final_tool_calls
                         # Normalize arguments if they are objects (Gemini) vs strings (OpenAI)
                         # My adapter dumped them as json strings, so it matches OpenAI.
                         
                     response = {
                         "choices": [
                             {
                                 "message": message_obj,
                                 "finish_reason": "stop" if not final_tool_calls else "tool_calls"
                             }
                         ]
                     }
                     
                else:
                    # Default Azure/OpenAI
                    async for chunk in self._call_llm(messages, tools=active_tools, stream=False):
                        response = chunk
                        break
                    
                if not response:
                    yield StreamingChunk(type="error", content="Failed to get LLM response", metadata=None)
                    return
                    
                choice = response["choices"][0]
                message = choice["message"]
                
                # Check for tool calls
                tool_calls = message.get("tool_calls", [])
                
                if tool_calls:
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
                        
                        # Add to messages
                        messages.append({
                            "role": "assistant",
                            "content": None,
                            "tool_calls": [{
                                "id": tool_call["id"],
                                "type": "function",
                                "function": func
                            }]
                        })
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call["id"],
                            "content": result
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
