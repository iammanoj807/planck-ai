"""Agent state management for LangGraph"""
from typing import TypedDict, Annotated, Sequence, Optional, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator


class AgentState(TypedDict):
    """State maintained throughout the agent execution"""
    # Conversation messages
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Current step in reasoning
    current_step: str
    
    # Tool calls history for visualization
    tool_history: List[Dict[str, Any]]
    
    # Uploaded files (images, PDFs)
    files: List[Dict[str, str]]
    
    # Conversation ID for memory
    conversation_id: str
    
    # Final response flag
    is_complete: bool
    
    # Error state
    error: Optional[str]


class ToolCall(TypedDict):
    """Structure for a tool call"""
    tool_name: str
    tool_input: Dict[str, Any]
    tool_output: Optional[str]
    timestamp: str
    duration_ms: int


class StreamingChunk(TypedDict):
    """Structure for streaming response chunks"""
    type: str  # 'thinking', 'tool_call', 'tool_result', 'response', 'error'
    content: str
    metadata: Optional[Dict[str, Any]]
