"""Chấm tự động Vòng 1 Olympic AI UNETI 2026.

Cách dùng:
  python cham.py <thu_muc_bai_nop> [--phieu phieu.docx|phieu.json] [--ma-doi D01] [--json ket_qua.json]

Không truyền --phieu thì tự lấy file Word (.docx) nằm trong thư mục bài nộp.

Đề yêu cầu mỗi phần một tệp <MaDoi>_<A/B/C>_BaiN.py (+ <MaDoi>_Hidden_<A/B/C>.py), nhưng engine vẫn
chấm được file đặt tên khác, gộp nhiều phần, .ipynb: phần nào nằm ở file nào được xác định bằng dữ liệu
đề cho xuất hiện trong code (tên file chỉ dùng làm gợi ý khi không tìm thấy dữ liệu). Sai quy cách tệp
chỉ mất điểm "tệp" của bài đó (xem _kiem_tra_tep).

Mỗi bài 5 điểm: A, B, C, Checkpoint + mảnh khóa (theo phiếu, code để xác thực) và 1 điểm tệp
(đủ 3 tệp đặt tên đúng, chạy được). Hidden Challenge không cộng điểm, chỉ xác nhận hoàn thành.

Mỗi phần A/B/C của mỗi bài (1 điểm) phải qua đủ:
  1. Kiểm tra tĩnh các ràng buộc đề trên vùng code của phần đó.
  2. Chạy thật (notebook: bỏ output đã lưu, chạy lại từ đầu). File gộp: tách riêng phần đó ra
     chạy để lỗi của phần khác không ảnh hưởng; không tách được thì chạy cả file.
  3. Test ẩn: thay dữ liệu đề cho bằng dữ liệu khác, chạy lại. Phải có dòng output đổi từ đáp án đề
     sang đúng đáp án mới -> chứng minh code tự tính ra kết quả, không hard-code.
"""
import argparse
import ast
import difflib
import json
import os
import re
import sys
import unicodedata
from collections import Counter

from chay_an_toan import chay
from de_bai import CAC_BAI, DAP_AN_K, DE_THI, HIDDEN, HIDDEN_BAI, MANH_KHOA, MAT_KHAU, THONG_DIEP, TU_KHOA, \
    tinh_checkpoint
from doc_phieu_word import LoiDocPhieu, doc_phieu
from kiem_tra_tinh import CANH_BAO, LOI
from nap_ma_nguon import LoiNapFile, nap
from phan_tach import tach_chuong_trinh, vung_code
from thay_du_lieu import _tuple_hoa, cac_literal, node_du_lieu, thay_du_lieu, tim_du_lieu
from thay_du_lieu import co_du_lieu as co_du_lieu_phan

MAU_TEN = re.compile(r"^(?P<doi>.+?)_(?P<tv>[ABC])_Bai(?P<bai>[1-5])\.(?P<duoi>py|ipynb)$", re.I)
MAU_TEN_HIDDEN = re.compile(r"hidden[_\- ]?(?P<tv>[ABC])(?![A-Za-z])", re.I)
CAC_PHAN = [(bai, tv) for bai in CAC_BAI for tv in "ABC"]
CAC_PHAN_HIDDEN = [(HIDDEN_BAI, tv) for tv in "ABC"]

DAT = "DAT"
KHONG_DAT = "KHONG_DAT"
CAN_REVIEW = "CAN_REVIEW"
DUYET_DAT = "DUYET_DAT"            # người chấm duyệt tay: đạt
DUYET_KHONG_DAT = "DUYET_KHONG_DAT"  # người chấm duyệt tay: không đạt

# Nhóm lý do trừ điểm, theo thứ tự ưu tiên khi một phần có nhiều lỗi
NHOM_LOI = {
    "khong_nop": "Không nộp code",
    "khong_dung_yeu_cau": "Code không đúng yêu cầu đề",
    "loi_chay": "Code lỗi, không chạy được",
    "khong_in": "Code chạy nhưng không in ra kết quả",
    "sai_dap_an": "Code in ra đáp án sai",
    "chua_xac_minh": "Chưa xác minh được code (chờ người chấm)",
    "checkpoint_sai": "Checkpoint không được công nhận vì output code chưa đúng",
    "duyet_khong_dat": "Người chấm duyệt: không đạt",
}

# Giây cho mỗi lần chạy code. Trên Vercel mỗi request tối đa 300 giây nên mặc định ngắn hơn.
THOI_GIAN_TOI_DA = int(os.environ.get("CHAM_THOI_GIAN") or (5 if os.environ.get("VERCEL") else 10))


def _chuan_so(s):
    x = float(s)
    return int(x) if x.is_integer() else x


def _cac_so(dong):
    return [_chuan_so(s) for s in re.findall(r"-?\d+(?:\.\d+)?", dong)]


def _chuan_chu(s):
    """Kết quả dạng chuỗi để so: bỏ khoảng trắng, chữ hoa ('70 nam' -> '70NAM')."""
    return re.sub(r"\s+", "", s or "").upper()


