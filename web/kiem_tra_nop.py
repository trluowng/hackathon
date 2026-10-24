"""Kiểm tra nhanh định dạng bài nộp (admin xem).

Chỉ báo về định dạng - code đọc được không (cú pháp), nhận ra bài nào, tên tệp đúng quy cách không,
phiếu đọc được không. KHÔNG chạy code (để nhiều đội nộp cùng lúc không quá tải; code được chạy khi
admin bấm chấm) và KHÔNG tiết lộ kết quả đúng/sai.
"""
import ast
import os
import re

from cham import CAC_PHAN, CAC_PHAN_HIDDEN, THONG_DIEP, _chuan_thong_diep, nap_phieu, ten_phan, tim_bo_cuc, \
    tim_phieu
from de_bai import HIDDEN_BAI
from doc_phieu_word import LoiDocPhieu
from nap_ma_nguon import LoiNapFile, nap

MAU_TEN_BAI = re.compile(r"^(?P<doi>.+?)_(?P<tv>[ABC])_Bai(?P<bai>[1-5])\.py$", re.I)
MAU_TEN_HIDDEN = re.compile(r"^(?P<doi>.+?)_Hidden_(?P<tv>[ABC])\.py$", re.I)


def phan_theo_ten(ten):
    """Phần mà tên tệp chuẩn chỉ tới: (1, 'A') cho D01_A_Bai1.py, ('H', 'B') cho D01_Hidden_B.py; None nếu sai mẫu."""
    m = MAU_TEN_BAI.match(ten)
    if m:
        return int(m["bai"]), m["tv"].upper()
    m = MAU_TEN_HIDDEN.match(ten)
    return (HIDDEN_BAI, m["tv"].upper()) if m else None


def kiem_tra(thu_muc, ma_doi=None):
    """Trả về (kết quả kiểm tra, hidden_dung - thông điệp cuối trong phiếu đúng, chỉ lưu phía server).

    kết quả["phieu"] gồm cả mã đội / tên đội ghi trong phiếu để đối chiếu với thông tin đội nhập khi nộp.
    """
    vi_tri, canh_bao, _ = tim_bo_cuc(thu_muc)
    phan_cua_file = {}
    for p, f in vi_tri.items():
        phan_cua_file.setdefault(os.path.basename(f), []).append(p)

    cac_file = []
    for ten in sorted(os.listdir(thu_muc)):
        if not ten.lower().endswith((".py", ".ipynb")):
            continue
        cac_phan = phan_cua_file.get(ten, [])
        muc = {"ten": ten, "phan": [ten_phan(p) for p in cac_phan], "van_de": []}
        try:
            cay = ast.parse(nap(os.path.join(thu_muc, ten)).ma_nguon)
            if not any(isinstance(n, ast.Call) and getattr(n.func, "id", None) in ("print", "display")
                       for n in ast.walk(cay)) and not ten.lower().endswith(".ipynb"):
                muc["van_de"].append("Không thấy lệnh print() nào - code cần in ra kết quả")
        except LoiNapFile as e:
            muc["van_de"].append(str(e))
        except SyntaxError as e:
            muc["van_de"].append("Lỗi cú pháp dòng %s: %s" % (e.lineno, e.msg))
        if not cac_phan:
            muc["van_de"].append("Không nhận ra bài nào trong file (không thấy dữ liệu đề cho trong code)")

        theo_ten = phan_theo_ten(ten)
        if theo_ten is None:
            muc["van_de"].append("Tên tệp chưa đúng quy cách <MaDoi>_<A/B/C>_BaiN.py hoặc <MaDoi>_Hidden_<A/B/C>.py")
        else:
            doi_trong_ten = (MAU_TEN_BAI.match(ten) or MAU_TEN_HIDDEN.match(ten))["doi"]
            if ma_doi and doi_trong_ten.upper() != ma_doi.upper():
                muc["van_de"].append("Mã đội trong tên tệp (%s) khác mã đội (%s)" % (doi_trong_ten, ma_doi))
            if cac_phan and theo_ten not in cac_phan:
                muc["van_de"].append("Tên tệp là %s nhưng nội dung là %s - kiểm tra có đặt nhầm tên không" % (
                    ten_phan(theo_ten), ", ".join(ten_phan(p) for p in cac_phan)))
        if len(cac_phan) > 1:
            muc["van_de"].append("Một tệp chứa nhiều phần - đề yêu cầu mỗi phần một tệp")
        cac_file.append(muc)

    phieu = {"ten": None, "van_de": [], "hop_le": False,  # hop_le: đọc được và đúng mẫu
             "ma_doi": "", "ten_doi": ""}
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
            phieu["ma_doi"] = (noi_dung.get("ma_doi") or "").strip()
            phieu["ten_doi"] = (noi_dung.get("ten_doi") or "").strip()
            hidden_dung = _chuan_thong_diep(noi_dung.get("thong_diep")) == THONG_DIEP
        except LoiDocPhieu as e:
            phieu["van_de"].append(str(e))

    return {
        "cac_file": cac_file,
        "thieu": [ten_phan(p) for p in CAC_PHAN if p not in vi_tri],
        "thieu_hidden": [ten_phan(p) for p in CAC_PHAN_HIDDEN if p not in vi_tri],
        "phieu": phieu,
        "canh_bao": canh_bao,
    }, hidden_dung
