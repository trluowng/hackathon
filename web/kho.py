"""Chọn nơi lưu trữ theo môi trường (các bản có cùng các hàm, app không cần biết đang dùng bản nào).

- APPS_SCRIPT_URL: Google Apps Script giữ trang nộp bài + Drive; web này chỉ admin + chấm (kho_apps_script).
- GOOGLE_REFRESH_TOKEN (hoặc KHO=drive_gia khi test): web lưu thẳng lên Google Drive bằng OAuth (kho_drive).
- Không có gì: SQLite + file trên ổ đĩa (kho_sqlite) - chạy trên máy cá nhân / VPS.
"""
import os

if os.environ.get("APPS_SCRIPT_URL"):
    import kho_apps_script as _ban
elif os.environ.get("GOOGLE_REFRESH_TOKEN") or os.environ.get("KHO") == "drive_gia":
    import kho_drive as _ban
elif os.environ.get("VERCEL"):
    raise RuntimeError("Chạy trên Vercel cần cấu hình nơi lưu bài: APPS_SCRIPT_URL và APPS_SCRIPT_KHOA "
                       "(xem HUONG_DAN_DEPLOY.md)")
else:
    import kho_sqlite as _ban

globals().update({k: v for k, v in vars(_ban).items() if not k.startswith("_")})

# Link trang nộp bài bên ngoài (Apps Script), nếu có - trang chủ web này chuyển hướng tới đó
NOP_BAI_NGOAI = getattr(_ban, "NOP_BAI_NGOAI", "")
# Lưu kết quả kiểm tra định dạng tính lúc chấm; các bản khác đã lưu lúc nộp nên bỏ qua
luu_kiem_tra = getattr(_ban, "luu_kiem_tra", lambda lan_nop_id, kiem_tra: None)
