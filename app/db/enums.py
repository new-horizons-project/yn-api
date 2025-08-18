from enum import Enum

class DisplayMode(str, Enum):
	standard = "Standard"
	wiki     = "Wiki"


class ParseMode(str, Enum):
	markdown = "Markdown"
	bbcode   = "BBCode"


class UserRoles(str, Enum):
	admin     = "admin"
	user      = "user"
	moderator = "moderator"


class ActionType(str, Enum):
	create = "create"
	update = "update"
	delete = "delete"


class ObjectType(str, Enum):
	user                 = "user"
	topic                = "topic"
	topic_translation    = "translation"
	translation_types    = "translation_types"
	category             = "category"
	tag                  = "tag"
	topic_link           = "topic_link"
	jwt_token            = "jwt_token"
	