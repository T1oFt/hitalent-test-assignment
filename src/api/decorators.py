import hashlib
from functools import wraps
from typing import Callable

from fastapi import Request
from fastapi.responses import JSONResponse, Response


def etag_decorator(max_age: int = 60) -> Callable:
    """
    Декоратор для ETag кэширования.
    
    Работает только с ответами типа JSONResponse.
    Берет уже сериализованные байты из ответа для вычисления хэша.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, request: Request, **kwargs):
            result = await func(*args, request=request, **kwargs)

            if not isinstance(result, JSONResponse):
                return result

            content_bytes = result.body
            
            query_params = sorted(request.query_params.items())
            query_str = "&".join(f"{k}={v}" for k, v in query_params)
            
            hash_input = f"{query_str}:".encode() + content_bytes
            etag = f'"{hashlib.md5(hash_input).hexdigest()}"'

            if_none_match = request.headers.get("if-none-match")
            
            if if_none_match and if_none_match == etag:
                return Response(
                    status_code=304,
                    headers={
                        "ETag": etag,
                        "Cache-Control": f"public, max-age={max_age}"
                    }
                )

            result.headers["ETag"] = etag
            result.headers["Cache-Control"] = f"public, max-age={max_age}"
            
            return result
        return wrapper
    return decorator