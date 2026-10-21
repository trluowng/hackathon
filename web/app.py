"""Web nộp bài và chấm bài Vòng 1 Olympic AI UNETI 2026.

Chạy:   cd web
        python app.py            (mở http://127.0.0.1:8000)
Tài khoản admin: admin / admin123 (đổi bằng biến môi trường ADMIN_TAI_KHOAN, ADMIN_MAT_KHAU).

- Đội thi (/): không cần đăng nhập, CHỈ nộp bài. Nộp xong chỉ nhận thông báo: nộp lỗi (chưa nhận,
  nộp lại) / đã nhận nhưng có vấn đề (nên nộp lại) / nộp thành công. Không xem được điểm hay gì khác.
  Lúc nộp chỉ kiểm tra nhẹ (không chạy code) và KHÔNG chấm.
- Admin (/admin, phải đăng nhập): bấm chấm khi muốn (từng đội hoặc tất cả bài chưa chấm), xem báo cáo,
  duyệt tay, xếp hạng, xuất CSV, cài đặt.
"""
import csv
import io
import json
import os
import re
import secrets
import sys
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

THU_MUC_WEB = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(THU_MUC_WEB, "..", "cham_diem"))

from fastapi import FastAPI, File, Form, Request, UploadFile  # noqa: E402
from fastapi.responses import RedirectResponse, Response  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402
from starlette.concurrency import run_in_threadpool  # noqa: E402
from starlette.middleware.sessions import SessionMiddleware  # noqa: E402

import hang_doi_cham  # noqa: E402
import kho  # noqa: E402
from cham import CAN_REVIEW, DAP_AN_K, DE_THI, MANH_KHOA, tinh_diem  # noqa: E402
from doc_phieu_word import LoiDocPhieu, doc_phieu  # noqa: E402
from kiem_tra_nop import kiem_tra  # noqa: E402

ADMIN_TAI_KHOAN = os.environ.get("ADMIN_TAI_KHOAN", "admin")
ADMIN_MAT_KHAU = os.environ.get("ADMIN_MAT_KHAU", "admin123")
MAU_MA_DOI = r"[A-Za-z0-9_\-]{1,30}"
DUOI_CODE = (".py", ".ipynb")
DUNG_LUONG_TOI_DA = 2 * 1024 * 1024  # 2 MB mỗi file
TEN_BAI = {1: "Dấu mốc 70 năm", 2: "Những con số dấu ấn", 3: "Nhịp sống UNETI",
           4: "Kết nối những chặng đường", 5: "UNETI vươn xa"}


@asynccontextmanager
async def lifespan(app):
    hang_doi_cham.khoi_dong()
    yield