def co_output(stdout, phan):
    return bool(stdout.strip()) if phan.la_chuoi else bool(_cac_so(stdout))


def doc_gia_tri(stdout, chu, la_chuoi=False):
    """Ưu tiên dòng dạng 'A = 21' (chuỗi: 'MANH_A = UNETI'); nếu không có thì lấy số cuối cùng được in ra
    (chuỗi: phần sau dấu ':' / '=' của dòng cuối, hoặc cả dòng cuối)."""
    if la_chuoi:
        mau = re.findall(r"^\s*(?:M[AẢ]NH[ _]?)?%s\s*[=:]\s*(.+?)\s*$" % chu, stdout, re.M | re.I)
        if mau:
            return _chuan_chu(mau[-1]), "dung_mau"
        dong = [d for d in stdout.splitlines() if d.strip()]
        if not dong:
            return None, None
        return _chuan_chu(re.split(r"[:=]", dong[-1])[-1]) or _chuan_chu(dong[-1]), "so_cuoi"
    mau = re.findall(r"^\s*%s\s*[=:]\s*(-?\d+(?:\.\d+)?)\s*$" % chu, stdout, re.M | re.I)
    if mau:
        return _chuan_so(mau[-1]), "dung_mau"
    so = _cac_so(stdout)
    if so:
        return so[-1], "so_cuoi"
    return None, None


def so_sanh_output(goc, moi, dap_an, mong_doi):
    """Có dòng output nào đổi từ đáp án đề (bản gốc) sang đáp án test ẩn (bản đã thay dữ liệu) không.

    Không phụ thuộc thí sinh in theo định dạng nào hay file in kết quả của bao nhiêu phần.
    Kết quả dạng chuỗi (Hidden): bản gốc in ra đáp án đề và bản mới in ra đáp án test ẩn.
    """
    if isinstance(dap_an, str):
        return (any(dap_an in _chuan_chu(d) for d in goc.splitlines())
                and any(mong_doi in _chuan_chu(d) for d in moi.splitlines()))
    a, b = goc.splitlines(), moi.splitlines()

    def khung(dong):
        return re.sub(r"-?\d+(?:\.\d+)?", "#", dong).strip()

    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op != "replace":
            continue
        cap = list(zip(a[i1:i2], b[j1:j2]))
        cap += [(x, y) for x in a[i1:i2] for y in b[j1:j2] if khung(x) == khung(y)]
        for x, y in cap:
            if any(p == dap_an and q == mong_doi for p, q in zip(_cac_so(x), _cac_so(y))):
                return True
    return False


def _dong_cuoi(loi):
    return loi.strip().splitlines()[-1] if loi and loi.strip() else str(loi)


def _khong_trung(ds):
    return list(dict.fromkeys(ds))


