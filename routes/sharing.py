from typing import Dict, Any
import json
import uuid
from datetime import datetime, timedelta
import traceback

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from models import SharedChat

# Create router
router = APIRouter()

# Configure templates
templates = Jinja2Templates(directory="templates")

@router.post("/api/share_chat")
async def share_chat(request: Request, data: Dict[str, Any]):
    """Share a chat for public viewing."""
    try:
        # Validate input data
        if 'messages' not in data or not data['messages']:
            return JSONResponse(
                status_code=400,
                content={"error": "No messages provided"}
            )
        
        # Log incoming data for debugging
        print("SHARING REQUEST DATA:")
        print(f"Title: {data.get('title', 'FinNews Conversation')}")
        print(f"Messages count: {len(data.get('messages', []))}")
        
        # Process messages to ensure HTML content is preserved
        messages = []
        for msg in data.get('messages', []):
            role = msg.get('role', 'unknown')
            content = msg.get('content', '')
            
            # For assistant messages, ensure HTML is preserved
            if role == 'assistant' and content:
                # Log a sample of the content
                print(f"Assistant message content sample: {content[:200]}...")
                
                # No need to escape HTML - store as is
                processed_message = {
                    'role': role,
                    'content': content  # Store the HTML content directly
                }
            else:
                processed_message = {
                    'role': role,
                    'content': content
                }
            
            messages.append(processed_message)
        
        title = data.get('title', 'FinNews Conversation')
        
        # Generate a unique ID for the shared chat
        share_id = str(uuid.uuid4())
        
        # Get current time
        now = datetime.now()
        
        # Store in database with processed messages
        await SharedChat.create(
            id=share_id,
            title=title,
            messages=messages,
            created_at=now
        )
        
        return {"share_id": share_id}
    except Exception as e:
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Error sharing chat: {str(e)}"}
        )


@router.get("/shared/{share_id}", response_class=HTMLResponse)
async def view_shared_chat(request: Request, share_id: str):
    """View a shared chat."""
    try:
        # Get the shared chat from database
        shared_chat = await SharedChat.get_or_none(id=share_id)
        
        if not shared_chat:
            return templates.TemplateResponse(
                "error.html",
                {
                    "request": request,
                    "error_message": "Shared chat not found. Please check the URL and try again."
                },
                status_code=404
            )
        
        # Parse the messages - handle both string and list formats
        messages = shared_chat.messages
        
        # Log retrieved messages for debugging
        print(f"RETRIEVED SHARED CHAT (ID: {share_id})")
        print(f"Message count: {len(messages) if isinstance(messages, list) else 'Not a list'}")
        
        if isinstance(messages, str):
            try:
                messages = json.loads(messages)
            except json.JSONDecodeError:
                raise ValueError("Invalid message format in database")
        
        # Log a sample of each message
        for i, msg in enumerate(messages):
            role = msg.get('role', 'unknown')
            content_preview = str(msg.get('content', ''))[:100] + '...'
            content_type = 'HTML' if '<' in str(msg.get('content', '')) else 'Text'
            print(f"Message {i+1}: Role={role}, Type={content_type}, Preview={content_preview}")
        
        title = shared_chat.title
        created_at = shared_chat.created_at
        
        # Return template with messages that preserve HTML
        return templates.TemplateResponse(
            "shared_chat.html",
            {
                "request": request,
                "title": title,
                "messages": messages,
                "created_at": created_at,
                "share_id": share_id
            }
        )
    except Exception as e:
        traceback.print_exc()
        return templates.TemplateResponse(
            "error.html",
            {
                "request": request,
                "error_message": f"Error viewing shared chat: {str(e)}"
            }
        )
