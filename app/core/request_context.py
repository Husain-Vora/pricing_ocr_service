"""
RequestContext: per-request correlation id, independent of any web
framework object, so services/ml/ocr code can log with the same id
without needing the Request object threaded through every call.
"""
import uuid
from contextvars import ContextVar
from typing import Optional

_request_id_ctx: ContextVar[Optional[str]] = ContextVar("request_id", default=None)


def new_request_id() -> str:
    return str(uuid.uuid4())


def set_request_id(request_id: str) -> None:
    _request_id_ctx.set(request_id)


def get_request_id() -> Optional[str]:
    return _request_id_ctx.get()