def cham_phan(duong_dan, bai, tv, cac_phan_trong_file=()):
    phan = DE_THI[bai][tv]
    khac = [p for p in cac_phan_trong_file if p != (bai, tv)]
    kq = {"file": os.path.basename(duong_dan),
          "bo_cuc": "gộp chung với " + ", ".join("Bài %s %s" % p for p in khac) if khac else "file riêng",
          "mong_doi": phan.dap_an, "ket_qua": None,
          "diem": 0, "trang_thai": KHONG_DAT, "nhom_loi": None, "output_dung": False, "chay_duoc": False,
          "ly_do": [], "canh_bao": []}
    nhom_gap = []

    def loi(nhom, thong_diep):
        kq["ly_do"].append(thong_diep)
        nhom_gap.append(nhom)

    try:
        bai_lam = nap(duong_dan)
        cay = ast.parse(bai_lam.ma_nguon)
    except LoiNapFile as e:
        loi("loi_chay", str(e))
        kq["nhom_loi"] = "loi_chay"
        return kq
    except SyntaxError as e:
        loi("loi_chay", "Lỗi cú pháp dòng %s: %s" % (e.lineno, e.msg))
        kq["nhom_loi"] = "loi_chay"
        return kq
    kq["dinh_dang"] = "ipynb" if bai_lam.la_notebook else "py"

    node_phan = node_du_lieu(cay, phan.dau_vao)
    node_khac = [ns for ns in (node_du_lieu(cay, DE_THI[b][t].dau_vao) for b, t in khac) if ns]

    # 1. Kiểm tra tĩnh, trên vùng code của riêng phần này nếu file gộp
    if khac and node_phan:
        cay_tinh = vung_code(cay, node_phan, [n for ns in node_khac for n in ns])
    else:
        cay_tinh = cay
    for luat in phan.luat:
        for muc_do, thong_diep in luat(cay_tinh):
            if muc_do == LOI and khac and not node_phan:
                muc_do, thong_diep = CANH_BAO, thong_diep + " (file gộp, chưa xác định được vùng code của phần này)"
            elif muc_do == LOI and cay_tinh is not cay and getattr(luat, "yeu_cau", False) \
                    and not any(m == LOI for m, _ in luat(cay)):
                muc_do, thong_diep = CANH_BAO, thong_diep + " (trong vùng code tách được; file vẫn có ở chỗ khác)"
            if muc_do == LOI:
                loi("khong_dung_yeu_cau", thong_diep)
            else:
                kq["canh_bao"].append(thong_diep)

    # 2. Chọn chương trình để chạy: tách riêng phần này (nếu gộp), dự phòng chạy cả file
    lua_chon = []
    if khac and node_phan and node_khac:
        cay_rieng = tach_chuong_trinh(cay, node_phan, node_khac)
        if cay_rieng is not None:
            lua_chon.append(("tách riêng phần này", ast.unparse(cay_rieng), cay_rieng, True))
    lua_chon.append(("cả file", bai_lam.ma_nguon, cay, not khac))

    ten_bien = [tv] + ([phan.giu_nguyen] if phan.giu_nguyen else [])
    for i, (cach_chay, ma_nguon, cay_chay, chi_mot_phan) in enumerate(lua_chon):
        r = chay(ma_nguon, bai_lam.la_notebook, ten_bien, THOI_GIAN_TOI_DA)
        if (r.loi or not co_output(r.stdout, phan)) and i < len(lua_chon) - 1:
            continue
        break
    if khac:
        kq["cach_chay"] = cach_chay
    kq["stdout"] = r.stdout[-3000:]
    kq["chay_duoc"] = r.loi is None and co_output(r.stdout, phan)
    kq["tim_thay_du_lieu"] = sorted(tim_du_lieu(cay, phan.dau_vao))
    for o in r.loi_o:
        kq["canh_bao"].append("Ô code thứ %d lỗi khi chạy lại từ đầu (%s) - %s" % (
            o["o"], o["loi"][:150],
            "chạy lại sau các ô khác thì được, có thể thí sinh chạy các ô sai thứ tự" if o["chay_lai_duoc"]
            else "đã bỏ qua để chạy tiếp các ô sau"))
    kq["test_an"] = []

    if r.loi:
        loi("loi_chay", "Chạy lỗi: " + _dong_cuoi(r.loi))
        kq["loi_chay"] = r.loi
    elif not co_output(r.stdout, phan):
        loi("khong_in", "Không in ra kết quả")
    else:
        gia_tri_doc, cach_doc = doc_gia_tri(r.stdout, tv, phan.la_chuoi) if chi_mot_phan else (None, None)

        if chi_mot_phan and phan.giu_nguyen and phan.giu_nguyen in r.bien:
            try:
                sau_khi_chay = _tuple_hoa(ast.literal_eval(r.bien[phan.giu_nguyen]))
            except (ValueError, SyntaxError):
                sau_khi_chay = None
            if sau_khi_chay is not None and sau_khi_chay != _tuple_hoa(phan.goc[phan.giu_nguyen]):
                loi("khong_dung_yeu_cau", "Danh sách gốc `%s` bị thay đổi sau khi chạy - đề cấm" % phan.giu_nguyen)

        # 3. Test ẩn
        tim_thay = tim_du_lieu(cay_chay, phan.dau_vao)
        for j, thay_doi in enumerate(phan.test_an, 1):
            t = {"test": j, "thay": sorted(thay_doi), "mong_doi": phan.tham_chieu(**{**phan.goc, **thay_doi})}
            thieu = set(thay_doi) - tim_thay
            if thieu:
                t.update(ap_dung=False, ly_do="Không tìm thấy dữ liệu %s trong code" % ", ".join(sorted(thieu)))
            else:
                cay_moi, _ = thay_du_lieu(cay_chay, phan.dau_vao, thay_doi)
                rt = chay(ast.unparse(cay_moi), bai_lam.la_notebook, [tv], THOI_GIAN_TOI_DA)
                t["ap_dung"] = True
                t["dat"] = rt.loi is None and so_sanh_output(r.stdout, rt.stdout, phan.dap_an, t["mong_doi"])
                if chi_mot_phan:
                    t["thuc_te"] = doc_gia_tri(rt.stdout, tv, phan.la_chuoi)[0]
                if rt.loi:
                    t["loi"] = _dong_cuoi(rt.loi)
            kq["test_an"].append(t)

        ap_dung = [t for t in kq["test_an"] if t["ap_dung"]]
        truot = [t for t in ap_dung if not t["dat"]]
        if ap_dung and not truot:
            kq["ket_qua"] = phan.dap_an  # đã chứng minh: output đổi đúng theo dữ liệu
            kq["output_dung"] = True
            if len(ap_dung) < len(kq["test_an"]):
                kq["canh_bao"].append("Chỉ chạy được %d/%d test ẩn" % (len(ap_dung), len(kq["test_an"])))
        else:
            kq["ket_qua"] = gia_tri_doc
            if gia_tri_doc is not None and gia_tri_doc != phan.dap_an:
                loi("sai_dap_an", "In ra %s, đáp án là %s" % (gia_tri_doc, phan.dap_an))
            if truot:
                loi("sai_dap_an", "Trượt %d/%d test ẩn (đổi dữ liệu đầu vào nhưng kết quả sai) - "
                                  "thuật toán sai hoặc hard-code đáp án" % (len(truot), len(ap_dung)))
            if cach_doc == "so_cuoi":
                kq["canh_bao"].append("Không in theo dạng '%s = <giá trị>', đã lấy số cuối cùng trong output" % tv)

        if bai_lam.la_notebook and bai_lam.output_da_luu and not khac:
            da_luu, _ = doc_gia_tri(bai_lam.output_da_luu, tv, phan.la_chuoi)
            hien_tai = doc_gia_tri(r.stdout, tv, phan.la_chuoi)[0]
            if da_luu is not None and da_luu != hien_tai:
                kq["canh_bao"].append("Output lưu sẵn trong notebook (%s) khác kết quả chạy lại (%s) - "
                                      "output có thể đã bị sửa tay" % (da_luu, hien_tai))

    # 4. Kết luận
    kq["ly_do"] = _khong_trung(kq["ly_do"])
    kq["canh_bao"] = _khong_trung(kq["canh_bao"])
    if kq["ly_do"]:
        kq["diem"], kq["trang_thai"] = 0, KHONG_DAT
        kq["nhom_loi"] = min(nhom_gap, key=list(NHOM_LOI).index)
    elif not any(t["ap_dung"] for t in kq["test_an"]):
        kq["diem"], kq["trang_thai"], kq["nhom_loi"] = 0, CAN_REVIEW, "chua_xac_minh"
        kq["canh_bao"].append("Không tìm thấy dữ liệu đề cho trong code nên không chạy được test ẩn - "
                              "tạm 0 điểm, cần người xem code (có thể hard-code)")
    else:
        kq["diem"] = 1
        kq["trang_thai"] = CAN_REVIEW if kq["canh_bao"] else DAT
    return kq


