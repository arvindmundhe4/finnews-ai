from typing import Dict, Any
import json
import uuid
from datetime import datetime
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
        
        title = data.get('title', 'FinNews Conversation')
        messages = data.get('messages', [])
        
        # Generate a unique ID for the shared chat
        share_id = str(uuid.uuid4())
        
        # Store in database - ensure consistent storage format for messages
        # The tortoise-orm JSONField stores Python objects directly
        await SharedChat.create(
            id=share_id,
            title=title,
            messages=messages  # Store as a Python list directly
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
        if isinstance(messages, str):
            try:
                messages = json.loads(messages)
            except json.JSONDecodeError:
                raise ValueError("Invalid message format in database")
        
        title = shared_chat.title
        created_at = shared_chat.created_at
        
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
            },
            status_code=500
        )
