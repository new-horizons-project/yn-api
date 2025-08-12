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


class ActionType(Enum):
	create = "create"
	update = "update"
	delete = "delete"


class ObjectType(Enum):
	user                 = "user"
	topic                = "topic"
	topic_translation    = "translation"
	translation_types    = "translation_types"
	category             = "category"
	tag                  = "tag"
	topic_link           = "topic_link"
	jwt_token            = "jwt_token"
	