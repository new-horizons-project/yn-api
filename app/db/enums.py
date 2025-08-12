from enum import Enum

class DisplayMode(Enum):
	standard = "Standard"
	wiki     = "Wiki"


class ParseMode(Enum):
	markdown = "Markdown"
	bbcode   = "BBCode"


class JWT_Type(Enum):
	access  = "access"
	refresh = "refresh"


class UserRoles(Enum):
	admin     = "admin"
	user      = "user"
	moderator = "moderator"