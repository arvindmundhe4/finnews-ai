import os
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import uuid
from pathlib import Path
import re

from fastapi import FastAPI, Request, Form, HTTPException, Depends, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import openai
from dotenv import load_dotenv
from tortoise.contrib.fastapi import register_tortoise

# Import middlewares and routes
from middleware import setup_middlewares
from routes import router as api_router

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="FinNews",
    description="Financial News Assistant with OpenAI API",
    version="1.0.0"
)

# Setup middlewares
setup_middlewares(app)

# Set OpenAI API key from environment variables
openai.api_key = os.getenv("OPENAI_API_KEY")

# Get model names from environment variables
SEARCH_MODEL = os.getenv("OPENAI_SEARCH_MODEL", "gpt-4o-mini-search-preview")
SENTIMENT_MODEL = os.getenv("OPENAI_SENTIMENT_MODEL", "gpt-4o-mini")

# Set up static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Database paths
DB_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(DB_DIR, "database.sqlite")

# Register router
app.include_router(api_router)

# Register Tortoise ORM
register_tortoise(
    app,
    db_url=os.getenv("DATABASE_URL", f"sqlite://{DB_PATH}"),
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Main route
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Start the application with Uvicorn when running this file directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
