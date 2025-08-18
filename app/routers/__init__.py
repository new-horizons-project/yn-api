from .auth import router as auth_router
from .users import router as user_router
from .jwt import router as jwt_router
from .admin import router as admin_router

__all__ = ["auth_router", "user_router", "jwt_router", "admin_router"]