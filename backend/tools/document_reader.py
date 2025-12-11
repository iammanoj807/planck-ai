"""Document reading tool for PDFs and URLs"""
import json
import os
import asyncio
import io
from PIL import Image
import httpx
from pathlib import Path
from bs4 import BeautifulSoup
import fitz  # PyMuPDF



# Helper for OCR
async def _ocr_page(image_data: str) -> str:
    """Use GPT-4o to transcribe text from a base64 image."""
    try:
        token = os.getenv("GITHUB_TOKEN")
        if not token:
            return "" # Skip if no token
            
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://models.inference.ai.azure.com/chat/completions",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-4o-mini", # Use mini to avoid 4o rate limits
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a precise OCR engine. Transcribe the text from this image exactly as it appears. Do not describe the image. Output ONLY the text."
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    "max_tokens": 2000
                }
            )
            if response.status_code == 200:
                res = response.json()
                content = res["choices"][0]["message"]["content"]
                return content
            return ""
    except Exception as e:
        print(f"OCR Error: {e}")
        return ""

async def read_pdf(file_path: str) -> str:
    """Extract text from a PDF file (supports scanned PDFs via OCR)."""
    try:
        doc = fitz.open(file_path)
        text = ""
        is_scanned = True
        
        # First pass: Try standard text extraction
        raw_text = ""
        for page in doc:
            raw_text += page.get_text()
            
        # Heuristic: If we found meaningful text, it's not a scanned-only PDF
        if len(raw_text.strip()) > 100:
             is_scanned = False
             text = raw_text
        
        # Second pass: If scanned/empty, use OCR on first 5 pages
        if is_scanned:
            print("DEBUG: PDF appears scanned or empty. Starting OCR...")
            import base64
            
            # Process ALL pages in batches of 3 to reduce API calls
            # e.g. 10 pages = 4 API calls (3+3+3+1), vs 10 calls.
            batch_size = 3
            total_pages = len(doc)
            
            # Helper to process a batch
            async def process_batch(start_idx):
                images = []
                for i in range(start_idx, min(start_idx + batch_size, total_pages)):
                    page = doc[i]
                    # Render page (1.5x zoom is good balance)
                    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
                    img_data = pix.tobytes("png")
                    images.append(Image.open(io.BytesIO(img_data)))
                
                if not images:
                    return ""
                    
                print(f"DEBUG: Stitching batch {start_idx}-{start_idx+len(images)}...")
                
                # Stitch images vertically
                total_height = sum(img.height for img in images)
                max_width = max(img.width for img in images)
                stitched_img = Image.new('RGB', (max_width, total_height), (255, 255, 255))
                y_offset = 0
                for img in images:
                    stitched_img.paste(img, (0, y_offset))
                    y_offset += img.height
                    
                # Encode
                buffered = io.BytesIO()
                stitched_img.save(buffered, format="JPEG", quality=80)
                b64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
                
                # OCR Call
                return await _ocr_page(b64_img)

            # Iterate through batches
            print(f"DEBUG: Processing {total_pages} pages in batches of {batch_size}...")
            
            for start in range(0, total_pages, batch_size):
                batch_text = await process_batch(start)
                text += f"\n--- Pages {start+1}-{min(start+batch_size, total_pages)} ---\n{batch_text}"
                
                # Tiny sleep between batches
                if start + batch_size < total_pages:
                    await asyncio.sleep(1)
            
        doc.close()
        return text.strip() if text.strip() else "PDF was empty and OCR failed to extract text."
        
    except Exception as e:
        return f"Error reading PDF: {str(e)}"


async def read_url(url: str) -> str:
    """Extract text content from a URL."""
    try:
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            response = await client.get(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            })
            
            if response.status_code != 200:
                if response.status_code == 403:
                    return "Error: Access Forbidden (403). This site blocks automated access. Please Try a DIFFERENT link from your search results."
                return f"Error fetching URL: HTTP {response.status_code}"
                
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
                
            # Get text
            text = soup.get_text(separator="\n", strip=True)
            
            # Clean up whitespace
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            return "\n".join(lines)
            
    except Exception as e:
        return f"Error reading URL: {str(e)}"


async def document_reader_tool(source: str, source_type: str = "auto") -> str:
    """
    Read content from a PDF file or URL.
    
    Args:
        source: File path or URL
        source_type: 'pdf', 'url', or 'auto' (auto-detect)
        
    Returns:
        JSON string with the extracted content
    """
    try:
        # Auto-detect source type
        if source_type == "auto":
            if source.startswith(("http://", "https://")):
                source_type = "url"
            elif source.lower().endswith(".pdf"):
                source_type = "pdf"
            else:
                source_type = "url"  # Default to URL for unknown
                
        # Extract content
        if source_type == "pdf":
            if not Path(source).exists():
                return json.dumps({"error": f"File not found: {source}"})
            content = await read_pdf(source)
        else:
            content = await read_url(source)
            
        # Truncate if too long
        # Critical for token management: A single huge page can blow the context window.
        # 10000 chars is ~2500 tokens, which fits comfortably in GPT-4o-mini's context.
        max_length = 10000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n[Content truncated...]"
            
        return json.dumps({
            "source": source,
            "source_type": source_type,
            "content": content,
            "length": len(content)
        }, indent=2)
        
    except Exception as e:
        return json.dumps({"error": str(e)})


# Tool definition for LangChain
DOCUMENT_READER_TOOL_DEF = {
    "name": "document_reader",
    "description": "Read and extract text content from PDFs or web URLs. Use this to analyze documents or gather information from web pages.",
    "parameters": {
        "type": "object",
        "properties": {
            "source": {
                "type": "string",
                "description": "File path for PDF or URL for web page"
            },
            "source_type": {
                "type": "string",
                "description": "Type of source: 'pdf', 'url', or 'auto'",
                "enum": ["pdf", "url", "auto"],
                "default": "auto"
            }
        },
        "required": ["source"]
    }
}
