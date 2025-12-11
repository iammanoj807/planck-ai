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
                messages.append({
                    "id": msg_id,
                    "content": results["documents"][i],
                    "role": results["metadatas"][i].get("role", "user"),
                    "timestamp": results["metadatas"][i].get("timestamp"),
                    "metadata": results["metadatas"][i]
                })
                
        # Sort by timestamp
        messages.sort(key=lambda x: x.get("timestamp", ""))
        
        return messages[-limit:]
        
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
