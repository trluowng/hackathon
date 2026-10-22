"""Lưu trữ qua Google Apps Script (apps_script/Code.gs).

Apps Script giữ trang nộp bài và Google Drive; web này (trên Vercel) chỉ làm trang admin + chấm, đọc/ghi dữ liệu
qua "API" của Apps Script (có khóa bí mật). Không cần Google Cloud, OAuth hay refresh token.

Biến môi trường: APPS_SCRIPT_URL (link .../exec của Web App), APPS_SCRIPT_KHOA (khóa in ra bởi caiDatLanDau()).
"""
import base64
import os
import secrets
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor

import httpx

from gio import bay_gio
from tom_tat import tinh_tom_tat

URL = os.environ.get("APPS_SCRIPT_URL", "")
KHOA = os.environ.get("APPS_SCRIPT_KHOA", "")
NOP_BAI_NGOAI = URL  # trang nộp bài nằm ở Apps Script; trang chủ web này chuyển hướng tới đó
THU_MUC_TAM = os.path.join(tempfile.gettempdir(), "olympic")

_http = httpx.Client(timeout=120, follow_redirects=True)  # Apps Script trả kết quả qua một lần chuyển hướng
_bo_nho = {}


class LoiAppsScript(Exception):
    pass


def _goi(hanh_dong, **tham_so):
    loi = "Apps Script không phản hồi"
    for lan in range(4):
        try:
            r = _http.post(URL, json=dict(tham_so, khoa=KHOA, hanh_dong=hanh_dong))
        except httpx.HTTPError as e:
            loi = str(e)
            time.sleep(1 + lan)
            continue
        if r.status_code in (429, 500, 502, 503, 504):
            loi = "Apps Script báo lỗi %d" % r.status_code
            time.sleep(1 + 2 * lan)
            continue
        try:
            kq = r.json()
        except ValueError:
            raise LoiAppsScript("Apps Script không trả về JSON - kiểm tra APPS_SCRIPT_URL là link /exec và Web App "
                                "đặt 'Who has access: Anyone'. Nội dung: %s" % r.text[:200])
        if kq.get("ok"):
            return kq.get("du_lieu")
        loi = kq.get("loi") or "lỗi không rõ"
        if "too many" not in loi.lower():  # chỉ thử lại khi Apps Script quá tải
            raise LoiAppsScript("Apps Script: %s" % loi)
        time.sleep(1 + 2 * lan)
    raise LoiAppsScript(loi)


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


def khoi_tao():
    if not URL or not KHOA:
        raise LoiAppsScript("Thiếu biến môi trường APPS_SCRIPT_URL / APPS_SCRIPT_KHOA")


# ---------- Cài đặt ----------

def doc_cai_dat(khoa, mac_dinh=None):
    return _nho("cai_dat", 10, lambda: _goi("cai_dat")).get(khoa, mac_dinh)


def ghi_cai_dat(khoa, gia_tri):
    _goi("ghi_cai_dat", ten=khoa, gia_tri=gia_tri)
    _quen("cai_dat")


def khoa_phien():
    khoa = os.environ.get("PHIEN_BI_MAT") or doc_cai_dat("khoa_phien")
    if not khoa:
        khoa = secrets.token_hex(32)
        ghi_cai_dat("khoa_phien", khoa)
    return khoa


# ---------- Lần nộp ----------

def _ds():
    return _nho("ds", 3, lambda: sorted(_goi("ds") or [], key=lambda r: (r.get("thoi_gian", ""), r["id"])))


def _cua_doi(ma_doi):
    """[(lần thứ mấy, bản ghi)] của đội, cũ nhất trước."""
    return list(enumerate((r for r in _ds() if r.get("ma_doi") == ma_doi), 1))


def _tim(lan_nop_id):
    for _ in range(2):
        for r in _ds():
            if r["id"] == lan_nop_id:
                return r
        _quen("ds")
    return None


def _so_thu_tu(ban_ghi):
    return next(so for so, r in _cua_doi(ban_ghi["ma_doi"]) if r["id"] == ban_ghi["id"])