def _goi_y_tu_ten(ten_file):
    """Các phần mà tên file gợi ý tới, vd D01_A_Bai1.py, bai_4_A.py, Bai2.ipynb, D01_Hidden_B.py."""
    m = MAU_TEN.match(ten_file)
    if m:
        return {(int(m["bai"]), m["tv"].upper())}
    goc = os.path.splitext(ten_file)[0]
    if "hidden" in goc.lower():
        m = MAU_TEN_HIDDEN.search(goc)
        return {(HIDDEN_BAI, m["tv"].upper())} if m else set(CAC_PHAN_HIDDEN)
    cac_bai = {int(b) for b in re.findall(r"b[aà]i\s*[_\- ]?\s*([1-5])", goc, re.I)}
    cac_tv = {t.upper() for t in re.findall(r"(?:^|[_\-\s.])([ABCabc])(?=[_\-\s.]|$)", goc)}
    if not cac_bai and not cac_tv:
        return set()
    return {(b, t) for b in (cac_bai or CAC_BAI) for t in (cac_tv or "ABC")}


def _chuan_thong_diep(s):
    s = (s or "").replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Za-z0-9]+", " ", s).strip().upper()


def _chuan_manh(s):
    """So mảnh / thông điệp Hidden: không dấu, bỏ dấu câu và khoảng trắng ('UNETI – 70 NĂM' -> 'UNETI70NAM')."""
    return _chuan_thong_diep(s).replace(" ", "")


def _so_hoac_none(x):
    try:
        return _chuan_so(x)
    except (TypeError, ValueError):
        return None


def ten_phan(p):
    return "Hidden %s" % p[1] if p[0] == HIDDEN_BAI else "Bài %d %s" % p


