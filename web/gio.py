"""Giờ Việt Nam (UTC+7) - máy chủ cloud như Vercel chạy giờ UTC nên không dùng datetime.now() trực tiếp."""
from datetime import datetime, timedelta, timezone

GIO_VN = timezone(timedelta(hours=7))


def bay_gio_dt():
    """Thời điểm hiện tại theo giờ Việt Nam (datetime không kèm múi giờ, để so với hạn nộp admin nhập)."""
    return datetime.now(GIO_VN).replace(tzinfo=None)


def bay_gio():
    return bay_gio_dt().isoformat(timespec="seconds")