kho.khoi_tao()
# Tắt /docs, /redoc, /openapi.json: không công khai danh sách đường dẫn (kể cả của admin)
app = FastAPI(title="Chấm bài Olympic AI UNETI 2026", lifespan=lifespan,
              docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(SessionMiddleware, secret_key=kho.khoa_phien(), same_site="lax", max_age=12 * 3600)
app.mount("/static", StaticFiles(directory=os.path.join(THU_MUC_WEB, "static")), name="static")
templates = Jinja2Templates(directory=os.path.join(THU_MUC_WEB, "templates"))


def hien_thoi_gian(s):
    if not s:
        return "—"
    try:
        return datetime.fromisoformat(s).strftime("%d/%m/%Y %H:%M:%S")
    except ValueError:
        return s


templates.env.filters["tg"] = hien_thoi_gian


# ---------- Tiện ích chung ----------

def thong_bao(request, noi_dung, loai="ok"):
    request.session.setdefault("tb", []).append([loai, noi_dung])


def trang(request, mau_trang, **ctx):
    ctx["thong_bao"] = request.session.pop("tb", [])
    ctx["la_admin"] = request.session.get("admin") is True
    return templates.TemplateResponse(request, mau_trang, ctx)


def ve(url):
    return RedirectResponse(url, status_code=303)


def la_admin(request):
    return request.session.get("admin") is True


def trang_thai_nop():
    han = kho.doc_cai_dat("han_nop", "")
    if kho.doc_cai_dat("mo_nop", "1") != "1":
        return False, "Ban Tổ chức đang khóa nộp bài.", han
    if han and datetime.now() > datetime.fromisoformat(han):
        return False, "Đã hết hạn nộp bài.", han
    return True, "", han


def _co_file(f):
    return f is not None and bool(f.filename)


def _duoi(ten_file):
    return re.sub(r"[^a-z0-9.]", "", os.path.splitext(ten_file)[1].lower())[:10]


def _loi_o_nop(ten_o, ten_file, noi_dung, duoi_cho_phep):
    """Lỗi của một ô nộp (sai loại, quá dung lượng, rỗng, không phải Word thật); None nếu hợp lệ."""
    if _duoi(ten_file) not in duoi_cho_phep:
        return "Ô %s chỉ nhận file %s (đã chọn: %s)." % (ten_o, " hoặc ".join(duoi_cho_phep), ten_file)
    if len(noi_dung) > DUNG_LUONG_TOI_DA:
        return "Ô %s: file %s quá 2 MB." % (ten_o, ten_file)
    if not noi_dung.strip():
        return "Ô %s: file %s rỗng." % (ten_o, ten_file)
    if duoi_cho_phep == (".docx",) and not noi_dung.startswith(b"PK"):
        return "Ô %s: %s không phải file Word .docx hợp lệ." % (ten_o, ten_file)
    return None


def bao_cao_hien_tai(lan_nop_id):
    """(kết quả trong kho, báo cáo đã áp dụng duyệt tay) - báo cáo None nếu chưa chấm xong."""
    kq = kho.lay_ket_qua(lan_nop_id)
    if not kq or kq["trang_thai"] != "da_cham" or not kq["bao_cao"]:
        return kq, None
    duyet = {phan: bool(r["dat"]) for phan, r in kho.ds_duyet(lan_nop_id).items()}
    return kq, tinh_diem(kq["bao_cao"], kq["phieu"], duyet)


def tong_hop_doi(doi):
    lan_nop = kho.lan_nop_moi_nhat(doi["ma_doi"])                       # bản hợp lệ được chấm
    lan_cuoi = kho.lan_nop_moi_nhat(doi["ma_doi"], ca_nop_loi=True)     # lần nộp gần nhất, kể cả lỗi
    hang = {"doi": doi, "lan_nop": lan_nop, "lan_cuoi": lan_cuoi,
            "nop_loi": lan_cuoi if lan_cuoi and lan_cuoi["loi_nop"] else None,
            "so_lan": len(kho.ds_lan_nop(doi["ma_doi"])),
            "trang_thai": None, "tong": None, "diem_bai": [], "cho_duyet": 0, "nen_xem": 0,
            "hidden_luc": kho.hidden_dung_som_nhat(doi["ma_doi"])}
    if lan_nop:
        kq, bc = bao_cao_hien_tai(lan_nop["id"])
        hang["trang_thai"] = kq["trang_thai"] if kq else "chua_cham"
        if bc:
            cac_phan = [p for b in bc["bai"].values() for p in b["thanh_vien"].values()]
            hang["tong"] = bc["tong_diem"]
            hang["diem_bai"] = [bc["bai"][str(i)]["diem"] for i in range(1, 6)]
            hang["cho_duyet"] = sum(p["trang_thai"] == CAN_REVIEW and not p["diem"] for p in cac_phan)
            hang["nen_xem"] = sum(p["trang_thai"] == CAN_REVIEW and p["diem"] for p in cac_phan)
    return hang


def bang_xep_hang():
    hang = [tong_hop_doi(d) for d in kho.ds_doi()]
    co_diem = sorted((h for h in hang if h["tong"] is not None),
                     key=lambda h: (-h["tong"], h["hidden_luc"] is None, h["hidden_luc"] or ""))
    return co_diem, [h for h in hang if h["tong"] is None]


# ---------- Đội thi (không cần đăng nhập) ----------

@app.get("/")
def nop_bai_form(request: Request):
    duoc_nop, ly_do_khoa, han_nop = trang_thai_nop()
    return trang(request, "nop_bai.html", duoc_nop=duoc_nop, ly_do_khoa=ly_do_khoa, han_nop=han_nop,
                 ma_doi_cu=request.session.get("ma_doi_cu", ""), ten_bai=TEN_BAI,
                 ket_qua=request.session.pop("ket_qua_nop", None))


def _nop_loi(request, loi):
    """Không nhận lần nộp: báo từng lỗi để đội sửa rồi nộp lại."""
    for x in loi:
        thong_bao(request, x, "loi")
    thong_bao(request, "NỘP LỖI - bài chưa được nhận. Vui lòng sửa các lỗi trên rồi nộp lại.", "loi")
    return ve("/")


def _van_de_can_bao(kt):
    """Vấn đề định dạng của lần nộp đã nhận (để đội biết mà nộp lại); không có thông tin đúng/sai."""
    van_de = []
    for f in kt["cac_file"]:
        ten_o = "Bài %d" % f["o"] if f.get("o") else f["ten"]
        van_de += ["%s: %s" % (ten_o, v) for v in f["van_de"]]
    van_de += ["Phiếu trả lời: %s" % v for v in kt["phieu"]["van_de"]]
    if kt.get("o_trong"):
        van_de.append("Chưa nộp file cho: " + ", ".join("Bài %d" % so for so in kt["o_trong"]))
    if kt["thieu"]:
        van_de.append("Chưa thấy bài làm cho các phần: " + ", ".join(kt["thieu"]))
    return van_de[:20]


@app.post("/nop-bai")
async def nop_bai(request: Request, ma_doi: str = Form(""), ten_doi: str = Form(""),
                  phieu: Optional[UploadFile] = File(None),
                  bai1: Optional[UploadFile] = File(None), bai2: Optional[UploadFile] = File(None),
                  bai3: Optional[UploadFile] = File(None), bai4: Optional[UploadFile] = File(None),
                  bai5: Optional[UploadFile] = File(None)):
    ma_doi, ten_doi = ma_doi.strip().upper(), ten_doi.strip()[:100]
    duoc_nop, ly_do_khoa, _ = trang_thai_nop()
    if not duoc_nop:
        thong_bao(request, ly_do_khoa, "loi")
        return ve("/")
    if not re.fullmatch(MAU_MA_DOI, ma_doi):
        thong_bao(request, "Mã đội chỉ gồm chữ không dấu, số, '-' hoặc '_' (tối đa 30 ký tự).", "loi")
        return ve("/")
    request.session["ma_doi_cu"] = ma_doi

    # Đọc và kiểm tra từng ô; có lỗi ở bất kỳ ô nào thì lần nộp bị từ chối (không chấm)
    cac_o = [("Phiếu trả lời", "phieu", phieu, (".docx",))] + \
            [("Bài %d" % so, so, f, DUOI_CODE) for so, f in enumerate((bai1, bai2, bai3, bai4, bai5), 1)]
    da_doc = [(ten_o, khoa, f.filename, await f.read(DUNG_LUONG_TOI_DA + 1), duoi)
              for ten_o, khoa, f, duoi in cac_o if _co_file(f)]
    loi = [x for x in (_loi_o_nop(ten_o, ten_file, nd, duoi) for ten_o, _, ten_file, nd, duoi in da_doc) if x]
    if not any(khoa == "phieu" for _, khoa, *_ in da_doc):
        loi.insert(0, "Chưa chọn phiếu trả lời (file Word .docx).")
    if not any(khoa != "phieu" for _, khoa, *_ in da_doc):
        loi.append("Chưa chọn file bài làm nào.")

    # Lưu file với tên chuẩn theo ô - kể cả lần nộp lỗi, để admin xem được đội đã nộp gì
    thoi_gian = datetime.now()
    tg = thoi_gian.isoformat(timespec="seconds")
    thu_muc = os.path.join(kho.THU_MUC_BAI_NOP, ma_doi, thoi_gian.strftime("%Y%m%d-%H%M%S-%f"))
    os.makedirs(thu_muc)
    da_luu, o_cua_file = [], {}
    for _, khoa, ten_file, noi_dung, _ in da_doc:
        if len(noi_dung) > DUNG_LUONG_TOI_DA:
            continue
        ten = "%s_%s%s" % (ma_doi, "PhieuTraLoi" if khoa == "phieu" else "Bai%d" % khoa, _duoi(ten_file))
        with open(os.path.join(thu_muc, ten), "wb") as g:
            g.write(noi_dung)
        da_luu.append(ten)
        if khoa != "phieu":
            o_cua_file[ten] = khoa
    kho.luu_doi(ma_doi, ten_doi)
    if loi:
        kho.them_lan_nop(ma_doi, tg, thu_muc, da_luu, {}, False, loi_nop=loi)
        return _nop_loi(request, loi)

    ket_qua_kt, hidden_dung = await run_in_threadpool(kiem_tra, thu_muc, ma_doi)
    if not ket_qua_kt["phieu"]["hop_le"]:
        # Phiếu là căn cứ chấm: không đọc được hoặc sai mẫu thì từ chối lần nộp
        chi_tiet = "; ".join(ket_qua_kt["phieu"]["van_de"]) or "không rõ"
        loi = ["Phiếu trả lời không đọc được hoặc không đúng mẫu của Ban Tổ chức (%s)." % chi_tiet]
        kho.them_lan_nop(ma_doi, tg, thu_muc, da_luu, ket_qua_kt, False, loi_nop=loi)
        return _nop_loi(request, loi)
    for f in ket_qua_kt["cac_file"]:
        so = f["o"] = o_cua_file.get(f["ten"])
        bai_nhan_ra = sorted({p[0] for p in f["phan"]})
        if so and bai_nhan_ra and str(so) not in bai_nhan_ra:
            f["van_de"].append("File nộp ở ô Bài %d nhưng nội dung là Bài %s - kiểm tra có chọn nhầm file không"
                               % (so, ", ".join(bai_nhan_ra)))
    ket_qua_kt["o_trong"] = [so for so in range(1, 6) if so not in o_cua_file.values()
                             and any(p.startswith(str(so)) for p in ket_qua_kt["thieu"])]
    # Không chấm ngay khi nộp (tránh quá tải khi nhiều đội nộp cùng lúc); admin bấm chấm sau.
    lan_nop_id = kho.them_lan_nop(ma_doi, tg, thu_muc, da_luu, ket_qua_kt, hidden_dung)
    request.session["ket_qua_nop"] = {"ma_doi": ma_doi, "lan": lan_nop_id,
                                      "thoi_gian": thoi_gian.strftime("%H:%M:%S %d/%m/%Y"),
                                      "van_de": _van_de_can_bao(ket_qua_kt)}
    return ve("/")


# ---------- Admin ----------

@app.get("/admin/dang-nhap")
def admin_dang_nhap_form(request: Request):
    return trang(request, "dang_nhap.html")


@app.post("/admin/dang-nhap")
def admin_dang_nhap(request: Request, tai_khoan: str = Form(...), mat_khau: str = Form(...)):
    dung_tk = secrets.compare_digest(tai_khoan.strip().encode(), ADMIN_TAI_KHOAN.encode())
    dung_mk = secrets.compare_digest(mat_khau.encode(), ADMIN_MAT_KHAU.encode())
    if not (dung_tk and dung_mk):
        thong_bao(request, "Sai tài khoản hoặc mật khẩu.", "loi")
        return ve("/admin/dang-nhap")
    request.session["admin"] = True
    return ve("/admin")


@app.get("/admin")
def admin_tong_quan(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    hang = [tong_hop_doi(d) for d in kho.ds_doi()]
    return trang(request, "admin_tong_quan.html", hang=hang,
                 so_chua_cham=sum(h["trang_thai"] == "chua_cham" for h in hang),
                 han_nop=kho.doc_cai_dat("han_nop", ""), mo_nop=kho.doc_cai_dat("mo_nop", "1") == "1")


@app.post("/admin/doi")
def admin_luu_doi(request: Request, danh_sach: str = Form(...)):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    so_doi, loi = 0, []
    for so_dong, dong in enumerate(danh_sach.splitlines(), 1):
        if not dong.strip():
            continue
        ma_doi, _, ten_doi = (x.strip() for x in dong.partition(","))
        if not re.fullmatch(MAU_MA_DOI, ma_doi):
            loi.append("dòng %d" % so_dong)
            continue
        kho.luu_doi(ma_doi.upper(), ten_doi)
        so_doi += 1
    if so_doi:
        thong_bao(request, "Đã lưu %d đội." % so_doi)
    if loi:
        thong_bao(request, "Bỏ qua (sai định dạng 'MÃ_ĐỘI,Tên đội'): " + ", ".join(loi), "loi")
    return ve("/admin")


@app.post("/admin/doi/{ma_doi}/xoa")
def admin_xoa_doi(request: Request, ma_doi: str):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    kho.xoa_doi(ma_doi)
    thong_bao(request, "Đã xóa đội %s khỏi danh sách (bài đã nộp vẫn được giữ trên đĩa; "
                       "đội nộp lại sẽ được tạo lại)." % ma_doi)
    return ve("/admin")


@app.post("/admin/cai-dat")
def admin_cai_dat(request: Request, han_nop: str = Form(""), mo_nop: str = Form(None)):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    if han_nop:
        try:
            han_nop = datetime.fromisoformat(han_nop).isoformat(timespec="seconds")
        except ValueError:
            thong_bao(request, "Hạn nộp không hợp lệ.", "loi")
            return ve("/admin")
    kho.ghi_cai_dat("han_nop", han_nop)
    kho.ghi_cai_dat("mo_nop", "1" if mo_nop else "0")
    thong_bao(request, "Đã lưu cài đặt nộp bài.")
    return ve("/admin")


@app.post("/admin/cham-lai/{lan_nop_id}")
def admin_cham_lai(request: Request, lan_nop_id: int):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if lan_nop and lan_nop["loi_nop"]:
        thong_bao(request, "Lần nộp #%d là lần nộp lỗi, không chấm điểm." % lan_nop_id, "loi")
        return ve("/admin/doi/%s?lan=%d" % (lan_nop["ma_doi"], lan_nop_id))
    if lan_nop:
        hang_doi_cham.dua_vao(lan_nop_id)
        thong_bao(request, "Đã đưa lần nộp #%d vào hàng đợi chấm." % lan_nop_id)
        return ve("/admin/doi/%s?lan=%d" % (lan_nop["ma_doi"], lan_nop_id))
    return ve("/admin")


def _dua_vao_cham(chi_chua_cham):
    """Đưa lần nộp hợp lệ mới nhất của mỗi đội vào hàng đợi chấm; trả về số lần nộp."""
    so = 0
    for doi in kho.ds_doi():
        lan_nop = kho.lan_nop_moi_nhat(doi["ma_doi"])
        if lan_nop and not (chi_chua_cham and kho.lay_ket_qua(lan_nop["id"])):
            hang_doi_cham.dua_vao(lan_nop["id"])
            so += 1
    return so


@app.post("/admin/cham-chua-cham")
def admin_cham_chua_cham(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    so = _dua_vao_cham(chi_chua_cham=True)
    thong_bao(request, "Đã đưa %d bài chưa chấm vào hàng đợi chấm." % so if so else "Không còn bài nào chưa chấm.")
    return ve("/admin")


@app.post("/admin/cham-tat-ca")
def admin_cham_tat_ca(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    so = _dua_vao_cham(chi_chua_cham=False)
    thong_bao(request, "Đã đưa %d lần nộp (mới nhất của mỗi đội) vào hàng đợi chấm lại." % so)
    return ve("/admin")


@app.get("/admin/doi/{ma_doi}")
def admin_doi(request: Request, ma_doi: str, lan: int = None):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    doi = kho.lay_doi(ma_doi)
    lich_su = kho.ds_lan_nop(ma_doi)
    lan_nop = kho.lay_lan_nop(lan) if lan else (lich_su[0] if lich_su else None)
    if lan_nop and lan_nop["ma_doi"] != ma_doi:
        lan_nop = None
    kq, bc = bao_cao_hien_tai(lan_nop["id"]) if lan_nop else (None, None)
    dap_an = {bai: {**{tv: DE_THI[bai][tv].dap_an for tv in "ABC"}, "K": DAP_AN_K[bai], "manh": MANH_KHOA[bai - 1]}
              for bai in range(1, 6)}
    return trang(request, "admin_doi.html", ma_doi=ma_doi, thong_tin_doi=doi, lich_su=lich_su, lan_nop=lan_nop,
                 kq=kq, bc=bc, duyet=kho.ds_duyet(lan_nop["id"]) if lan_nop else {}, dap_an=dap_an,
                 la_moi_nhat=bool(lich_su and lan_nop and lan_nop["id"] == lich_su[0]["id"]),
                 lan_hop_le=kho.lan_nop_moi_nhat(ma_doi))


@app.post("/admin/duyet/{lan_nop_id}")
def admin_duyet(request: Request, lan_nop_id: int, phan: str = Form(...), quyet: str = Form(...),
                ghi_chu: str = Form("")):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if not lan_nop or not re.fullmatch(r"[1-5][ABC]", phan) or quyet not in ("dat", "khong_dat", "bo"):
        return ve("/admin")
    kho.duyet(lan_nop_id, phan, {"dat": True, "khong_dat": False, "bo": None}[quyet], ghi_chu.strip())
    thong_bao(request, "Bài %s phần %s: %s." % (phan[0], phan[1], {"dat": "đã duyệt ĐẠT", "khong_dat": "đã duyệt KHÔNG ĐẠT",
                                                                  "bo": "đã bỏ duyệt, dùng kết quả tự động"}[quyet]))
    return ve("/admin/doi/%s?lan=%d#phan-%s" % (lan_nop["ma_doi"], lan_nop_id, phan))


@app.get("/admin/file/{lan_nop_id}/{ten}")
def admin_xem_file(request: Request, lan_nop_id: int, ten: str):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if not lan_nop or ten not in lan_nop["cac_file"]:
        return ve("/admin")
    duong_dan = os.path.join(lan_nop["thu_muc"], ten)
    ctx = {"lan_nop": lan_nop, "ten": ten, "dong": None, "o_code": None, "phieu": None, "loi": None}
    if ten.lower().endswith(".py"):
        with open(duong_dan, encoding="utf-8", errors="replace") as f:
            ctx["dong"] = f.read().splitlines()
    elif ten.lower().endswith(".ipynb"):
        try:
            with open(duong_dan, encoding="utf-8") as f:
                nb = json.load(f)
            ctx["o_code"] = [(o.get("cell_type"), "".join(o.get("source", "")) if isinstance(o.get("source"), list)
                              else o.get("source", "")) for o in nb.get("cells", [])]
        except ValueError as e:
            ctx["loi"] = "Notebook không hợp lệ: %s" % e
    elif ten.lower().endswith(".docx"):
        try:
            ctx["phieu"], ctx["phieu_canh_bao"] = doc_phieu(duong_dan)
        except LoiDocPhieu as e:
            ctx["loi"] = str(e)
    else:
        ctx["loi"] = "Không xem trực tiếp được loại file này (đội nộp sai loại file)."
    return trang(request, "admin_file.html", **ctx)


@app.get("/admin/xep-hang")
def admin_xep_hang(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    co_diem, chua_co = bang_xep_hang()
    return trang(request, "admin_xep_hang.html", co_diem=co_diem, chua_co=chua_co,
                 tam_tinh=any(h["cho_duyet"] for h in co_diem) or bool(chua_co))


@app.get("/admin/xep-hang.csv")
def admin_xep_hang_csv(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    co_diem, chua_co = bang_xep_hang()
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["Hạng", "Mã đội", "Tên đội", "Tổng điểm", "Bài 1", "Bài 2", "Bài 3", "Bài 4", "Bài 5",
                "Hidden Challenge đúng lúc", "Phần chờ duyệt", "Lần nộp cuối"])
    for i, h in enumerate(co_diem, 1):
        w.writerow([i, h["doi"]["ma_doi"], h["doi"]["ten_doi"], h["tong"], *h["diem_bai"],
                    hien_thoi_gian(h["hidden_luc"]) if h["hidden_luc"] else "", h["cho_duyet"],
                    hien_thoi_gian(h["lan_nop"]["thoi_gian"])])
    for h in chua_co:
        w.writerow(["", h["doi"]["ma_doi"], h["doi"]["ten_doi"], "chưa chấm", "", "", "", "", "", "", "",
                    hien_thoi_gian(h["lan_nop"]["thoi_gian"]) if h["lan_nop"] else "chưa nộp"])
    return Response("﻿" + out.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=xep_hang_vong1.csv"})


@app.get("/admin/dang-xuat")
def admin_dang_xuat(request: Request):
    request.session.pop("admin", None)
    return ve("/admin/dang-nhap")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=os.environ.get("HOST", "127.0.0.1"), port=int(os.environ.get("PORT", "8000")))