def tim_bo_cuc(thu_muc):
    """Xác định phần nào nằm ở file nào. Trả về ({(bài, tv): đường dẫn}, cảnh báo, file không xác định).

    Bài là 1..5 hoặc HIDDEN_BAI. File Hidden (có dữ liệu Hidden, hoặc tên chứa 'hidden' mà không có dữ liệu
    của 5 bài) chỉ được xét cho Hidden và ngược lại, để file Hidden không bị chấm nhầm thành bài thi.
    """
    cac_file = []
    for goc, thu_muc_con, ten_cac_file in os.walk(thu_muc):
        thu_muc_con[:] = [d for d in thu_muc_con if not d.startswith(".") and d != "__pycache__"]
        cac_file += [os.path.join(goc, f) for f in sorted(ten_cac_file) if f.lower().endswith((".py", ".ipynb"))]

    co_du_lieu = {}
    for duong_dan in cac_file:
        try:
            literal = cac_literal(ast.parse(nap(duong_dan).ma_nguon))  # duyệt code một lần cho cả 18 phần
        except (LoiNapFile, SyntaxError):
            continue
        co_du_lieu[duong_dan] = {p for p in CAC_PHAN + CAC_PHAN_HIDDEN
                                 if co_du_lieu_phan(literal, DE_THI[p[0]][p[1]].dau_vao)}

    goi_y = {f: _goi_y_tu_ten(os.path.basename(f)) for f in cac_file}

    def la_hidden(f):
        du_lieu = co_du_lieu.get(f, set())
        if any(p[0] == HIDDEN_BAI for p in du_lieu):
            return True
        return not du_lieu and any(p[0] == HIDDEN_BAI for p in goi_y[f])

    nhom = {False: [f for f in cac_file if not la_hidden(f)], True: [f for f in cac_file if la_hidden(f)]}
    vi_tri, canh_bao = {}, []
    for hidden, cac_phan in ((False, CAC_PHAN), (True, CAC_PHAN_HIDDEN)):
        for p in cac_phan:
            ung_vien = [f for f in nhom[hidden] if p in co_du_lieu.get(f, ())]
            if ung_vien:
                uu_tien = [f for f in ung_vien if p in goi_y[f]] or ung_vien
                vi_tri[p] = uu_tien[0]
                if len(ung_vien) > 1:
                    canh_bao.append("%s có trong nhiều file (%s), chấm file %s" % (
                        ten_phan(p), ", ".join(os.path.basename(f) for f in ung_vien), os.path.basename(uu_tien[0])))
            else:
                theo_ten = [f for f in nhom[hidden] if p in goi_y[f] and not co_du_lieu.get(f)]
                if theo_ten:
                    vi_tri[p] = theo_ten[0]
    khong_xac_dinh = [os.path.relpath(f, thu_muc) for f in cac_file if f not in vi_tri.values()]
    return vi_tri, canh_bao, khong_xac_dinh


def tim_phieu(thu_muc):
    """File Word phiếu trả lời trong thư mục bài nộp (bỏ file khóa tạm ~$ của Word)."""
    cac_file = sorted(f for f in os.listdir(thu_muc) if f.lower().endswith(".docx") and not f.startswith("~$"))
    if not cac_file:
        return None
    uu_tien = [f for f in cac_file if "phieu" in _chuan_thong_diep(f).lower()] or cac_file
    return os.path.join(thu_muc, uu_tien[0])


def nap_phieu(duong_dan):
    """Trả về (phiếu, cảnh báo khi đọc). Nhận .docx (mẫu BTC) hoặc .json."""
    if duong_dan.lower().endswith(".docx"):
        return doc_phieu(duong_dan)
    with open(duong_dan, encoding="utf-8") as f:
        return json.load(f), []


def _khong_nop(p):
    return {"file": None, "diem": 0, "trang_thai": KHONG_DAT, "nhom_loi": "khong_nop", "canh_bao": [],
            "output_dung": False, "chay_duoc": False,
            "ly_do": ["Không tìm thấy bài làm %s trong các file đã nộp" % ten_phan(p)]}


def _kiem_tra_tep(bai, vi_tri, phan_trong_file, thanh_vien, ma_doi):
    """Điểm tệp của một bài: đủ 3 tệp <MaDoi>_<A/B/C>_BaiN.py, mỗi phần một tệp, chạy được."""
    ly_do = []
    for tv in "ABC":
        dung_ten = "%s_%s_Bai%d.py" % (ma_doi, tv, bai)
        f = vi_tri.get((bai, tv))
        if not f:
            ly_do.append("Thiếu tệp phần %s (%s)" % (tv, dung_ten))
            continue
        ten = os.path.basename(f)
        if len(phan_trong_file[f]) > 1:
            ly_do.append("Phần %s nằm chung tệp %s với %s - đề yêu cầu mỗi phần một tệp" % (
                tv, ten, ", ".join(ten_phan(p) for p in phan_trong_file[f] if p != (bai, tv))))
        elif ten.lower() != dung_ten.lower():
            ly_do.append("Tệp phần %s đặt tên %s, đúng quy cách là %s" % (tv, ten, dung_ten))
        if not thanh_vien[tv].get("chay_duoc"):
            ly_do.append("Tệp %s %s" % (ten, "không in ra kết quả" if thanh_vien[tv].get("nhom_loi") == "khong_in"
                                        else "chạy lỗi"))
    return {"diem": int(not ly_do), "ly_do": _khong_trung(ly_do)}


