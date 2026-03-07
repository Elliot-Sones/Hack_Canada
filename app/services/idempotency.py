from typing import TypeVar

from pydantic import BaseModel

from app.middleware.idempotency import check_idempotency

ResponseModelT = TypeVar("ResponseModelT", bound=BaseModel)


async def get_cached_response(key: str | None, response_model: type[ResponseModelT]) -> ResponseModelT | None:
    cached = await check_idempotency(key)
    if cached is None:
        return None
    return response_model.model_validate(cached)


async def cache_response(key: str | None, response: BaseModel) -> None:
    await check_idempotency(key, response.model_dump(mode="json"))
