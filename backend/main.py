"""FastAPI application for Planck AI"""
import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, List
from datetime import datetime

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Import agent and memory
from agent.graph import agent_runner
from memory.store import ConversationMemory

# Initialize app
app = FastAPI(
    title="Planck AI API",
    description="Multi-Modal AI Agent API",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize memory store
memory = ConversationMemory()

# Upload directory (Absolute path)
UPLOAD_DIR = Path(__file__).parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)


# Request/Response models
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    files: Optional[List[dict]] = None
    model: Optional[str] = "gpt-4o-mini"


class ChatResponse(BaseModel):
    conversation_id: str
    response: str
    tool_calls: List[dict]


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    message_count: int


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


# Chat endpoint with streaming
@app.post("/chat")
async def chat(request: ChatRequest):
    """Send a message to the agent and get a streaming response."""
    
    # Check for API token
    if not os.getenv("GITHUB_TOKEN"):
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured")
    
    # Get or create conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        # Strip Mode tag for the title
        import re
        # Strip [Mode: ...] and [Focus Mode: ...]
        clean_title_msg = re.sub(r'\[(Focus )?Mode:.*?\]\s*', '', request.message)
        title = clean_title_msg[:50] + "..." if len(clean_title_msg) > 50 else clean_title_msg
        
        conversation_id = memory.create_conversation(title=title)
    
    # Get conversation history
    history = memory.get_messages(conversation_id)
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in history
    ]
    
    # Add user message to memory
    memory.add_message(conversation_id, "user", request.message)
    
    async def generate():
        """Generate streaming response."""
        full_response = ""
        tool_calls = []
        
        # Detect mode from message content (injected by frontend)
        mode = "web"
        clean_message = request.message

        if "[Mode: Chat]" in request.message:
            mode = "chat"
            clean_message = request.message.replace("[Mode: Chat]", "").strip()
        elif "[Mode: Web]" in request.message:
            mode = "web"
            clean_message = request.message.replace("[Mode: Web]", "").strip()
        
        # Detect and extract language preference
        # Format: [Language: Nepali]
        language = "English"
        import re
        lang_match = re.search(r'\[Language: (.*?)\]', clean_message)
        if lang_match:
            language = lang_match.group(1)
            clean_message = clean_message.replace(lang_match.group(0), "").strip()
        
        # Also handle legacy format just in case
        elif "[Focus Mode: Chat Only]" in request.message:
            mode = "chat"
            # Strip the heavy-handed legacy tag
            clean_message = re.sub(r'\[Focus Mode:.*?\]', '', request.message).strip()

        async for chunk in agent_runner.run(
            user_message=clean_message,
            conversation_history=conversation_history,
            files=request.files,
            model_name=request.model,
            mode=mode,
            language=language
        ):
            # Yield chunk as SSE
            yield f"data: {json.dumps(chunk)}\n\n"
            
            # Collect response
            if chunk["type"] == "response":
                full_response = chunk["content"]
            elif chunk["type"] == "thinking":
                # Save the thinking step so it appears on reload
                tool_data = {
                    "tool": "thinking",
                    "input": {"query": "Analyzing request..."},
                    "status": "complete"
                }
                if not any(t.get("tool") == "thinking" for t in tool_calls):
                    tool_calls.append(tool_data)
            elif chunk["type"] == "tool_call":
                # Create entry for new tool call
                tool_data = {
                    "tool": chunk["metadata"].get("tool"),
                    "input": chunk["metadata"].get("input"),
                    "status": "running" # Mark as running initially
                }
                tool_calls.append(tool_data)
                
            elif chunk["type"] == "tool_result":
                # Update the last tool call with the result
                if tool_calls:
                    last_tool = tool_calls[-1]
                    # Verify it matches the tool name to be safe
                    if last_tool.get("tool") == chunk["metadata"].get("tool"):
                        result = chunk["metadata"].get("full_result")
                        
                        # Attempt to parse code executor results which are JSON strings
                        if last_tool.get("tool") == "code_executor" and isinstance(result, str):
                            try:
                                parsed_result = json.loads(result)
                                result = parsed_result
                            except:
                                pass
                                
                        last_tool["result"] = result
                        last_tool["status"] = "complete"

            elif chunk["type"] == "error":
                # Signal frontend that processing is complete
                # Also save the error to memory so it doesn't disappear on reload
                full_response = f"**Error:** {chunk['content']}"
                
        # Save assistant response to memory (only if not an error)
        if full_response:
            memory.add_message(
                conversation_id,
                "assistant",
                full_response,
                metadata={"tool_calls": tool_calls, "model": request.model}
            )
            
        # Send done signal
        yield f"data: {json.dumps({'type': 'done', 'conversation_id': request.conversation_id if request.conversation_id else conversation_id})}\n\n"


    return StreamingResponse(generate(), media_type="text/event-stream")

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Handle file uploads (images, PDFs, etc.).
    Saves the file to the local uploads directory and returns its metadata.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    return {
        "filename": file.filename,
        "original_name": file.filename,
        "path": file_path,
        "type": "image" if file.content_type.startswith("image/") else "pdf" if file.content_type == "application/pdf" else "file"
    }

# -------------------------------------------------------------------------
# Conversation Management
# -------------------------------------------------------------------------

# -------------------------------------------------------------------------
# Conversation Management
# -------------------------------------------------------------------------

@app.get("/conversations")
def list_conversations():
    """
    List all saved conversations.
    Retrieves from ChromaDB memory store.
    """
    try:
        conversations = memory.get_conversations(limit=100)
        return {"conversations": conversations}
    except Exception as e:
        print(f"Error listing conversations: {e}")
        return {"conversations": []}

@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: str):
    """
    Get full history of a specific conversation.
    """
    try:
        # Check if conversation exists (basic check via message retrieval or metadata)
        # For now, just try to get messages
        messages = memory.get_messages(conversation_id)
        return {
            "id": conversation_id,
            "messages": messages
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    """
    Delete a conversation.
    """
    success = memory.delete_conversation(conversation_id)
    if success:
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Conversation not found or could not be deleted")

# -------------------------------------------------------------------------
# Static Files & SPA Handling (Production/Docker)
# -------------------------------------------------------------------------
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Check for frontend build
frontend_dist = Path("frontend/dist")

if frontend_dist.exists():
    # Mount assets
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    # Manifest and other root files
    @app.get("/manifest.json")
    async def manifest():
        return FileResponse(frontend_dist / "manifest.json")
        
    @app.get("/favicon.ico")
    async def favicon():
        # Fallback if favicon isn't in root
        if (frontend_dist / "favicon.ico").exists():
            return FileResponse(frontend_dist / "favicon.ico")
        return {"error": "not found"}

    # Catch-all for SPA (must be last)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Skip API routes (handled above)
        if full_path.startswith("api"):
            raise HTTPException(status_code=404, detail="API route not found")
        
        # Check if file exists (e.g. manoj.png)
        file_path = frontend_dist / full_path
        if file_path.exists() and file_path.is_file():
            return FileResponse(file_path)
            
        # Default to index.html for React Router
        return FileResponse(frontend_dist / "index.html")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

