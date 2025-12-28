import json
from typing import Any, Generic, Optional, Type, TypeVar

from pydantic import BaseModel

from ..db.enums import EntityType
from ..schema.category import CategoryBase
from ..schema.topics import TopicBase, TopicTranslationBase
from ..schema.translation_code import Translation
from ..schema.tag import TagBase
from .client import redis

T = TypeVar("T", bound = BaseModel)


class RedisEntityCache(Generic[T]):
	def __init__(self, entity_type: EntityType, model: Type[T]):
		self.entity_type = entity_type
		self.model = model


	@staticmethod
	def _key(
		entity_type: EntityType,
		entity_id: int,
		relation_type: Optional[EntityType] = None,
		suffix: Optional[str] = None
	) -> str:
		base = f"{entity_type.value}:{entity_id}"

		if relation_type is not None:
			base += f":{relation_type.value}"

		if suffix is not None:
			base += f":{suffix}"

		return base


	def key(self, entity_id: int) -> str:
		return self._key(self.entity_type, entity_id)


	def cascade_key(self, entity_id: int) -> str:
		return self._key(self.entity_type, entity_id, suffix = "cascade")


	def relation_key(self, entity_id: int, related_type: EntityType) -> str:
		return self._key(self.entity_type, entity_id, related_type)


	def back_relation_key(self, entity_id: int) -> str:
		return self._key(self.entity_type, entity_id, suffix = "back-relation")


	async def exist(self, entity_id: int, relation_type: Optional[EntityType] = None) -> int:
		return await redis.exists(self._key(self.entity_type, entity_id, relation_type))


	async def set(self, entity_id: int, obj: T) -> None:
		def checknull(value):
			if value is None:
				return "null"
			
			return value

		mapping = {
			key: checknull(value) 
			for key, value in obj.model_dump(mode="json").items()
		}

		await redis.hset(self.key(entity_id), mapping = mapping)


	async def get(self, entity_id: int) -> Optional[T]:
		raw = await redis.hgetall(self.key(entity_id))

		if not raw:
			return None
		
		object = {}

		for key, value in raw.items():
			if value == "null":
				object[key] = None
				continue
			object[key] = value

		print(object)

		return self.model.model_validate(object)


	async def incr(self, entity_id: int, relation_type: Optional[EntityType] = None) -> int:
		return await redis.incr(self._key(self.entity_type, entity_id, relation_type, "count"))


	async def add_cascade(self,
		entity_id: int,
		related_type: EntityType,
		related_id: int
	) -> None:
		await redis.sadd(self.cascade_key(entity_id), self._key(related_type, related_id))


	async def add_relation(self,
		entity_id: int,
		related_type: EntityType,
		related_id: int
	) -> None:
		await redis.sadd(self.relation_key(entity_id, related_type), self._key(related_type, related_id))


	async def add_back_relation(self,
		entity_id: int,
		related_type: EntityType,
		related_id: int,
	) -> None:
		await redis.sadd(self.back_relation_key(entity_id), self._key(related_type, related_id))


	async def get_relations(self, entity_id: int, related_type: EntityType) -> list[Any]:
		relation_keys = await redis.smembers(self.relation_key(entity_id, related_type))
		pipe = redis.pipeline()

		for relation_key in relation_keys:
			pipe.hgetall(relation_key)

		return await pipe.execute()


	async def delete(self, entity_id: int) -> None:
		name = self.key(entity_id)
		cascade_name = self.cascade_key(entity_id)
		cascade = await redis.smembers(cascade_name)

		await redis.delete(name, *cascade, cascade_name)

		back_relation = await redis.smembers(self.back_relation_key(entity_id))

		for i in back_relation:
			back_name = f"{i}:{self.entity_type.value}"
			await redis.srem(back_name, cascade_name)


	async def delete_relation(self, entity_id: int, related_type: EntityType, related_id: int) -> None:
		await redis.srem(self.relation_key(entity_id, related_type), self._key(related_type, related_id))


	async def delete_back_relation(self, entity_id: int, related_type: EntityType, related_id: int) -> None:
		await redis.srem(self.back_relation_key(entity_id), self._key(related_type, related_id))


topic_cache = RedisEntityCache(EntityType.topic, TopicBase)
category_cache = RedisEntityCache(EntityType.category, CategoryBase)
topic_translation_cache = RedisEntityCache(EntityType.topic_translation, TopicTranslationBase)
translation_cache = RedisEntityCache(EntityType.translation, Translation)
tag_cache = RedisEntityCache(EntityType.tag, TagBase)


# "topic:1": TopicBase
# "topic:1:count": 0
# "category:1": CategoryBase
# "category:1:count": 0
# "category:1:cascade": # cascade del
#	"topic:1"
#	"topic:2"
#	 ...
# "topic:1:topic-translation":
#	"topic-translation:1"
#	"topic-translation:2"
#    ...
# "topic:1:topic-translation:count": 0
# "topic-translation:1:back-relation": "topic:1" # del\edit relation