def cham_doi(thu_muc, ma_doi=None, phieu=None, phieu_canh_bao=(), duyet_tay=None):
    """Chạy và kiểm tra code của đội (chậm), rồi tính điểm theo phiếu (nhanh, xem tinh_diem)."""
    vi_tri, canh_bao, khong_xac_dinh = tim_bo_cuc(thu_muc)
    if not ma_doi:
        theo_ten = [m["doi"] for m in (MAU_TEN.match(os.path.basename(f)) for f in vi_tri.values()) if m]
        ma_doi = Counter(theo_ten).most_common(1)[0][0] if theo_ten else os.path.basename(os.path.abspath(thu_muc))

    phan_trong_file = {}
    for p, f in vi_tri.items():
        phan_trong_file.setdefault(f, []).append(p)

    bao_cao = {"ma_doi": ma_doi,
               "bo_cuc": {os.path.relpath(f, thu_muc): [ten_phan(p) for p in ps] for f, ps in phan_trong_file.items()},
               "file_khong_xac_dinh": khong_xac_dinh, "canh_bao": canh_bao,
               "phieu_canh_bao": list(phieu_canh_bao), "bai": {}}
    for bai in CAC_BAI:
        b = {"thanh_vien": {}}
        for tv in "ABC":
            f = vi_tri.get((bai, tv))
            b["thanh_vien"][tv] = cham_phan(f, bai, tv, phan_trong_file[f]) if f else _khong_nop((bai, tv))
        gia_tri = [b["thanh_vien"][tv].get("ket_qua") for tv in "ABC"]
        b["k_tu_code"] = tinh_checkpoint(bai, *gia_tri) if None not in gia_tri else None
        b["nop_du"] = _kiem_tra_tep(bai, vi_tri, phan_trong_file, b["thanh_vien"], ma_doi)
        bao_cao["bai"][str(bai)] = b
    bao_cao["hidden"] = {"thanh_vien": {}}
    for tv in "ABC":
        p = (HIDDEN_BAI, tv)
        f = vi_tri.get(p)
        bao_cao["hidden"]["thanh_vien"][tv] = cham_phan(f, HIDDEN_BAI, tv, phan_trong_file[f]) if f else _khong_nop(p)
    return tinh_diem(bao_cao, phieu, duyet_tay)


def _ap_dung_duyet(p, quyet):
    """Kết quả tự động của một phần, hoặc kết luận duyệt tay (True/False) nếu có."""
    tu_dong = p.setdefault("tu_dong", {k: p.get(k) for k in ("diem", "output_dung", "trang_thai", "nhom_loi")})
    if quyet is None:
        p.update(tu_dong)
    else:
        p.update(diem=int(bool(quyet)), output_dung=bool(quyet),
                 trang_thai=DUYET_DAT if quyet else DUYET_KHONG_DAT,
                 nhom_loi=None if quyet else "duyet_khong_dat")


def tinh_diem(bao_cao, phieu, duyet_tay=None):
    """Tính (lại) điểm từ kết quả code đã chấm + phiếu + quyết định duyệt tay. Không chạy lại code.

    duyet_tay: {"2B": True/False, "3T": ..., "HA": ...} - người chấm kết luận đạt/không đạt cho phần đó
    (xT: điểm tệp của bài x, HA/HB/HC: code Hidden), thay kết quả tự động.
    """
    duyet_tay = duyet_tay or {}
    tong = 0
    for bai in CAC_BAI:
        b = bao_cao["bai"][str(bai)]
        for tv in "ABC":
            _ap_dung_duyet(b["thanh_vien"][tv], duyet_tay.get("%d%s" % (bai, tv)))
        tep = b["nop_du"]
        tep.setdefault("tu_dong", tep.get("diem", 0))
        tep["duyet"] = duyet_tay.get("%dT" % bai)
        tep["diem"] = tep["tu_dong"] if tep["duyet"] is None else int(bool(tep["duyet"]))

        # Bước 1: điểm theo phiếu trả lời
        pb = (phieu or {}).get("bai", {}).get(str(bai)) or {}
        b["phieu"] = {}
        for tv in "ABC":
            ghi = _so_hoac_none(pb.get(tv))
            b["phieu"][tv] = {"ghi": ghi, "dung": ghi == DE_THI[bai][tv].dap_an}
        k = _so_hoac_none(pb.get("K"))
        chu = str(pb.get("manh_khoa") or "").strip().upper()
        b["phieu"]["checkpoint"] = {"K": k, "manh_khoa": chu, "dung": k == DAP_AN_K[bai] and chu == MANH_KHOA[bai - 1]}
        b["diem_phieu"] = sum(v["dung"] for v in b["phieu"].values())

        # Phiếu là căn cứ chấm: ghi sai thì không có điểm mục đó, kể cả khi code đúng.
        b["phieu_sai"] = []
        if not pb:
            b["phieu_sai"].append({"muc": "Cả bài", "ly_do": "Chưa có phiếu trả lời cho bài này"})
        else:
            for tv in "ABC":
                if not b["phieu"][tv]["dung"]:
                    ghi = b["phieu"][tv]["ghi"]
                    b["phieu_sai"].append({"muc": tv, "ly_do": "Phiếu ghi %s, đáp án là %s%s" % (
                        "(trống/không đọc được)" if ghi is None else ghi, DE_THI[bai][tv].dap_an,
                        " (code đúng nhưng phiếu sai vẫn không được điểm)" if b["thanh_vien"][tv]["diem"] else "")})
            if not b["phieu"]["checkpoint"]["dung"]:
                b["phieu_sai"].append({"muc": "Checkpoint", "ly_do": "Phiếu ghi K = %s, mảnh khóa '%s'; đáp án K = %d, '%s'" % (
                    "(trống/không đọc được)" if k is None else k, chu, DAP_AN_K[bai], MANH_KHOA[bai - 1])})

        # Bước 2: code để xác thực - trừ những mục phiếu ghi đúng nhưng code không chứng minh được
        b["tru"] = []
        for tv in "ABC":
            p = b["thanh_vien"][tv]
            if not p["diem"] and b["phieu"][tv]["dung"]:
                if p["trang_thai"] == DUYET_KHONG_DAT:
                    chi_tiet = "; ".join(p["ly_do"] or p["canh_bao"]) or "theo kết luận của người chấm"
                else:
                    chi_tiet = "; ".join(p["ly_do"] or [c for c in p["canh_bao"] if "tạm 0" in c] or p["canh_bao"])
                b["tru"].append({"muc": tv, "nhom": p["nhom_loi"], "ly_do": "%s: %s" % (NHOM_LOI[p["nhom_loi"]], chi_tiet)})
        # Checkpoint chỉ bị kéo theo khi output code sai/không có (vi phạm yêu cầu đề mà output đúng thì không)
        sai = [tv for tv in "ABC" if not b["thanh_vien"][tv].get("output_dung")]
        b["phieu"]["checkpoint"]["cong_nhan"] = b["phieu"]["checkpoint"]["dung"] and not sai
        b["phieu"]["checkpoint"]["code_sai"] = sai
        if b["phieu"]["checkpoint"]["dung"] and sai:
            b["tru"].append({"muc": "Checkpoint", "nhom": "checkpoint_sai",
                             "ly_do": "%s (phần %s)" % (NHOM_LOI["checkpoint_sai"], ", ".join(sai))})

        b["diem"] = b["diem_phieu"] - len(b["tru"]) + tep["diem"]
        tong += b["diem"]

    bao_cao["hidden_challenge"] = _hidden_challenge(bao_cao, phieu or {}, duyet_tay)
    bao_cao["tong_diem"] = tong
    bao_cao["toi_da"] = 25
    return bao_cao


