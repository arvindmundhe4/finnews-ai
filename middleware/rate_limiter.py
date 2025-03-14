from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Create a global rate limiter instance
limiter = Limiter(key_func=get_remote_address)

def setup_rate_limiter(app: FastAPI):
    """Setup rate limiter middleware for the application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    return app
