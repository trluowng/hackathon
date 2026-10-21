"""Lưu trữ SQLite: đội thi, lần nộp, kết quả chấm, duyệt tay, cài đặt."""
import json
import os
import secrets
import sqlite3
from datetime import datetime

THU_MUC_DU_LIEU = os.environ.get("DU_LIEU_WEB") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "du_lieu")
THU_MUC_BAI_NOP = os.path.join(THU_MUC_DU_LIEU, "bai_nop")
DB = os.path.join(THU_MUC_DU_LIEU, "cham_diem.db")


def bay_gio():
    return datetime.now().isoformat(timespec="seconds")


def ket_noi():
    os.makedirs(THU_MUC_DU_LIEU, exist_ok=True)
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    return c


def khoi_tao():
    with ket_noi() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS doi (
            ma_doi TEXT PRIMARY KEY, ten_doi TEXT, mat_khau TEXT, tao_luc TEXT);
        CREATE TABLE IF NOT EXISTS lan_nop (
            id INTEGER PRIMARY KEY AUTOINCREMENT, ma_doi TEXT, thoi_gian TEXT, thu_muc TEXT,
            cac_file TEXT, kiem_tra TEXT, hidden_dung INTEGER);
        CREATE TABLE IF NOT EXISTS ket_qua (
            lan_nop_id INTEGER PRIMARY KEY, trang_thai TEXT, cap_nhat TEXT,
            bao_cao TEXT, phieu TEXT, loi TEXT);
        CREATE TABLE IF NOT EXISTS duyet_tay (
            lan_nop_id INTEGER, phan TEXT, dat INTEGER, ghi_chu TEXT, thoi_gian TEXT,
            PRIMARY KEY (lan_nop_id, phan));
        CREATE TABLE IF NOT EXISTS cai_dat (khoa TEXT PRIMARY KEY, gia_tri TEXT);
        """)
        try:  # lý do nộp lỗi (JSON); khác NULL = lần nộp bị từ chối, không chấm điểm
            c.execute("ALTER TABLE lan_nop ADD COLUMN loi_nop TEXT")
        except sqlite3.OperationalError:
            pass


# ---------- Cài đặt ----------

def doc_cai_dat(khoa, mac_dinh=None):
    with ket_noi() as c:
        r = c.execute("SELECT gia_tri FROM cai_dat WHERE khoa = ?", (khoa,)).fetchone()
    return r["gia_tri"] if r else mac_dinh


def ghi_cai_dat(khoa, gia_tri):
    with ket_noi() as c:
        c.execute("INSERT OR REPLACE INTO cai_dat (khoa, gia_tri) VALUES (?, ?)", (khoa, gia_tri))


def khoa_phien():
    """Khóa ký cookie phiên, tạo một lần rồi giữ nguyên qua các lần khởi động."""
    khoa = doc_cai_dat("khoa_phien")
    if not khoa:
        khoa = secrets.token_hex(32)
        ghi_cai_dat("khoa_phien", khoa)
    return khoa


# ---------- Đội ----------

def luu_doi(ma_doi, ten_doi=""):
    """Thêm đội; đội đã có thì cập nhật tên (nếu có tên mới)."""
    with ket_noi() as c:
        c.execute("""INSERT INTO doi (ma_doi, ten_doi, mat_khau, tao_luc) VALUES (?, ?, '', ?)
                     ON CONFLICT(ma_doi) DO UPDATE SET
                         ten_doi = CASE WHEN excluded.ten_doi != '' THEN excluded.ten_doi ELSE doi.ten_doi END""",
                  (ma_doi, ten_doi, bay_gio()))


def xoa_doi(ma_doi):
    with ket_noi() as c:
        c.execute("DELETE FROM doi WHERE ma_doi = ?", (ma_doi,))


def lay_doi(ma_doi):
    with ket_noi() as c:
        return c.execute("SELECT * FROM doi WHERE ma_doi = ?", (ma_doi,)).fetchone()


def ds_doi():
    with ket_noi() as c:
        return c.execute("SELECT * FROM doi ORDER BY ma_doi").fetchall()


# ---------- Lần nộp ----------

def them_lan_nop(ma_doi, thoi_gian, thu_muc, cac_file, kiem_tra, hidden_dung, loi_nop=None):
    """loi_nop: danh sách lý do nếu lần nộp bị từ chối (vẫn lưu để admin xem, không chấm)."""
    with ket_noi() as c:
        cur = c.execute("""INSERT INTO lan_nop (ma_doi, thoi_gian, thu_muc, cac_file, kiem_tra, hidden_dung, loi_nop)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (ma_doi, thoi_gian, thu_muc, json.dumps(cac_file, ensure_ascii=False),
                         json.dumps(kiem_tra, ensure_ascii=False), int(hidden_dung),
                         json.dumps(loi_nop, ensure_ascii=False) if loi_nop else None))
        return cur.lastrowid