def _nhe(r, so):
    return {"id": r["id"], "ma_doi": r["ma_doi"], "ten_doi": r.get("ten_doi", ""), "thoi_gian": r.get("thoi_gian", ""),
            "thu_muc": r.get("thu_muc"), "hidden_dung": bool(r.get("hidden")), "loi_nop": r.get("loi") or None,
            "cac_file": r.get("cac_file", []), "kiem_tra": {}, "so": so}


def _day_du(r, so):
    d = _nhe(r, so)
    d["kiem_tra"] = _goi("doc_json", id=r["id"], ten="kiem_tra.json") or {}
    return d


def tao_thu_muc_nop(ma_doi, thoi_gian):
    raise LoiAppsScript("Bài được nộp ở trang Apps Script, không nộp qua web này")


def them_lan_nop(*a, **kw):
    raise LoiAppsScript("Bài được nộp ở trang Apps Script, không nộp qua web này")


def lay_lan_nop(lan_nop_id):
    r = _tim(lan_nop_id)
    return _day_du(r, _so_thu_tu(r)) if r else None


def ds_lan_nop(ma_doi):
    cua_doi = list(reversed(_cua_doi(ma_doi)))
    with ThreadPoolExecutor(6) as ex:
        return list(ex.map(lambda x: _day_du(x[1], x[0]), cua_doi))


def dem_lan_nop(ma_doi):
    return len(_cua_doi(ma_doi))


def lan_nop_moi_nhat(ma_doi, ca_nop_loi=False):
    for so, r in reversed(_cua_doi(ma_doi)):
        if ca_nop_loi or not r.get("loi"):
            return _nhe(r, so)
    return None


def hidden_dung_som_nhat(ma_doi):
    ds = [r["thoi_gian"] for _, r in _cua_doi(ma_doi) if r.get("hidden") and not r.get("loi")]
    return min(ds) if ds else None


def thu_muc_lam_viec(lan_nop):
    """Tải file của lần nộp (qua Apps Script) về thư mục tạm để chấm."""
    dich = os.path.join(THU_MUC_TAM, "cham", lan_nop["id"])
    os.makedirs(dich, exist_ok=True)
    for ten, b64 in (_goi("tai_file", id=lan_nop["id"]) or {}).items():
        with open(os.path.join(dich, ten), "wb") as f:
            f.write(base64.b64decode(b64))
    return dich


def doc_file(lan_nop, ten):
    return base64.b64decode(_goi("tai_file", id=lan_nop["id"], ten=ten)[ten])


def luu_kiem_tra(lan_nop_id, kiem_tra):
    """Kiểm tra định dạng tính lúc chấm (Apps Script không chạy được Python) - lưu để admin xem."""
    _goi("ghi_json", id=lan_nop_id, ten="kiem_tra.json", du_lieu=kiem_tra)


# ---------- Kết quả chấm ----------

def _sua_ban_ghi(lan_nop_id, sua):
    _goi("sua_ban_ghi", id=lan_nop_id, sua=sua)
    _quen("ds")


def dat_ket_qua(lan_nop_id, trang_thai, bao_cao=None, phieu=None, loi=None):
    sua = {"tt": trang_thai}
    if bao_cao is not None or loi is not None:
        du_lieu = {"trang_thai": trang_thai, "cap_nhat": bay_gio(), "bao_cao": bao_cao, "phieu": phieu, "loi": loi}
        _goi("ghi_json", id=lan_nop_id, ten="ket_qua.json", du_lieu=du_lieu)
        if trang_thai == "da_cham":
            duyet = {p: bool(v["dat"]) for p, v in ds_duyet(lan_nop_id).items()}
            sua.update(tinh_tom_tat(du_lieu, duyet))
            sua["tt"] = trang_thai
    _sua_ban_ghi(lan_nop_id, sua)