def _hidden_challenge(bao_cao, phieu, duyet_tay):
    """Hoàn thành Hidden = 3 mảnh trong phiếu đúng + thông điệp đúng + code từng mảnh được xác thực. Không cộng điểm."""
    code = (bao_cao.get("hidden") or {}).get("thanh_vien", {})
    for tv, p in code.items():
        _ap_dung_duyet(p, duyet_tay.get("H" + tv))
    ghi = phieu.get("hidden") or {}
    h = {"tung_phan": {}, "ly_do": [],
         "tu_khoa_dung": _chuan_manh(phieu.get("tu_khoa")) == TU_KHOA,
         "mat_khau_dung": _chuan_manh(phieu.get("mat_khau")) == MAT_KHAU,
         "thong_diep": phieu.get("thong_diep") or "",
         "thong_diep_dung": _chuan_manh(phieu.get("thong_diep")) == _chuan_manh(THONG_DIEP),
         "ghi_chu": "Không cộng điểm; khi bằng điểm, đội hoàn thành Hidden xếp trên, rồi tới đội nộp sớm hơn"}
    for tv in "ABC":
        p = code.get(tv) or {}
        muc = {"ghi": ghi.get(tv) or "", "dung": _chuan_manh(ghi.get(tv)) == HIDDEN[tv], "code_dat": bool(p.get("diem"))}
        h["tung_phan"][tv] = muc
        if not muc["dung"]:
            h["ly_do"].append("Phiếu ghi mảnh %s là '%s', đáp án '%s'" % (tv, muc["ghi"] or "(trống)", HIDDEN[tv]))
        if not muc["code_dat"]:
            h["ly_do"].append("Code Hidden %s chưa được xác thực: %s" % (
                tv, "; ".join(p.get("ly_do") or [c for c in p.get("canh_bao", []) if "tạm 0" in c])
                or "không có code"))
    # Như Checkpoint của 5 bài: output code của mảnh nào sai/không có thì thông điệp ghép cũng không được công nhận
    h["thong_diep_phieu_dung"] = h["thong_diep_dung"]
    h["code_sai"] = [tv for tv in "ABC" if not (code.get(tv) or {}).get("output_dung")]
    # Duyệt tay "HT": BTC kết luận thông điệp đội ghi có đúng không (vd ghi thêm chữ ngoài thông điệp đúng)
    h["duyet_thong_diep"] = duyet_tay.get("HT")
    if h["duyet_thong_diep"] is not None:
        h["thong_diep_phieu_dung"] = bool(h["duyet_thong_diep"])
    h["thong_diep_dung"] = h["thong_diep_phieu_dung"] and not h["code_sai"]
    if not h["thong_diep_phieu_dung"]:
        h["ly_do"].append("Thông điệp cuối '%s' chưa đúng" % (h["thong_diep"] or "(trống)"))
    elif h["code_sai"]:
        h["ly_do"].append("Thông điệp cuối không được công nhận vì output code Hidden %s chưa đúng"
                          % ", ".join(h["code_sai"]))
    h["hoan_thanh"] = not h["ly_do"]
    return h


