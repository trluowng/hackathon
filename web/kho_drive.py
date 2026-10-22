"""Lưu trữ trên Google Drive cá nhân - dùng khi deploy lên nơi không có ổ đĩa lâu dài (vd Vercel).

Cấu trúc trong thư mục gốc (DRIVE_FOLDER_ID, tạo bằng lay_token_drive.py):
  bai_nop/<MÃ>_<ngày-giờ>/    mỗi lần nộp một thư mục. Nhãn (appProperties) của thư mục giữ thông tin
                              để liệt kê nhanh: mã đội, giờ nộp, nộp lỗi, trạng thái chấm, điểm tóm tắt.
      <MÃ>_Bai1.py ... <MÃ>_PhieuTraLoi.docx, thong_tin.json, ket_qua.json, duyet.json
  cai_dat.json   hạn nộp, mở/khóa nộp
  doi.json       đội admin thêm trước / đã xóa
Mỗi lần nộp là một thư mục riêng nên nhiều đội nộp cùng lúc không ghi đè nhau.
"""
import json
import os
import secrets
import shutil
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from gio import bay_gio
from tom_tat import tinh_tom_tat

THU_MUC_TAM = os.path.join(tempfile.gettempdir(), "olympic")
JSON = "application/json"
MIME = {".py": "text/x-python", ".ipynb": JSON,
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


def _tao_drive():
    if os.environ.get("KHO") == "drive_gia":  # bản giả lập để chạy test, không gọi Google
        from drive_gia import DriveGia
        return DriveGia.chung()
    from drive_api import DriveApi
    return DriveApi()


_drive = _tao_drive()
_khoa = threading.Lock()
_id = {}       # id thư mục gốc và các thành phần: goc, bai_nop, cai_dat, doi
_bo_nho = {}   # bộ nhớ tạm trong tiến trình: khóa -> (hết hạn, giá trị)


def _nho(khoa, giay, ham):
    now = time.time()
    muc = _bo_nho.get(khoa)
    if muc and muc[0] > now:
        return muc[1]
    gia_tri = ham()
    _bo_nho[khoa] = (now + giay, gia_tri)
    return gia_tri


def _quen(*khoa):
    for k in khoa:
        _bo_nho.pop(k, None)


def _doc_json(file_id):
    return json.loads(_drive.tai_ve(file_id) or b"{}")


def _ghi_json(file_id, du_lieu):
    _drive.ghi_de(file_id, json.dumps(du_lieu, ensure_ascii=False).encode(), JSON)


def _tao_json(ten, cha, du_lieu, nhan=None):
    return _drive.tai_len(ten, cha, json.dumps(du_lieu, ensure_ascii=False).encode(), JSON, nhan)


def _cat(khoa, chuoi):
    """Nhãn Drive giới hạn 124 byte cho khóa + giá trị."""
    du = 124 - len(khoa.encode())
    while len(chuoi.encode()) > du:
        chuoi = chuoi[:-1]
    return chuoi


def khoi_tao():
    with _khoa:
        if _id:
            return
        goc = os.environ.get("DRIVE_FOLDER_ID")
        if not goc:
            ds = _drive.tim_theo_nhan({"olympic": "goc"})
            goc = ds[0]["id"] if ds else _drive.tao_thu_muc("OlympicAI_Vong1", None, {"olympic": "goc"})
        # Lỡ có bản trùng (nhiều tiến trình cùng tạo lúc mới deploy) thì mọi nơi đều chọn bản tạo sớm nhất
        thanh_phan = {}
        for f in sorted(_drive.con(goc), key=lambda f: (str(f.get("createdTime") or ""), f["id"])):
            loai = (f.get("appProperties") or {}).get("olympic")
            if loai and loai not in thanh_phan:
                thanh_phan[loai] = f["id"]
        if "bai_nop" not in thanh_phan:
            thanh_phan["bai_nop"] = _drive.tao_thu_muc("bai_nop", goc, {"olympic": "bai_nop"})
        for ten in ("cai_dat", "doi"):
            if ten not in thanh_phan:
                thanh_phan[ten] = _tao_json(ten + ".json", goc, {}, {"olympic": ten})
        _id.update(thanh_phan, goc=goc)


# ---------- Cài đặt ----------

def doc_cai_dat(khoa, mac_dinh=None):
    return _nho("cai_dat", 10, lambda: _doc_json(_id["cai_dat"])).get(khoa, mac_dinh)


def ghi_cai_dat(khoa, gia_tri):
    du_lieu = _doc_json(_id["cai_dat"])
    du_lieu[khoa] = gia_tri
    _ghi_json(_id["cai_dat"], du_lieu)
    _quen("cai_dat")


def khoa_phien():
    khoa = os.environ.get("PHIEN_BI_MAT") or doc_cai_dat("khoa_phien")
    if not khoa:
        khoa = secrets.token_hex(32)
        ghi_cai_dat("khoa_phien", khoa)
    return khoa


# ---------- Lần nộp: liệt kê bằng nhãn thư mục (một lần gọi Drive cho mọi đội) ----------

def _ds_nhan():
    def tai():
        ds = []
        for f in _drive.con(_id["bai_nop"], chi_thu_muc=True):
            nhan = f.get("appProperties") or {}
            if nhan.get("olympic") == "lan_nop":
                ds.append(dict(nhan, id=f["id"]))
        return sorted(ds, key=lambda n: (n.get("thoi_gian", ""), n["id"]))
    return _nho("lan_nop", 3, tai)


def _cua_doi(ma_doi):
    """[(lần thứ mấy, nhãn)] của đội, cũ nhất trước."""
    return list(enumerate((n for n in _ds_nhan() if n.get("ma_doi") == ma_doi), 1))


def _tim(lan_nop_id):
    for lan in range(2):
        for n in _ds_nhan():
            if n["id"] == lan_nop_id:
                return n
        _quen("lan_nop")  # có thể vừa được tạo ở tiến trình khác
    return None


def _so_thu_tu(nhan):
    return next(so for so, n in _cua_doi(nhan["ma_doi"]) if n["id"] == nhan["id"])


def _nhe(nhan, so):
    """Thông tin lấy ngay từ nhãn, không tải file."""
    return {"id": nhan["id"], "ma_doi": nhan["ma_doi"], "thoi_gian": nhan.get("thoi_gian", ""),
            "thu_muc": nhan["id"], "hidden_dung": nhan.get("hidden") == "1",
            "loi_nop": ["(nộp lỗi)"] if nhan.get("loi") == "1" else None,
            "cac_file": [], "kiem_tra": {}, "so": so, "_file": {}}


def _day_du(nhan, so):
    d = _nhe(nhan, so)
    if nhan.get("f_tt"):
        tt = _doc_json(nhan["f_tt"])
        d.update(cac_file=tt.get("cac_file", []), kiem_tra=tt.get("kiem_tra", {}), _file=tt.get("file_id", {}),
                 loi_nop=tt.get("loi_nop") or d["loi_nop"], ten_doi=tt.get("ten_doi", ""))
    return d


def tao_thu_muc_nop(ma_doi, thoi_gian):
    """Thư mục tạm trên máy để app ghi file trước khi đưa lên Drive."""
    thu_muc = os.path.join(THU_MUC_TAM, "nop", "%s_%s_%s" % (ma_doi, thoi_gian.strftime("%Y%m%d-%H%M%S-%f"),
                                                            secrets.token_hex(3)))
    os.makedirs(thu_muc)
    return thu_muc


def them_lan_nop(ma_doi, thoi_gian, thu_muc, cac_file, kiem_tra, hidden_dung, loi_nop=None, ten_doi=""):
    nhan = {"olympic": "lan_nop", "ma_doi": ma_doi, "thoi_gian": thoi_gian, "loi": "1" if loi_nop else "0",
            "hidden": "1" if hidden_dung else "0", "ten_doi": _cat("ten_doi", ten_doi)}
    ten = "%s_%s" % (ma_doi, datetime.fromisoformat(thoi_gian).strftime("%Y%m%d-%H%M%S"))
    tm = _drive.tao_thu_muc(ten, _id["bai_nop"], nhan)

    def len_mot(ten_file):
        with open(os.path.join(thu_muc, ten_file), "rb") as f:
            return ten_file, _drive.tai_len(ten_file, tm, f.read(), MIME.get(os.path.splitext(ten_file)[1],
                                                                                "application/octet-stream"))

    with ThreadPoolExecutor(4) as ex:
        file_id = dict(ex.map(len_mot, cac_file))
    f_tt = _tao_json("thong_tin.json", tm, {"cac_file": cac_file, "kiem_tra": kiem_tra, "loi_nop": loi_nop,
                                            "ten_doi": ten_doi, "file_id": file_id})
    _drive.sua_nhan(tm, {"f_tt": f_tt})
    shutil.rmtree(thu_muc, ignore_errors=True)
    _quen("lan_nop")
    return tm


def lay_lan_nop(lan_nop_id):
    nhan = _tim(lan_nop_id)
    return _day_du(nhan, _so_thu_tu(nhan)) if nhan else None


def ds_lan_nop(ma_doi):
    """Các lần nộp của đội, mới nhất trước (tải thông tin chi tiết song song)."""
    cua_doi = list(reversed(_cua_doi(ma_doi)))
    with ThreadPoolExecutor(8) as ex:
        return list(ex.map(lambda x: _day_du(x[1], x[0]), cua_doi))


def dem_lan_nop(ma_doi):
    return len(_cua_doi(ma_doi))


def lan_nop_moi_nhat(ma_doi, ca_nop_loi=False):
    for so, nhan in reversed(_cua_doi(ma_doi)):
        if ca_nop_loi or nhan.get("loi") != "1":
            return _nhe(nhan, so)
    return None


def hidden_dung_som_nhat(ma_doi):
    ds = [n["thoi_gian"] for _, n in _cua_doi(ma_doi) if n.get("hidden") == "1" and n.get("loi") != "1"]
    return min(ds) if ds else None


def thu_muc_lam_viec(lan_nop):
    """Tải file của lần nộp từ Drive về thư mục tạm để chấm."""
    dich = os.path.join(THU_MUC_TAM, "cham", lan_nop["id"])
    os.makedirs(dich, exist_ok=True)

    def tai(muc):
        ten_file, file_id = muc
        duong_dan = os.path.join(dich, ten_file)
        if not os.path.exists(duong_dan):
            with open(duong_dan, "wb") as f:
                f.write(_drive.tai_ve(file_id))

    with ThreadPoolExecutor(4) as ex:
        list(ex.map(tai, lan_nop.get("_file", {}).items()))
    return dich


def doc_file(lan_nop, ten):
    return _drive.tai_ve(lan_nop["_file"][ten])


# ---------- Kết quả chấm ----------

def _nhan_tom_tat(tom_tat):
    return {"tong": str(tom_tat["tong"]), "diem_bai": ",".join(map(str, tom_tat["diem_bai"])),
            "cho_duyet": str(tom_tat["cho_duyet"]), "nen_xem": str(tom_tat["nen_xem"])}


def dat_ket_qua(lan_nop_id, trang_thai, bao_cao=None, phieu=None, loi=None):
    nhan = _tim(lan_nop_id)
    sua = {"tt": trang_thai}
    if bao_cao is not None or loi is not None:
        du_lieu = {"trang_thai": trang_thai, "cap_nhat": bay_gio(), "bao_cao": bao_cao, "phieu": phieu, "loi": loi}
        if nhan.get("f_kq"):
            _ghi_json(nhan["f_kq"], du_lieu)
        else:
            sua["f_kq"] = _tao_json("ket_qua.json", lan_nop_id, du_lieu)
        if trang_thai == "da_cham":
            duyet = {p: bool(r["dat"]) for p, r in ds_duyet(lan_nop_id).items()}
            sua.update(_nhan_tom_tat(tinh_tom_tat(du_lieu, duyet)))
    _drive.sua_nhan(lan_nop_id, sua)
    _quen("lan_nop")


def lay_ket_qua(lan_nop_id):
    nhan = _tim(lan_nop_id)
    if not nhan or not nhan.get("tt"):
        return None
    kq = {"trang_thai": nhan["tt"], "cap_nhat": None, "bao_cao": None, "phieu": None, "loi": None}
    if nhan.get("f_kq"):
        da_luu = _doc_json(nhan["f_kq"])
        kq.update({k: da_luu.get(k) for k in ("cap_nhat", "bao_cao", "phieu", "loi")})
    return kq


def ds_chua_xong():
    return [n["id"] for n in _ds_nhan() if n.get("tt") in ("cho_cham", "dang_cham")]


def lay_tom_tat(lan_nop_id):
    """Đọc ngay từ nhãn thư mục (không tải báo cáo) - đủ nhanh cho trang tổng quan nhiều đội."""
    nhan = _tim(lan_nop_id) or {}
    tom_tat = {"trang_thai": nhan.get("tt") or "chua_cham", "tong": None, "diem_bai": [], "cho_duyet": 0, "nen_xem": 0}
    if tom_tat["trang_thai"] == "da_cham" and nhan.get("tong") not in (None, "", "None"):
        tom_tat.update(tong=int(nhan["tong"]), diem_bai=[int(x) for x in nhan.get("diem_bai", "").split(",") if x],
                       cho_duyet=int(nhan.get("cho_duyet", 0)), nen_xem=int(nhan.get("nen_xem", 0)))
    return tom_tat


# ---------- Duyệt tay ----------

def ds_duyet(lan_nop_id):
    nhan = _tim(lan_nop_id)
    return _doc_json(nhan["f_dt"]) if nhan and nhan.get("f_dt") else {}


def duyet(lan_nop_id, phan, dat, ghi_chu=""):
    nhan = _tim(lan_nop_id)
    ds = ds_duyet(lan_nop_id)
    if dat is None:
        ds.pop(phan, None)
    else:
        ds[phan] = {"phan": phan, "dat": int(dat), "ghi_chu": ghi_chu, "thoi_gian": bay_gio()}
    sua = {}
    if nhan.get("f_dt"):
        _ghi_json(nhan["f_dt"], ds)
    else:
        sua["f_dt"] = _tao_json("duyet.json", lan_nop_id, ds)
    kq = lay_ket_qua(lan_nop_id)
    if kq and kq["trang_thai"] == "da_cham" and kq["bao_cao"]:
        sua.update(_nhan_tom_tat(tinh_tom_tat(kq, {p: bool(r["dat"]) for p, r in ds.items()})))
    if sua:
        _drive.sua_nhan(lan_nop_id, sua)
    _quen("lan_nop")


# ---------- Đội: ghép từ doi.json (admin thêm/xóa) và các lần nộp ----------

def _doi_json():
    return _nho("doi", 10, lambda: _doc_json(_id["doi"]))


def _sua_doi_json(ham):
    du_lieu = _doc_json(_id["doi"])
    du_lieu.setdefault("ds", {})
    du_lieu.setdefault("an", {})
    ham(du_lieu)
    _ghi_json(_id["doi"], du_lieu)
    _quen("doi")


def luu_doi(ma_doi, ten_doi="", tu_nop=False):
    if tu_nop:
        return  # đội nộp bài: thông tin đã nằm trong nhãn lần nộp, không ghi doi.json (tránh ghi đè khi nộp cùng lúc)

    def sua(d):
        cu = d["ds"].get(ma_doi, {})
        d["ds"][ma_doi] = {"ten": ten_doi or cu.get("ten", "")}
        d["an"].pop(ma_doi, None)
    _sua_doi_json(sua)


def xoa_doi(ma_doi):
    def sua(d):
        d["ds"].pop(ma_doi, None)
        d["an"][ma_doi] = bay_gio()  # đội nộp lại sau thời điểm này sẽ hiện lại
    _sua_doi_json(sua)


def ds_doi():
    dj = _doi_json()
    doi = {ma: {"ma_doi": ma, "ten_doi": v.get("ten", "")} for ma, v in dj.get("ds", {}).items()}
    moi_nhat = {}
    for n in _ds_nhan():
        muc = doi.setdefault(n["ma_doi"], {"ma_doi": n["ma_doi"], "ten_doi": ""})
        if n.get("ten_doi") and (n.get("loi") != "1" or not muc["ten_doi"]) and n["ma_doi"] not in dj.get("ds", {}):
            muc["ten_doi"] = n["ten_doi"]
        moi_nhat[n["ma_doi"]] = n.get("thoi_gian", "")
    for ma, luc_xoa in dj.get("an", {}).items():
        if moi_nhat.get(ma, "") <= luc_xoa:
            doi.pop(ma, None)
    return sorted(doi.values(), key=lambda d: d["ma_doi"])


def lay_doi(ma_doi):
    return next((d for d in ds_doi() if d["ma_doi"] == ma_doi), None)
