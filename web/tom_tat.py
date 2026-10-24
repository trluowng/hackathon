"""Tóm tắt điểm của một lần nộp, dùng cho trang tổng quan và xếp hạng (không cần tải cả báo cáo)."""
from cham import CAN_REVIEW, tinh_diem


def tinh_tom_tat(kq, duyet):
    """kq: {"trang_thai", "bao_cao", "phieu"} hoặc None; duyet: {"2B": True/False}.

    hidden: đội hoàn thành Hidden Challenge (không cộng điểm, dùng khi bằng điểm).
    """
    tom_tat = {"trang_thai": kq["trang_thai"] if kq else "chua_cham", "tong": None, "diem_bai": [],
               "cho_duyet": 0, "nen_xem": 0, "hidden": False}
    if kq and kq["trang_thai"] == "da_cham" and kq.get("bao_cao"):
        bc = tinh_diem(kq["bao_cao"], kq.get("phieu") or {}, duyet)
        cac_phan = [p for b in bc["bai"].values() for p in b["thanh_vien"].values()]
        cac_phan += list((bc.get("hidden") or {}).get("thanh_vien", {}).values())
        tom_tat.update(tong=bc["tong_diem"], diem_bai=[bc["bai"][str(i)]["diem"] for i in range(1, 6)],
                       cho_duyet=sum(p["trang_thai"] == CAN_REVIEW and not p["diem"] for p in cac_phan),
                       nen_xem=sum(p["trang_thai"] == CAN_REVIEW and p["diem"] for p in cac_phan),
                       hidden=bool(bc["hidden_challenge"]["hoan_thanh"]))
    return tom_tat
