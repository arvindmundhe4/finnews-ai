from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

def setup_cors(app: FastAPI):
    """Setup CORS middleware for the application."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, you would restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    return app
