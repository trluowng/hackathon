"""Điểm vào cho Vercel: mọi đường dẫn được chuyển về app FastAPI trong thư mục web/ (xem vercel.json)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "web"))

from app import app  # noqa: E402,F401
