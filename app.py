import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from tortoise.contrib.fastapi import register_tortoise
from dotenv import load_dotenv

# ✅ Explicitly load .env from full path
load_dotenv()

# Import middlewares and routes
from middleware import setup_middlewares
from routes import router

# ✅ Configure API KEY from environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    print("❌ WARNING: OPENAI_API_KEY environment variable not set. API calls will fail.")

# Create FastAPI app
app = FastAPI(
    title="FinNews AI",
    description="Financial news assistant powered by FastAPI and OpenAI",
    version="1.0.0",
)

# Setup middlewares
setup_middlewares(app)

# Set up static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Register the router
app.include_router(router)

# Set up the database
register_tortoise(
    app,
    db_url=os.getenv("DATABASE_URL", "sqlite://database.sqlite"),
    modules={"models": ["models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Custom error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse("404.html", {"request": request}, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    templates = Jinja2Templates(directory="templates")
    return templates.TemplateResponse(
        "error.html",
        {"request": request, "error_message": str(exc)},
        status_code=500
    )

# Run the FastAPI app if executed directly
if __name__ == "__main__":
    import uvicorn
    #uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
