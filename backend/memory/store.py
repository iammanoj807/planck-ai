"""Conversation memory store using ChromaDB"""
import chromadb
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import uuid


class ConversationMemory:
    """Manages conversation history and context using ChromaDB."""
    
    def __init__(self, persist_directory: str = "./data/memory"):
        """Initialize the memory store."""
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Collection for conversation messages
        self.messages_collection = self.client.get_or_create_collection(
            name="messages",
            metadata={"description": "Conversation messages"}
        )
        
        # Collection for conversation metadata
        self.conversations_collection = self.client.get_or_create_collection(
            name="conversations",
            metadata={"description": "Conversation metadata"}
        )
        
    def create_conversation(self, title: str = "New Conversation") -> str:
        """Create a new conversation and return its ID."""
        conversation_id = str(uuid.uuid4())
        
        self.conversations_collection.add(
            ids=[conversation_id],
            documents=[title],
            metadatas=[{
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "message_count": 0
            }]
        )
        
        return conversation_id
        
    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Add a message to a conversation."""
        message_id = str(uuid.uuid4())
        
        msg_metadata = {
            "conversation_id": conversation_id,
            "role": role,
            "timestamp": datetime.now().isoformat(),
        }
        # Merge additional metadata if provided
        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    msg_metadata[k] = v
                elif isinstance(v, (list, dict)):
                    # Serialize complex types as JSON strings
                    msg_metadata[k] = json.dumps(v)
        
        self.messages_collection.add(
            ids=[message_id],
            documents=[content],
            metadatas=[msg_metadata]
        )
        
        return message_id
        
    def get_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get messages for a conversation."""
        results = self.messages_collection.get(
            where={"conversation_id": conversation_id},
            include=["documents", "metadatas"]
        )
        
        messages = []
        if results["ids"]:
            for i, msg_id in enumerate(results["ids"]):
                msg_metadata = results["metadatas"][i]
                
                # Deserialize JSON-serialized metadata
                tool_calls = []
                if "tool_calls" in msg_metadata:
                    try:
                        tool_calls = json.loads(msg_metadata["tool_calls"])
                    except (json.JSONDecodeError, TypeError):
                        pass
                
                messages.append({
                    "id": msg_id,
                    "content": results["documents"][i],
                    "role": msg_metadata.get("role", "user"),
                    "timestamp": msg_metadata.get("timestamp"),
                    "model": msg_metadata.get("model"),
                    "toolCalls": tool_calls,
                    "metadata": msg_metadata
                })
                
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))

        # Post-processing: Merge ToolMessage outputs into the parent AIMessage's tool_calls
        # This is critical for the frontend to display results in the ReasoningPanel
        # instead of as separate messages.
        
        final_messages = []
        message_map = {msg["id"]: msg for msg in messages}
        
        # We need to map tool_call_id to the message that generated it
        tool_call_map = {} # tool_call_id -> (message_index, tool_call_index)
        
        for i, msg in enumerate(messages):
            if msg.get("toolCalls"):
                for tc_index, tc in enumerate(msg["toolCalls"]):
                    if "id" in tc:
                        tool_call_map[tc["id"]] = (i, tc_index)
            
            # If it's a ToolMessage (role='tool'), try to merge it back
            if msg.get("role") == "tool":
                # Find the parent tool call
                # Note: ToolMessages usually store tool_call_id in metadata or we need to look it up
                # Our current add_message doesn't explicitly store tool_call_id in top-level metadata
                # likely it's inside the 'metadata' dict if LangGraph saved it.
                
                # Check metadata for tool_call_id
                meta = msg.get("metadata", {})
                tool_call_id = meta.get("tool_call_id")
                
                # If not in metadata, usually the artifact/output is the content
                # But we need the ID to link it.
                # If LangChain saves it, it's usually in `tool_call_id` key.
                
                if tool_call_id and tool_call_id in tool_call_map:
                    parent_idx, tc_idx = tool_call_map[tool_call_id]
                    parent_msg = messages[parent_idx]
                    
                    # Update the result in the parent message
                    if "toolCalls" in parent_msg:
                        # Ensure we don't overwrite if it's already there (unlikely for history)
                        # Parse the content (it might be JSON string from code_executor)
                        result_content = msg["content"]
                        try:
                            # If the result is a JSON string (like code_executor returns), parse it
                            # to avoid double-encoding in the frontend
                            if isinstance(result_content, str) and (result_content.strip().startswith('{') or result_content.strip().startswith('[')):
                                # Try parsing, if fails keep as string
                                parsed = json.loads(result_content)
                                # If it's code executor result, we definitively want the parsed object
                                # so ReasoningPanel can access .stdout, .stderr
                                result_content = parsed
                        except:
                            pass
                            
                        parent_msg["toolCalls"][tc_idx]["result"] = result_content
                        parent_msg["toolCalls"][tc_idx]["status"] = "complete" 
                        
                # We do NOT add ToolMessages to final_messages as they are now merged
                continue

            final_messages.append(msg)
        
        return final_messages[-limit:]
        
    def get_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of conversations."""
        results = self.conversations_collection.get(
            include=["documents", "metadatas"]
        )
        
        conversations = []
        if results["ids"]:
            for i, conv_id in enumerate(results["ids"]):
                conversations.append({
                    "id": conv_id,
                    "title": results["documents"][i],
                    "created_at": results["metadatas"][i].get("created_at"),
                    "updated_at": results["metadatas"][i].get("updated_at"),
                    "message_count": results["metadatas"][i].get("message_count", 0)
                })
                
        # Sort by updated_at descending
        conversations.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        return conversations[:limit]
        
    def delete_conversation(self, conversation_id: str) -> bool:
        """Delete a conversation and all its messages."""
        try:
            # Delete messages
            messages = self.messages_collection.get(
                where={"conversation_id": conversation_id}
            )
            if messages["ids"]:
                self.messages_collection.delete(ids=messages["ids"])
                
            # Delete conversation
            self.conversations_collection.delete(ids=[conversation_id])
            
            return True
        except Exception:
            return False
            
    def search_messages(
        self,
        query: str,
        conversation_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search messages by semantic similarity."""
        where_filter = {"conversation_id": conversation_id} if conversation_id else None
        
        results = self.messages_collection.query(
            query_texts=[query],
            n_results=limit,
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
        
        messages = []
        if results["ids"] and results["ids"][0]:
            for i, msg_id in enumerate(results["ids"][0]):
                messages.append({
                    "id": msg_id,
                    "content": results["documents"][0][i],
                    "role": results["metadatas"][0][i].get("role", "user"),
                    "relevance": 1 - results["distances"][0][i]  # Convert distance to similarity
                })
                
        return messages