def in_tom_tat(bc):
    print("Đội %s - tổng %d/%d" % (bc["ma_doi"], bc["tong_diem"], bc["toi_da"]))
    print("Phiếu trả lời: %s" % (bc.get("phieu_nguon") or "không có"))
    for c in bc.get("phieu_canh_bao", []):
        print("  ! " + c)
    print("Bố cục file:")
    for f, ps in bc["bo_cuc"].items():
        print("  %-28s -> %s" % (f, ", ".join(ps)))
    if bc["file_khong_xac_dinh"]:
        print("  File không xác định được là bài nào:", ", ".join(bc["file_khong_xac_dinh"]))
    print()
    print("%-5s %-26s %-10s %-5s %s" % ("Bài", "Theo phiếu (A B C K)", "Trừ (code)", "Tệp", "Điểm"))
    bi_tru, phieu_sai, can_xem, tep_sai = [], [], [], []
    for bai, b in bc["bai"].items():
        dau = " ".join("✓" if b["phieu"][m]["dung"] else "✗" for m in ("A", "B", "C", "checkpoint"))
        print("%-5s %-26s %-10s %-5s %d" % (bai, "%d/4  (%s)" % (b["diem_phieu"], dau),
                                            "-%d" % len(b["tru"]) if b["tru"] else "0", b["nop_du"]["diem"], b["diem"]))
        for t in b["tru"]:
            tv = t["muc"] if t["muc"] in "ABC" else None
            bi_tru.append(("Bài %s %s" % (bai, t["muc"]), b["thanh_vien"][tv].get("file") if tv else None, t["ly_do"]))
        phieu_sai += ["Bài %s %s: %s" % (bai, s["muc"], s["ly_do"]) for s in b["phieu_sai"]]
        if not b["nop_du"]["diem"]:
            tep_sai += ["Bài %s: %s" % (bai, x) for x in b["nop_du"]["ly_do"]]
        for tv in "ABC":
            p = b["thanh_vien"][tv]
            if p["diem"] and p["canh_bao"]:
                can_xem.append(("Bài %s %s" % (bai, tv), p.get("file"), p["canh_bao"]))
    for c in bc["canh_bao"]:
        can_xem.append(("Bố cục", None, [c]))
    if phieu_sai:
        print("\nMất điểm do phiếu ghi sai:")
        for s in phieu_sai:
            print("  - " + s)
    if bi_tru:
        print("\nBị trừ điểm do code không xác thực được:")
        for ten, f, ly_do in bi_tru:
            print("  - %s%s: %s" % (ten, " [%s]" % f if f else "", ly_do))
    if tep_sai:
        print("\nMất điểm tệp (đủ 3 tệp đặt tên đúng, chạy được):")
        for s in tep_sai:
            print("  - " + s)
    h = bc.get("hidden_challenge")
    if h:
        print("\nHidden Challenge (không cộng điểm): %s" % ("HOÀN THÀNH" if h["hoan_thanh"] else "chưa hoàn thành"))
        for x in h["ly_do"]:
            print("  - " + x)
    if can_xem:
        print("\nĐược điểm nhưng có cảnh báo, nên xem lại:")
        for ten, f, ds in can_xem:
            print("  - %s%s:" % (ten, " [%s]" % f if f else ""))
            for d in ds:
                print("      * " + d)


def main():
    global THOI_GIAN_TOI_DA
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Chấm tự động Vòng 1 Olympic AI UNETI 2026")
    ap.add_argument("thu_muc", help="Thư mục chứa bài nộp của một đội")
    ap.add_argument("--phieu", help="Phiếu trả lời của đội (.docx theo mẫu BTC hoặc .json); "
                                    "mặc định lấy file .docx trong thư mục bài nộp")
    ap.add_argument("--ma-doi", help="Mã đội (mặc định đoán từ tên file / tên thư mục)")
    ap.add_argument("--json", help="Ghi báo cáo chi tiết ra file JSON")
    ap.add_argument("--thoi-gian", type=int, default=THOI_GIAN_TOI_DA, help="Giới hạn giây cho mỗi lần chạy")
    args = ap.parse_args()
    THOI_GIAN_TOI_DA = args.thoi_gian

    phieu, phieu_canh_bao = None, []
    duong_dan_phieu = args.phieu or tim_phieu(args.thu_muc)
    if duong_dan_phieu:
        try:
            phieu, phieu_canh_bao = nap_phieu(duong_dan_phieu)
        except LoiDocPhieu as e:
            phieu_canh_bao = [str(e)]
    bc = cham_doi(args.thu_muc, args.ma_doi or (phieu or {}).get("ma_doi"), phieu, phieu_canh_bao)
    bc["phieu_nguon"] = os.path.basename(duong_dan_phieu) if duong_dan_phieu else None
    in_tom_tat(bc)
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(bc, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
