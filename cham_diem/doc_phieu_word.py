"""Đọc phiếu trả lời của đội từ file Word (.docx) theo mẫu BTC, chuyển thành dict phiếu cho engine.

Chỉ dùng thư viện chuẩn. Bảng được nhận ra theo tiêu đề/nhãn (không theo thứ tự), nên đội có
thêm/bớt đoạn văn vẫn đọc được. Ô ghi sai định dạng không bị đoán: giá trị None (tính là sai)
kèm cảnh báo để người chấm xem lại.
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


def _doc_so(gt, ten_o, canh_bao):
    s = gt.replace(" ", "")
    if not s:
        return None
    if re.fullmatch(r"-?\d+", s):
        return int(s)
    canh_bao.append("Ô '%s' ghi '%s' - không phải một số nguyên, tính là sai (cần người chấm xem lại)" % (ten_o, gt))
    return None


def _doc_chu_cai(gt, ten_o, canh_bao):
    s = gt.strip().upper()
    if not s:
        return None
    if re.fullmatch(r"[A-Z]", s):
        return s
    canh_bao.append("Ô '%s' ghi '%s' - không phải một chữ cái A-Z, tính là sai (cần người chấm xem lại)" % (ten_o, gt))
    return None


def doc_phieu(duong_dan):
    """Trả về (phiếu dạng dict như phieu.json, danh sách cảnh báo khi đọc)."""
    try:
        with zipfile.ZipFile(duong_dan) as z:
            xml = z.read("word/document.xml")
    except (zipfile.BadZipFile, KeyError, OSError) as e:
        raise LoiDocPhieu("Không đọc được file Word %s: %s" % (duong_dan, e))

    body = ET.fromstring(xml).find(W + "body")
    phieu = {"bai": {}, "hidden": {}}
    canh_bao = []
    doan_truoc = ""
    for el in body:
        if el.tag == W + "p":
            t = _chu(el).strip()
            if t:
                doan_truoc = _chuan(t)
            continue
        if el.tag != W + "tbl":
            continue
        hang = [[_o(tc) for tc in tr.findall(W + "tc")] for tr in el.findall(W + "tr")]
        if not hang:
            continue
        tieu_de = [_chuan(c) for c in hang[0]]

        # Bảng kết quả 5 bài: cột được xác định theo tiêu đề
        if any("KET QUA A" in c for c in tieu_de) and any("CHECKPOINT" in c for c in tieu_de):
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
                    else:
                        ten = "Checkpoint (K)" if khoa == "K" else "Kết quả " + khoa
                        muc[khoa] = _doc_so(gt, "Bài %s - %s" % (bai, ten), canh_bao)
                phieu["bai"][bai] = muc
            continue

        # Thông điệp cuối: bảng một ô ngay sau tiêu đề "THÔNG ĐIỆP CUỐI CÙNG"
        if len(hang) == 1 and len(hang[0]) == 1 and "THONG DIEP CUOI CUNG" in doan_truoc:
            phieu["thong_diep"] = hang[0][0]
            continue

        # Các bảng nhãn - giá trị
        for h in hang:
            if len(h) < 2:
                continue
            nhan = _chuan(h[0])
            if nhan.startswith("MA DOI"):
                phieu["ma_doi"] = h[1]
                if len(h) >= 4 and _chuan(h[2]).startswith("TEN DOI"):
                    phieu["ten_doi"] = h[3]
            elif nhan.startswith("TU KHOA BI MAT"):
                phieu["tu_khoa"] = h[1]
            elif nhan.startswith("MAT KHAU"):
                phieu["mat_khau"] = h[1]
            elif "GIAI MA" in nhan:
                m = re.search(r"THANH VIEN ([ABC])\b", nhan)
                if m:
                    phieu["hidden"][m.group(1)] = h[1]

    if not phieu["bai"]:
        canh_bao.append("Không tìm thấy bảng 'Kết quả 05 bài thi' trong phiếu - phiếu có thể đã bị sửa mẫu")
    return phieu, canh_bao
