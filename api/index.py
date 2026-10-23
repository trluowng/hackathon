"""Điểm vào cho Vercel: Vercel nhận ra app FastAPI ở đây và chuyển mọi đường dẫn về nó."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))

from app import app as _web  # noqa: E402

_TIEN_TO = "/api/index"


async def app(scope, receive, send):
    """Phòng khi Vercel chuyển request với đường dẫn /api/index/... (kiểu rewrite cũ): bỏ tiền tố đó đi."""
    duong_dan = scope.get("path", "")
    if scope["type"] in ("http", "websocket") and (duong_dan == _TIEN_TO or duong_dan.startswith(_TIEN_TO + "/")):
        scope = dict(scope, path=duong_dan[len(_TIEN_TO):] or "/")
    await _web(scope, receive, send)
