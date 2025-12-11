"""Image analysis tool using vision model"""
import base64
import json
import os
import httpx
from pathlib import Path


async def image_analyzer_tool(image_path: str, question: str = "Describe this image in detail.") -> str:
    """
    Analyze an image using GPT-4o Vision.
    
    Args:
        image_path: Path to the image file
        question: Question about the image
        
    Returns:
        JSON string with the analysis
    """
    try:
        # Debug logging
        print(f"DEBUG: Analyzing image at {image_path}")
        
        # Handle potential quotes in path string from LLM
        clean_path = str(image_path).strip().strip("'").strip('"')
        path_obj = Path(clean_path)
        
        if not path_obj.exists():
            print(f"DEBUG: Image file NOT FOUND at {clean_path}")
            # Try to resolve relative to cwd or upload dir if absolute fails
            upload_dir = Path("backend/uploads") if Path("backend/uploads").exists() else Path("uploads")
            alt_path = upload_dir / path_obj.name
            if alt_path.exists():
                print(f"DEBUG: Found image at alternative path: {alt_path}")
                path_obj = alt_path
            else:
                 return json.dumps({"error": f"Image file not found at: {clean_path} (or {alt_path})"})
            
        with open(path_obj, "rb") as f:
            image_data = base64.b64encode(f.read()).decode("utf-8")
            
        # Determine image type
        suffix = path_obj.suffix.lower()
        media_type = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".gif": "image/gif",
            ".webp": "image/webp"
        }.get(suffix, "image/jpeg")
        
        # Call GitHub Models API
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return json.dumps({"error": "GITHUB_TOKEN not set"})
            
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini",
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": question
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:{media_type};base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 1000
                }
            )
            
            if response.status_code != 200:
                return json.dumps({"error": f"API error: {response.status_code} - {response.text}"})
                
            result = response.json()
            analysis = result["choices"][0]["message"]["content"]
            
            return json.dumps({
                "image_path": str(image_path),
                "question": question,
                "analysis": analysis
            }, indent=2)
            
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tool definition for LangChain
IMAGE_ANALYZER_TOOL_DEF = {
    "name": "image_analyzer",
    "description": "Analyze an uploaded image using computer vision. Use this to describe images, identify objects, read text in images, or answer questions about visual content.",
    "parameters": {
        "type": "object",
        "properties": {
            "image_path": {
                "type": "string",
                "description": "Path to the image file"
            },
            "question": {
                "type": "string",
                "description": "Question about the image (default: describe the image)",
                "default": "Describe this image in detail."
            }
        },
        "required": ["image_path"]
    }
}
