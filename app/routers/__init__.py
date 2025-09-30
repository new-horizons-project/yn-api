from .auth  import router as auth_router
from .tag   import router as tag_router, router_public as tag_router_public
from .topic import router as topic_router, router_public as topic_router_public
from .users import router as user_router, router_public as user_router_public
from .admin import router as admin_router
from .translation_codes import router as translation_codes_router

__all__ = (
	"auth_router",
	"tag_router",
	"tag_router_public",
	"topic_router",
	"topic_router_public",
	"user_router_public",
	"user_router",
    "admin_router",
	"translation_codes_router"
)