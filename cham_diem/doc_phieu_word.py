"""Đọc phiếu trả lời của đội từ file Word (.docx) theo mẫu BTC, chuyển thành dict phiếu cho engine.

Chỉ dùng thư viện chuẩn. Bảng / đoạn được nhận ra theo tiêu đề, nhãn (không theo thứ tự), nên đội có
thêm/bớt đoạn văn vẫn đọc được. Dòng chấm "......" của mẫu được bỏ đi, nên đội gõ đè lên hay gõ chèn vào
giữa dòng chấm đều được. Ô ghi sai định dạng không bị đoán: giá trị None (tính là sai) kèm cảnh báo để
người chấm xem lại.

Mẫu phiếu (Olympic AI UNETI 2026 - Phiếu trả lời.docx):
  I.   bảng "Trường thông tin | Nội dung": Mã đội, Tên đội, ...
  II.  bảng "Bài | Kết quả A | Kết quả B | Kết quả C | Checkpoint | Mảnh khóa" (ô Checkpoint dạng "K1 = 21")
  III. đoạn "TỪ KHÓA BÍ MẬT: ...", "MẬT KHẨU MỞ HIDDEN CHALLENGE: ..."
  IV.  bảng "Thành viên | Mảnh thông điệp khôi phục | Xác nhận mã nguồn" và các đoạn sau
       "THÔNG ĐIỆP CUỐI CÙNG CỦA ĐỘI:".
"""
import re
import unicodedata
import zipfile
from xml.etree import ElementTree as ET

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


class LoiDocPhieu(Exception):
    pass


def _chu(node):
    phan = []
    for n in node.iter():
        if n.tag == W + "t" and n.text:
            phan.append(n.text)
        elif n.tag in (W + "tab", W + "br"):
            phan.append(" ")
    return "".join(phan)


def _o(tc):
    return " ".join(_chu(p) for p in tc.iter(W + "p")).strip()


def _chuan(s):
    """'Kết quả giải mã – Thành viên A' -> 'KET QUA GIAI MA THANH VIEN A' (để so nhãn)."""
    s = s.replace("đ", "d").replace("Đ", "D")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"[^A-Z0-9]+", " ", s.upper()).strip()


def _sach(s):
    """Bỏ dòng chấm của mẫu ('....', '…', '___'), ô đánh dấu, khoảng trắng thừa."""
    s = re.sub(r"\.{2,}|…+|_{2,}|[☐☑☒]", " ", s or "")
    return " ".join(s.split()).strip(" :")


def _sau_nhan(doan):
    """'TỪ KHÓA BÍ MẬT:  UNETI....' -> 'UNETI'."""
    return _sach(doan.split(":", 1)[1]) if ":" in doan else ""


def _doc_so(gt, ten_o, canh_bao):
    s = _sach(gt).replace(" ", "")
    if not s:
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    canh_bao.append("Ô '%s' ghi '%s' - không phải một số nguyên, tính là sai (cần người chấm xem lại)" % (ten_o, gt))
    return None


def _doc_chu_cai(gt, ten_o, canh_bao):
    s = _sach(gt).upper()
    if not s:
        return None
    if re.fullmatch(r"[A-Z]", s):
        return s
    canh_bao.append("Ô '%s' ghi '%s' - không phải một chữ cái A-Z, tính là sai (cần người chấm xem lại)" % (ten_o, gt))
    return None


def _bang_ket_qua(hang, tieu_de, phieu, canh_bao):
    cot = {}
    for j, c in enumerate(tieu_de):
        for tv in "ABC":
            if c == "KET QUA " + tv:
                cot[tv] = j
        if "CHECKPOINT" in c:
            cot["K"] = j
        elif "MANH KHOA" in c:
            cot["manh_khoa"] = j
    for h in hang[1:]:
        m = re.search(r"\bBAI ([1-5])\b", _chuan(h[0])) if h else None
        if not m:
            continue
        bai, muc = m.group(1), {}
        for khoa, j in cot.items():
            gt = h[j] if j < len(h) else ""
            if khoa == "manh_khoa":
                muc[khoa] = _doc_chu_cai(gt, "Bài %s - Mảnh khóa" % bai, canh_bao)
            elif khoa == "K":
                gt = re.sub(r"^\s*K\s*[1-5]?\s*[=:]", "", _sach(gt), flags=re.I)  # mẫu ghi sẵn "K1 = ...."
                muc[khoa] = _doc_so(gt, "Bài %s - Checkpoint (K)" % bai, canh_bao)
            else:
                muc[khoa] = _doc_so(gt, "Bài %s - Kết quả %s" % (bai, khoa), canh_bao)
        phieu["bai"][bai] = muc


