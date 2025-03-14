from .cors import setup_cors
from .rate_limiter import setup_rate_limiter

def setup_middlewares(app):
    """Setup all middleware for the application"""
    setup_cors(app)
    setup_rate_limiter(app)
