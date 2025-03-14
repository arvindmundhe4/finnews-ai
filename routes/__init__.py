from fastapi import APIRouter

# Import all route modules
from .pages import router as pages_router
from .news import router as news_router
from .sharing import router as sharing_router

# Create main router that includes all sub-routers
router = APIRouter()

# Include all sub-routers
router.include_router(pages_router)
router.include_router(news_router)
router.include_router(sharing_router)
