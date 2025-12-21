from typing import Any, Dict, List, Optional, Protocol, Set, Union, cast

from redis.asyncio import Redis
from redis.typing import AbsExpiryT, EncodableT, ExpiryT, FieldT, KeyT, ResponseT

from ..config import settings

redis_client = Redis(
	host = settings.REDIS_HOST,
	port = settings.REDIS_PORT,
	db   = settings.REDIS_DB,
	decode_responses = True
)
redis_client.srem

class AsyncRedisPipelineProtocol(Protocol):
    def hgetall(self, name: str) -> dict[Any, Any]: ...
    async def execute(self, raise_on_error: bool = True) -> List[Any]: ...

class AsyncRedisProtocol(Protocol):
	def exists(self, *names: KeyT) -> ResponseT: ...

	async def hset(
		self,
		name: str,
		key: str | None = None,
		value: str | None = None,
		mapping: Dict[Any, Any] | None = None,
		items: List[Any] | None = None,
	) -> int: ...

	async def hgetall(
		self,
		name: str,
	) -> Dict[Any, Any]: ...

	async def hget(
		self,
		name: str,
		key: str,
	) -> str | None: ...

	def set(
        self,
        name: KeyT,
        value: EncodableT,
        ex: Optional[ExpiryT] = None,
        px: Optional[ExpiryT] = None,
        nx: bool = False,
        xx: bool = False,
        keepttl: bool = False,
        get: bool = False,
        exat: Optional[AbsExpiryT] = None,
        pxat: Optional[AbsExpiryT] = None,
        ifeq: Optional[Union[bytes, str]] = None,
        ifne: Optional[Union[bytes, str]] = None,
        ifdeq: Optional[str] = None,  # hex digest of current value
        ifdne: Optional[str] = None,  # hex digest of current value
    ) -> ResponseT: ...

	def get(self, name: KeyT) -> ResponseT: ...

	def delete(
		self,
		*names: KeyT,
	) -> ResponseT: ...

	def incr(
		self,
		name: KeyT,
		amount: int = 1,
	) -> ResponseT: ...

	async def sadd(self, name: KeyT, *values: FieldT) -> int: ...

	async def srem(self,
		name: KeyT,
		*values: FieldT
	) -> int: ...

	async def smembers(self, name: KeyT) -> Set[Any]: ...

	def pipeline(
		self, transaction: bool = True, shard_hint: Optional[str] = None
	) -> AsyncRedisPipelineProtocol: ...

redis: AsyncRedisProtocol = cast(AsyncRedisProtocol, redis_client)
