from .auth  import router as auth_router
# from .topic import router as topic_router
# from .translation import router as translation_router
from .users import router as user_router, router_public as user_router_public
from .admin import router as admin_router

__all__ = (
	"auth_router",
	#"topic_router",
	#"translation_router",
	"user_router_public",
	"user_router",
    "admin_router"
)