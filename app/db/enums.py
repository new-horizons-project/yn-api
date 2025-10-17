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
	

class JWT_Type(str, Enum):
	access  = "access"
	refresh = "refresh"


class MediaType(str, Enum):
	user_avatar    = "user_avatar"
	system         = "system"
	topic          = "topic"


class MediaSize(str, Enum):
	original   = "original"
	large      = "large"
	medium     = "medium"
	small      = "small"
	thumbnail  = "thumbnail"