def lay_ket_qua(lan_nop_id):
    r = _tim(lan_nop_id)
    if not r or not r.get("tt"):
        return None
    kq = {"trang_thai": r["tt"], "cap_nhat": None, "bao_cao": None, "phieu": None, "loi": None}
    if r["tt"] in ("da_cham", "loi"):
        da_luu = _goi("doc_json", id=lan_nop_id, ten="ket_qua.json") or {}
        kq.update({k: da_luu.get(k) for k in ("cap_nhat", "bao_cao", "phieu", "loi")})
    return kq


def ds_chua_xong():
    return [r["id"] for r in _ds() if r.get("tt") in ("cho_cham", "dang_cham")]


def lay_tom_tat(lan_nop_id):
    r = _tim(lan_nop_id) or {}
    tom_tat = {"trang_thai": r.get("tt") or "chua_cham", "tong": None, "diem_bai": [], "cho_duyet": 0, "nen_xem": 0}
    if tom_tat["trang_thai"] == "da_cham" and r.get("tong") is not None:
        tom_tat.update(tong=r["tong"], diem_bai=r.get("diem_bai") or [],
                       cho_duyet=r.get("cho_duyet", 0), nen_xem=r.get("nen_xem", 0))
    return tom_tat


# ---------- Duyệt tay ----------

def ds_duyet(lan_nop_id):
    return _goi("doc_json", id=lan_nop_id, ten="duyet.json") or {}


def duyet(lan_nop_id, phan, dat, ghi_chu=""):
    ds = ds_duyet(lan_nop_id)
    if dat is None:
        ds.pop(phan, None)
    else:
        ds[phan] = {"phan": phan, "dat": int(dat), "ghi_chu": ghi_chu, "thoi_gian": bay_gio()}
    _goi("ghi_json", id=lan_nop_id, ten="duyet.json", du_lieu=ds)
    kq = lay_ket_qua(lan_nop_id)
    if kq and kq["trang_thai"] == "da_cham" and kq["bao_cao"]:
        _sua_ban_ghi(lan_nop_id, tinh_tom_tat(kq, {p: bool(v["dat"]) for p, v in ds.items()}))


# ---------- Đội: ghép từ danh sách admin thêm/xóa và các lần nộp ----------

def _doi():
    return _nho("doi", 10, lambda: _goi("doi") or {})


def _sua_doi(ham):
    du_lieu = _goi("doi") or {}
    du_lieu.setdefault("ds", {})
    du_lieu.setdefault("an", {})
    ham(du_lieu)
    _goi("ghi_doi", du_lieu=du_lieu)
    _quen("doi")


def luu_doi(ma_doi, ten_doi="", tu_nop=False):
    if tu_nop:
        return

    def sua(d):
        d["ds"][ma_doi] = {"ten": ten_doi or d["ds"].get(ma_doi, {}).get("ten", "")}
        d["an"].pop(ma_doi, None)
    _sua_doi(sua)


def xoa_doi(ma_doi):
    def sua(d):
        d["ds"].pop(ma_doi, None)
        d["an"][ma_doi] = bay_gio()  # đội nộp lại sau thời điểm này sẽ hiện lại
    _sua_doi(sua)


def ds_doi():
    dj = _doi()
    them_truoc = dj.get("ds", {})
    doi = {ma: {"ma_doi": ma, "ten_doi": v.get("ten", "")} for ma, v in them_truoc.items()}
    moi_nhat = {}
    for r in _ds():
        muc = doi.setdefault(r["ma_doi"], {"ma_doi": r["ma_doi"], "ten_doi": ""})
        if r.get("ten_doi") and r["ma_doi"] not in them_truoc and (not r.get("loi") or not muc["ten_doi"]):
            muc["ten_doi"] = r["ten_doi"]
        moi_nhat[r["ma_doi"]] = r.get("thoi_gian", "")
    for ma, luc_xoa in dj.get("an", {}).items():
        if moi_nhat.get(ma, "") <= luc_xoa:
            doi.pop(ma, None)
    return sorted(doi.values(), key=lambda d: d["ma_doi"])


def lay_doi(ma_doi):
    return next((d for d in ds_doi() if d["ma_doi"] == ma_doi), None)