def _lan_nop(r):
    if r is None:
        return None
    d = dict(r)
    d["cac_file"] = json.loads(d["cac_file"] or "[]")
    d["kiem_tra"] = json.loads(d["kiem_tra"] or "{}")
    d["loi_nop"] = json.loads(d["loi_nop"]) if d.get("loi_nop") else None
    return d


def lay_lan_nop(lan_nop_id):
    with ket_noi() as c:
        return _lan_nop(c.execute("SELECT * FROM lan_nop WHERE id = ?", (lan_nop_id,)).fetchone())


def ds_lan_nop(ma_doi):
    with ket_noi() as c:
        return [_lan_nop(r) for r in c.execute(
            "SELECT * FROM lan_nop WHERE ma_doi = ? ORDER BY id DESC", (ma_doi,)).fetchall()]


def lan_nop_moi_nhat(ma_doi, ca_nop_loi=False):
    """Lần nộp hợp lệ mới nhất (bản được chấm); ca_nop_loi=True: kể cả lần nộp lỗi."""
    dieu_kien = "" if ca_nop_loi else " AND loi_nop IS NULL"
    with ket_noi() as c:
        return _lan_nop(c.execute(
            "SELECT * FROM lan_nop WHERE ma_doi = ?%s ORDER BY id DESC LIMIT 1" % dieu_kien, (ma_doi,)).fetchone())


def hidden_dung_som_nhat(ma_doi):
    """Thời điểm sớm nhất đội nộp phiếu có thông điệp Hidden Challenge đúng (để phân hạng)."""
    with ket_noi() as c:
        r = c.execute("""SELECT MIN(thoi_gian) AS t FROM lan_nop
                         WHERE ma_doi = ? AND hidden_dung = 1 AND loi_nop IS NULL""", (ma_doi,)).fetchone()
    return r["t"] if r else None


# ---------- Kết quả chấm ----------

def dat_ket_qua(lan_nop_id, trang_thai, bao_cao=None, phieu=None, loi=None):
    with ket_noi() as c:
        c.execute("""INSERT INTO ket_qua (lan_nop_id, trang_thai, cap_nhat, bao_cao, phieu, loi)
                     VALUES (?, ?, ?, ?, ?, ?)
                     ON CONFLICT(lan_nop_id) DO UPDATE SET trang_thai = excluded.trang_thai,
                         cap_nhat = excluded.cap_nhat,
                         bao_cao = COALESCE(excluded.bao_cao, ket_qua.bao_cao),
                         phieu = COALESCE(excluded.phieu, ket_qua.phieu),
                         loi = excluded.loi""",
                  (lan_nop_id, trang_thai, bay_gio(),
                   json.dumps(bao_cao, ensure_ascii=False) if bao_cao is not None else None,
                   json.dumps(phieu, ensure_ascii=False) if phieu is not None else None, loi))


def lay_ket_qua(lan_nop_id):
    with ket_noi() as c:
        r = c.execute("SELECT * FROM ket_qua WHERE lan_nop_id = ?", (lan_nop_id,)).fetchone()
    if r is None:
        return None
    d = dict(r)
    d["bao_cao"] = json.loads(d["bao_cao"]) if d["bao_cao"] else None
    d["phieu"] = json.loads(d["phieu"]) if d["phieu"] else None
    return d


def ds_chua_xong():
    with ket_noi() as c:
        return [r["lan_nop_id"] for r in c.execute(
            "SELECT lan_nop_id FROM ket_qua WHERE trang_thai IN ('cho_cham', 'dang_cham')").fetchall()]


# ---------- Duyệt tay ----------

def duyet(lan_nop_id, phan, dat, ghi_chu=""):
    """dat = True/False; None để bỏ duyệt (trở về kết quả tự động)."""
    with ket_noi() as c:
        if dat is None:
            c.execute("DELETE FROM duyet_tay WHERE lan_nop_id = ? AND phan = ?", (lan_nop_id, phan))
        else:
            c.execute("INSERT OR REPLACE INTO duyet_tay VALUES (?, ?, ?, ?, ?)",
                      (lan_nop_id, phan, int(dat), ghi_chu, bay_gio()))


def ds_duyet(lan_nop_id):
    with ket_noi() as c:
        return {r["phan"]: dict(r) for r in c.execute(
            "SELECT * FROM duyet_tay WHERE lan_nop_id = ?", (lan_nop_id,)).fetchall()}
