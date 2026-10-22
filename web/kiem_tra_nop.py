"""Kiểm tra nhanh ngay lúc nộp.

Chỉ báo về định dạng - code đọc được không (cú pháp), nhận ra bài nào, phiếu đọc được không -
để đội kịp sửa trước hạn. KHÔNG chạy code (để nhiều đội nộp cùng lúc không quá tải; code được
chạy khi admin bấm chấm) và KHÔNG tiết lộ kết quả đúng/sai.
"""
import ast
import os
import re

from cham import CAC_PHAN, THONG_DIEP, _chuan_thong_diep, nap_phieu, tim_bo_cuc, tim_phieu
from doc_phieu_word import LoiDocPhieu
from nap_ma_nguon import LoiNapFile, nap


def kiem_tra(thu_muc):
    """Trả về (kết quả kiểm tra, hidden_dung - chỉ lưu phía server).

    kết quả["phieu"] gồm cả mã đội / tên đội ghi trong phiếu để đối chiếu với thông tin đội nhập khi nộp.
    """
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

    # Ô nộp suy ra từ tên file chuẩn <MÃ>_BaiN.py: báo nộp nhầm ô, ô để trống
    thieu = ["%d%s" % p for p in CAC_PHAN if p not in vi_tri]
    for f in cac_file:
        m = re.search(r"_Bai([1-5])\.(py|ipynb)$", f["ten"], re.I)
        f["o"] = int(m.group(1)) if m else None
        bai_nhan_ra = sorted({p[0] for p in f["phan"]})
        if f["o"] and bai_nhan_ra and str(f["o"]) not in bai_nhan_ra:
            f["van_de"].append("File nộp ở ô Bài %d nhưng nội dung là Bài %s - kiểm tra có chọn nhầm file không"
                               % (f["o"], ", ".join(bai_nhan_ra)))
    o_da_nop = {f["o"] for f in cac_file if f["o"]}
    o_trong = [so for so in range(1, 6) if so not in o_da_nop and any(p.startswith(str(so)) for p in thieu)]

    return {
        "cac_file": cac_file,
        "thieu": thieu,
        "o_trong": o_trong,
        "phieu": phieu,
        "canh_bao": canh_bao,
    }, hidden_dung