def doc_phieu(duong_dan):
    """Trả về (phiếu dạng dict như phieu.json, danh sách cảnh báo khi đọc). duong_dan: đường dẫn hoặc file-like."""
    try:
        with zipfile.ZipFile(duong_dan) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        raise LoiDocPhieu("Không đọc được file Word %s: %s" % (getattr(duong_dan, "name", duong_dan), e))

    body = ET.fromstring(xml).find(W + "body")
    phieu = {"bai": {}, "hidden": {}}
    canh_bao = []
    doan_truoc = ""
    thong_diep, dang_gom = None, False  # gom các đoạn sau "THÔNG ĐIỆP CUỐI CÙNG" (mẫu mới)
    for el in body:
        if el.tag == W + "p":
            t = _chu(el).strip()
            if not t:
                continue
            nhan = _chuan(t)
            if dang_gom and re.match(r"^(I|II|III|IV|V|VI)\b", nhan):
                dang_gom = False  # sang mục khác
            if nhan.startswith("TU KHOA BI MAT"):
                phieu["tu_khoa"] = _sau_nhan(t)
            elif nhan.startswith("MAT KHAU"):
                phieu["mat_khau"] = _sau_nhan(t)
            elif "THONG DIEP CUOI CUNG" in nhan:
                thong_diep, dang_gom = [_sau_nhan(t)], True
            elif dang_gom:
                thong_diep.append(_sach(t))
            doan_truoc = nhan
            continue
        if el.tag != W + "tbl":
            continue
        dang_gom = False
        hang = [[_o(tc) for tc in tr.findall(W + "tc")] for tr in el.findall(W + "tr")]
        if not hang:
            continue
        tieu_de = [_chuan(c) for c in hang[0]]

        # Bảng kết quả 5 bài: cột được xác định theo tiêu đề
        if any("KET QUA A" in c for c in tieu_de) and any("CHECKPOINT" in c for c in tieu_de):
            _bang_ket_qua(hang, tieu_de, phieu, canh_bao)
            continue

        # Bảng Hidden: "Thành viên | Mảnh thông điệp khôi phục | ..."
        if any("MANH THONG DIEP" in c for c in tieu_de):
            for h in hang[1:]:
                if len(h) >= 2 and _chuan(h[0]) in ("A", "B", "C"):
                    phieu["hidden"][_chuan(h[0])] = _sach(h[1])
            continue

        # Mẫu cũ: thông điệp cuối là bảng một ô ngay sau tiêu đề "THÔNG ĐIỆP CUỐI CÙNG"
        if len(hang) == 1 and len(hang[0]) == 1 and "THONG DIEP CUOI CUNG" in doan_truoc:
            phieu["thong_diep"] = _sach(hang[0][0])
            continue

        # Các bảng nhãn - giá trị
        for h in hang:
            if len(h) < 2:
                continue
            nhan = _chuan(h[0])
            if nhan.startswith("MA DOI"):
                phieu["ma_doi"] = _sach(h[1])
                if len(h) >= 4 and _chuan(h[2]).startswith("TEN DOI"):
                    phieu["ten_doi"] = _sach(h[3])
            elif nhan.startswith("TEN DOI"):
                phieu["ten_doi"] = _sach(h[1])
            elif nhan.startswith("TU KHOA BI MAT"):
                phieu["tu_khoa"] = _sach(h[1])
            elif nhan.startswith("MAT KHAU"):
                phieu["mat_khau"] = _sach(h[1])
            elif "GIAI MA" in nhan:
                m = re.search(r"THANH VIEN ([ABC])\b", nhan)
                if m:
                    phieu["hidden"][m.group(1)] = _sach(h[1])
    if thong_diep is not None and not phieu.get("thong_diep"):
        phieu["thong_diep"] = " ".join(x for x in thong_diep if x)
    phieu.setdefault("thong_diep", "")

    if not phieu["bai"]:
        canh_bao.append("Không tìm thấy bảng 'Kết quả 05 bài thi' trong phiếu - phiếu có thể đã bị sửa mẫu")
    return phieu, canh_bao
