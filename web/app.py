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
import time
import unicodedata
from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional

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
from cham import DAP_AN_K, DE_THI, HIDDEN, MANH_KHOA, THONG_DIEP, tinh_diem  # noqa: E402
from doc_phieu_word import LoiDocPhieu, doc_phieu  # noqa: E402
from gio import bay_gio_dt  # noqa: E402
from kiem_tra_nop import kiem_tra  # noqa: E402

ADMIN_TAI_KHOAN = os.environ.get("ADMIN_TAI_KHOAN", "admin")
ADMIN_MAT_KHAU = os.environ.get("ADMIN_MAT_KHAU", "admin123")
MAU_MA_DOI = r"[A-Za-z0-9_\-]{1,30}"
DUOI_CODE = (".py",)
DUNG_LUONG_TOI_DA = 2 * 1024 * 1024  # 2 MB mỗi file
SO_FILE_MOI_O = 3  # mỗi ô bài / Hidden: 3 tệp của thành viên A, B, C
TEN_BAI = {1: "Dấu mốc khởi đầu", 2: "Những con số kết nối", 3: "Nhịp sống công nghệ",
           4: "Kết nối những chặng đường", 5: "Trí tuệ nhân tạo vươn xa"}


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
    if han and bay_gio_dt() > datetime.fromisoformat(han):
        return False, "Đã hết hạn nộp bài.", han
    return True, "", han


def _co_file(f):
    return f is not None and bool(f.filename)


def _ten_an_toan(ten_file):
    """Giữ tên tệp đội đặt (đề chấm điểm cả quy cách đặt tên), chỉ bỏ đường dẫn và ký tự không hợp lệ."""
    ten = os.path.basename(ten_file.replace("\\", "/")).strip()
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", ten)[:120] or "khong_ten"


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
            "so_lan": kho.dem_lan_nop(doi["ma_doi"]),
            "trang_thai": None, "tong": None, "diem_bai": [], "cho_duyet": 0, "nen_xem": 0, "hidden": False}
    if lan_nop:
        hang.update(kho.lay_tom_tat(lan_nop["id"]))
    return hang


def bang_xep_hang():
    hang = [tong_hop_doi(d) for d in kho.ds_doi()]
    # Bằng điểm: đội hoàn thành Hidden Challenge xếp trên, rồi tới đội nộp (bản được chấm) sớm hơn
    co_diem = sorted((h for h in hang if h["tong"] is not None),
                     key=lambda h: (-h["tong"], not h["hidden"], h["lan_nop"]["thoi_gian"]))
    return co_diem, [h for h in hang if h["tong"] is None]


# ---------- Đội thi (không cần đăng nhập) ----------

@app.get("/")
def nop_bai_form(request: Request):
    if kho.NOP_BAI_NGOAI:  # bài nộp ở trang Apps Script
        return RedirectResponse(kho.NOP_BAI_NGOAI, status_code=307)
    duoc_nop, ly_do_khoa, han_nop = trang_thai_nop()
    return trang(request, "nop_bai.html", duoc_nop=duoc_nop, ly_do_khoa=ly_do_khoa, han_nop=han_nop,
                 ma_doi_cu=request.session.get("ma_doi_cu", ""), ten_doi_cu=request.session.get("ten_doi_cu", ""),
                 ten_bai=TEN_BAI,
                 ket_qua=request.session.pop("ket_qua_nop", None))


def _nop_loi(request, loi):
    """Không nhận lần nộp: báo từng lỗi để đội sửa rồi nộp lại."""
    for x in loi:
        thong_bao(request, x, "loi")
    thong_bao(request, "NỘP LỖI - bài chưa được nhận. Vui lòng sửa các lỗi trên rồi nộp lại.", "loi")
    return ve("/")


def _chuan_ten(s):
    """So tên không phân biệt hoa/thường, khoảng trắng thừa, kiểu mã hóa dấu (NFC/NFD) của Word."""
    return " ".join(unicodedata.normalize("NFC", s or "").casefold().split())


