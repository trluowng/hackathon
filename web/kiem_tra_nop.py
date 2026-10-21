"""Kiểm tra nhanh ngay lúc nộp.

Chỉ báo về định dạng - code đọc được không (cú pháp), nhận ra bài nào, phiếu đọc được không -
để đội kịp sửa trước hạn. KHÔNG chạy code (để nhiều đội nộp cùng lúc không quá tải; code được
chạy khi admin bấm chấm) và KHÔNG tiết lộ kết quả đúng/sai.
"""
import ast
import os

from cham import CAC_PHAN, THONG_DIEP, _chuan_thong_diep, nap_phieu, tim_bo_cuc, tim_phieu
from doc_phieu_word import LoiDocPhieu
from nap_ma_nguon import LoiNapFile, nap


def kiem_tra(thu_muc, ma_doi=None):
    """Trả về (kết quả kiểm tra để hiện cho đội, hidden_dung - chỉ lưu phía server)."""
    vi_tri, canh_bao, _ = tim_bo_cuc(thu_muc)
    phan_cua_file = {}
    for (bai, tv), f in vi_tri.items():
        phan_cua_file.setdefault(os.path.basename(f), []).append("%d%s" % (bai, tv))

    cac_file = []
    for ten in sorted(os.listdir(thu_muc)):
        if not ten.lower().endswith((".py", ".ipynb")):
            continue
        muc = {"ten": ten, "phan": sorted(phan_cua_file.get(ten, [])), "van_de": []}
        try:
            cay = ast.parse(nap(os.path.join(thu_muc, ten)).ma_nguon)
            if not any(isinstance(n, ast.Call) and getattr(n.func, "id", None) in ("print", "display")
                       for n in ast.walk(cay)) and not ten.lower().endswith(".ipynb"):
                muc["van_de"].append("Không thấy lệnh print() nào - code cần in ra kết quả")
        except LoiNapFile as e:
            muc["van_de"].append(str(e))
        except SyntaxError as e:
            muc["van_de"].append("Lỗi cú pháp dòng %s: %s" % (e.lineno, e.msg))
        if not muc["phan"]:
            muc["van_de"].append("Không nhận ra bài nào trong file (không thấy dữ liệu đề cho trong code)")
        cac_file.append(muc)

    phieu = {"ten": None, "van_de": [], "hop_le": False}  # hop_le: đọc được và đúng mẫu
    hidden_dung = False
    duong_dan_phieu = tim_phieu(thu_muc)
    if not duong_dan_phieu:
        phieu["van_de"].append("Chưa có phiếu trả lời (file Word .docx theo mẫu)")
    else:
        phieu["ten"] = os.path.basename(duong_dan_phieu)
        try:
            noi_dung, canh_bao_phieu = nap_phieu(duong_dan_phieu)
            phieu["van_de"] += canh_bao_phieu
            phieu["hop_le"] = bool(noi_dung.get("bai"))
            so_o_trong = sum(1 for b in noi_dung.get("bai", {}).values() for v in b.values() if v is None)
            if so_o_trong:
                phieu["van_de"].append("Còn %d ô kết quả để trống hoặc không đọc được" % so_o_trong)
            ma_trong_phieu = (noi_dung.get("ma_doi") or "").strip()
            if ma_doi and ma_trong_phieu and ma_trong_phieu.upper() != ma_doi.upper():
                phieu["van_de"].append("Mã đội ghi trong phiếu (%s) khác mã đội đã nhập khi nộp (%s)"
                                       % (ma_trong_phieu, ma_doi))
            hidden_dung = _chuan_thong_diep(noi_dung.get("thong_diep")) == THONG_DIEP
        except LoiDocPhieu as e:
            phieu["van_de"].append(str(e))

    return {
        "cac_file": cac_file,
        "thieu": ["%d%s" % p for p in CAC_PHAN if p not in vi_tri],
        "phieu": phieu,
        "canh_bao": canh_bao,
    }, hidden_dung