def _doi_chieu_phieu(phieu, ma_doi, ten_doi):
    """Mã đội và tên đội nhập khi nộp phải khớp với phiếu trả lời; trả về danh sách lỗi."""
    loi = []
    if not phieu["ma_doi"]:
        loi.append("Phiếu trả lời chưa ghi Mã đội.")
    elif phieu["ma_doi"].replace(" ", "").upper() != ma_doi:
        loi.append("Mã đội trong phiếu trả lời (%s) khác mã đội đã nhập (%s)." % (phieu["ma_doi"], ma_doi))
    if not phieu["ten_doi"]:
        loi.append("Phiếu trả lời chưa ghi Tên đội.")
    elif _chuan_ten(phieu["ten_doi"]) != _chuan_ten(ten_doi):
        loi.append("Tên đội trong phiếu trả lời (%s) khác tên đội đã nhập (%s)." % (phieu["ten_doi"], ten_doi))
    return loi


@app.post("/nop-bai")
async def nop_bai(request: Request, ma_doi: str = Form(""), ten_doi: str = Form(""),
                  phieu: Optional[UploadFile] = File(None),
                  bai1: List[UploadFile] = File([]), bai2: List[UploadFile] = File([]),
                  bai3: List[UploadFile] = File([]), bai4: List[UploadFile] = File([]),
                  bai5: List[UploadFile] = File([]), hidden: List[UploadFile] = File([])):
    if kho.NOP_BAI_NGOAI:
        return ve(kho.NOP_BAI_NGOAI)
    ma_doi, ten_doi = ma_doi.strip().upper(), ten_doi.strip()[:100]
    duoc_nop, ly_do_khoa, _ = trang_thai_nop()
    if not duoc_nop:
        thong_bao(request, ly_do_khoa, "loi")
        return ve("/")
    if not re.fullmatch(MAU_MA_DOI, ma_doi):
        thong_bao(request, "Mã đội chỉ gồm chữ không dấu, số, '-' hoặc '_' (tối đa 30 ký tự).", "loi")
        return ve("/")
    request.session["ma_doi_cu"] = ma_doi
    request.session["ten_doi_cu"] = ten_doi
    if not ten_doi:
        thong_bao(request, "Chưa nhập tên đội (phải giống tên đội ghi trong phiếu trả lời).", "loi")
        return ve("/")

    # Đọc và kiểm tra từng ô; có lỗi ở bất kỳ ô nào thì lần nộp bị từ chối (không chấm)
    cac_o = [("Phiếu trả lời", "phieu", [phieu] if _co_file(phieu) else [], (".docx",))] + \
            [("Bài %d" % so, so, ds, DUOI_CODE) for so, ds in enumerate((bai1, bai2, bai3, bai4, bai5), 1)] + \
            [("Hidden Challenge", "hidden", hidden, DUOI_CODE)]
    da_doc, loi = [], []
    for ten_o, khoa, ds, duoi in cac_o:
        ds = [f for f in ds if _co_file(f)]
        if khoa != "phieu" and len(ds) > SO_FILE_MOI_O:
            loi.append("Ô %s chỉ nhận tối đa %d tệp (A, B, C), đã chọn %d tệp." % (ten_o, SO_FILE_MOI_O, len(ds)))
        for f in ds:
            da_doc.append((ten_o, khoa, _ten_an_toan(f.filename), await f.read(DUNG_LUONG_TOI_DA + 1), duoi))
    loi += [x for x in (_loi_o_nop(ten_o, ten_file, nd, duoi) for ten_o, _, ten_file, nd, duoi in da_doc) if x]
    cac_ten = [ten.lower() for _, _, ten, _, _ in da_doc]
    trung = sorted({ten for _, _, ten, _, _ in da_doc if cac_ten.count(ten.lower()) > 1})
    if trung:
        loi.append("Có tệp trùng tên: %s - mỗi tệp phải có tên riêng." % ", ".join(trung))
    if not any(khoa == "phieu" for _, khoa, *_ in da_doc):
        loi.insert(0, "Chưa chọn phiếu trả lời (file Word .docx).")
    if not any(khoa != "phieu" for _, khoa, *_ in da_doc):
        loi.append("Chưa chọn file bài làm nào.")

    # Lưu file với tên đội đặt - kể cả lần nộp lỗi, để admin xem được đội đã nộp gì
    thoi_gian = bay_gio_dt()
    tg = thoi_gian.isoformat(timespec="seconds")
    thu_muc = kho.tao_thu_muc_nop(ma_doi, thoi_gian)
    da_luu = []
    for _, khoa, ten, noi_dung, _ in da_doc:
        if len(noi_dung) > DUNG_LUONG_TOI_DA or ten.lower() in (x.lower() for x in da_luu):
            continue
        with open(os.path.join(thu_muc, ten), "wb") as g:
            g.write(noi_dung)
        da_luu.append(ten)
    kho.luu_doi(ma_doi, ten_doi, tu_nop=True)
    if loi:
        await run_in_threadpool(kho.them_lan_nop, ma_doi, tg, thu_muc, da_luu, {}, False, loi, ten_doi)
        return _nop_loi(request, loi)

    ket_qua_kt, hidden_dung = await run_in_threadpool(kiem_tra, thu_muc, ma_doi)
    if not ket_qua_kt["phieu"]["hop_le"]:
        # Phiếu là căn cứ chấm: không đọc được hoặc sai mẫu thì từ chối lần nộp
        chi_tiet = "; ".join(ket_qua_kt["phieu"]["van_de"]) or "không rõ"
        loi = ["Phiếu trả lời không đọc được hoặc không đúng mẫu của Ban Tổ chức (%s)." % chi_tiet]
    else:
        loi = _doi_chieu_phieu(ket_qua_kt["phieu"], ma_doi, ten_doi)
    if loi:
        await run_in_threadpool(kho.them_lan_nop, ma_doi, tg, thu_muc, da_luu, ket_qua_kt, False, loi, ten_doi)
        return _nop_loi(request, loi)
    # Mã đội, tên đội đúng và đủ -> nộp thành công. Không chấm ngay (admin bấm chấm sau);
    # kết quả kiểm tra định dạng chỉ lưu cho admin xem, đội không thấy.
    await run_in_threadpool(kho.them_lan_nop, ma_doi, tg, thu_muc, da_luu, ket_qua_kt, hidden_dung, None, ten_doi)
    request.session["ket_qua_nop"] = {"ma_doi": ma_doi, "ten_doi": ten_doi,
                                      "thoi_gian": thoi_gian.strftime("%H:%M:%S %d/%m/%Y")}
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
    return trang(request, "admin_tong_quan.html", hang=hang, cham_dong_bo=hang_doi_cham.DONG_BO,
                 link_nop_bai=kho.NOP_BAI_NGOAI or str(request.base_url), lien_ket=kho.lien_ket(),
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
def admin_cham_lai(request: Request, lan_nop_id: str, quay_ve: str = Form("")):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if not lan_nop:
        return ve("/admin")
    trang_doi = "/admin/doi/%s" % lan_nop["ma_doi"]
    moi_nhat = kho.lan_nop_moi_nhat(lan_nop["ma_doi"])
    if lan_nop["loi_nop"]:
        thong_bao(request, "Lần nộp thứ %d là lần nộp lỗi, không chấm điểm." % lan_nop["so"], "loi")
    elif not moi_nhat or moi_nhat["id"] != lan_nop_id:
        thong_bao(request, "Chỉ chấm lần nộp thành công cuối cùng của đội (lần thứ %d)." % moi_nhat["so"], "loi")
    else:
        hang_doi_cham.dua_vao(lan_nop_id)
        if hang_doi_cham.DONG_BO:
            tom_tat = kho.lay_tom_tat(lan_nop_id)
            thong_bao(request, "Đội %s: đã chấm xong lần nộp thứ %d - %s." % (
                lan_nop["ma_doi"], lan_nop["so"],
                "%s/25 điểm" % tom_tat["tong"] if tom_tat["tong"] is not None else "có lỗi khi chấm, xem chi tiết"))
        else:
            thong_bao(request, "Đội %s: đã đưa lần nộp thứ %d vào hàng đợi chấm." % (lan_nop["ma_doi"], lan_nop["so"]))
    return ve("/admin" if quay_ve == "tong_quan" else trang_doi)


THOI_GIAN_MOT_LUOT_CHAM = 240  # giây; chế độ đồng bộ (Vercel) mỗi request tối đa 300 giây


def _dua_vao_cham(chi_chua_cham):
    """Chấm lần nộp hợp lệ mới nhất của các đội. Trả về (số đã chấm/đưa vào hàng đợi, số còn lại).

    Chế độ đồng bộ: chấm lần lượt trong một request, dừng khi gần hết thời gian - admin bấm tiếp phần còn lại.
    """
    can_cham = []
    for doi in kho.ds_doi():
        lan_nop = kho.lan_nop_moi_nhat(doi["ma_doi"])
        if lan_nop and not (chi_chua_cham and kho.lay_tom_tat(lan_nop["id"])["trang_thai"] != "chua_cham"):
            can_cham.append(lan_nop["id"])
    het_gio = time.time() + THOI_GIAN_MOT_LUOT_CHAM
    for i, lan_nop_id in enumerate(can_cham):
        if hang_doi_cham.DONG_BO and time.time() > het_gio:
            return i, len(can_cham) - i
        hang_doi_cham.dua_vao(lan_nop_id)
    return len(can_cham), 0


def _bao_da_cham(request, so, con_lai, chu):
    if not so and not con_lai:
        thong_bao(request, "Không còn bài nào %s." % chu)
    elif hang_doi_cham.DONG_BO:
        thong_bao(request, "Đã chấm xong %d đội." % so + (" Còn %d đội - bấm lại nút để chấm tiếp." % con_lai
                                                          if con_lai else ""), "loi" if con_lai else "ok")
    else:
        thong_bao(request, "Đã đưa %d bài vào hàng đợi chấm." % so)


@app.post("/admin/cham-chua-cham")
def admin_cham_chua_cham(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    _bao_da_cham(request, *_dua_vao_cham(chi_chua_cham=True), "chưa chấm")
    return ve("/admin")


@app.post("/admin/cham-tat-ca")
def admin_cham_tat_ca(request: Request):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    _bao_da_cham(request, *_dua_vao_cham(chi_chua_cham=False), "để chấm")
    return ve("/admin")


@app.get("/admin/doi/{ma_doi}")
def admin_doi(request: Request, ma_doi: str, lan: str = None):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    doi = kho.lay_doi(ma_doi)
    lich_su = kho.ds_lan_nop(ma_doi)
    lan_hop_le = kho.lan_nop_moi_nhat(ma_doi)  # lần nộp thành công cuối cùng = bản được chấm
    # Mặc định mở bản được chấm; chưa có thì mở lần nộp gần nhất. Luôn lấy bản đầy đủ (file, kiểm tra định dạng).
    id_xem = lan or (lan_hop_le["id"] if lan_hop_le else (lich_su[0]["id"] if lich_su else None))
    lan_nop = kho.lay_lan_nop(id_xem) if id_xem else None
    if lan_nop and lan_nop["ma_doi"] != ma_doi:
        lan_nop = None
    kq, bc = bao_cao_hien_tai(lan_nop["id"]) if lan_nop else (None, None)

    # Bảng lịch sử: trạng thái nộp + trạng thái chấm của từng lần
    cac_lan = []
    for ln in lich_su:
        dong = {"ln": ln, "la_ban_cham": bool(lan_hop_le and ln["id"] == lan_hop_le["id"]),
                "trang_thai_cham": None, "diem": None}
        if not ln["loi_nop"]:
            tom_tat = kho.lay_tom_tat(ln["id"])
            dong["trang_thai_cham"], dong["diem"] = tom_tat["trang_thai"], tom_tat["tong"]
        cac_lan.append(dong)
    dap_an = {bai: {**{tv: DE_THI[bai][tv].dap_an for tv in "ABC"}, "K": DAP_AN_K[bai], "manh": MANH_KHOA[bai - 1]}
              for bai in range(1, 6)}
    dap_an["H"] = {**HIDDEN, "thong_diep": THONG_DIEP}
    return trang(request, "admin_doi.html", ma_doi=ma_doi, thong_tin_doi=doi, lich_su=lich_su, lan_nop=lan_nop,
                 kq=kq, bc=bc, duyet=kho.ds_duyet(lan_nop["id"]) if lan_nop else {}, dap_an=dap_an,
                 la_moi_nhat=bool(lich_su and lan_nop and lan_nop["id"] == lich_su[0]["id"]),
                 lan_hop_le=lan_hop_le, cac_lan=cac_lan)


@app.post("/admin/duyet/{lan_nop_id}")
def admin_duyet(request: Request, lan_nop_id: str, phan: str = Form(...), quyet: str = Form(...),
                ghi_chu: str = Form("")):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if not lan_nop or not re.fullmatch(r"[1-5][ABCT]|H[ABC]", phan) or quyet not in ("dat", "khong_dat", "bo"):
        return ve("/admin")
    kho.duyet(lan_nop_id, phan, {"dat": True, "khong_dat": False, "bo": None}[quyet], ghi_chu.strip())
    ten = "Hidden %s" % phan[1] if phan[0] == "H" else (
        "Bài %s - điểm tệp" % phan[0] if phan[1] == "T" else "Bài %s phần %s" % (phan[0], phan[1]))
    thong_bao(request, "%s: %s." % (ten, {"dat": "đã duyệt ĐẠT", "khong_dat": "đã duyệt KHÔNG ĐẠT",
                                          "bo": "đã bỏ duyệt, dùng kết quả tự động"}[quyet]))
    return ve("/admin/doi/%s?lan=%s#phan-%s" % (lan_nop["ma_doi"], lan_nop_id, phan))


@app.get("/admin/file/{lan_nop_id}/{ten}")
def admin_xem_file(request: Request, lan_nop_id: str, ten: str):
    if not la_admin(request):
        return ve("/admin/dang-nhap")
    lan_nop = kho.lay_lan_nop(lan_nop_id)
    if not lan_nop or ten not in lan_nop["cac_file"]:
        return ve("/admin")
    noi_dung = kho.doc_file(lan_nop, ten)
    ctx = {"lan_nop": lan_nop, "ten": ten, "dong": None, "o_code": None, "phieu": None, "loi": None}
    if ten.lower().endswith(".py"):
        ctx["dong"] = noi_dung.decode("utf-8", errors="replace").splitlines()
    elif ten.lower().endswith(".ipynb"):
        try:
            nb = json.loads(noi_dung)
            ctx["o_code"] = [(o.get("cell_type"), "".join(o.get("source", "")) if isinstance(o.get("source"), list)
                              else o.get("source", "")) for o in nb.get("cells", [])]
        except ValueError as e:
            ctx["loi"] = "Notebook không hợp lệ: %s" % e
    elif ten.lower().endswith(".docx"):
        try:
            ctx["phieu"], ctx["phieu_canh_bao"] = doc_phieu(io.BytesIO(noi_dung))
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
                "Hidden Challenge", "Phần chờ duyệt", "Thời điểm nộp (bản được chấm)"])
    for i, h in enumerate(co_diem, 1):
        w.writerow([i, h["doi"]["ma_doi"], h["doi"]["ten_doi"], h["tong"], *h["diem_bai"],
                    "Hoàn thành" if h["hidden"] else "", h["cho_duyet"],
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
