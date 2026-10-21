"""Chạy mã nguồn thí sinh trong tiến trình riêng, có giới hạn thời gian.

Đây là lớp cách ly tối thiểu: tiến trình con, thư mục tạm, không stdin, timeout.
Khi chạy trên server thật nên bọc thêm container (không mạng, giới hạn RAM/CPU, user không quyền).

Notebook được chạy từng ô như Jupyter: ô lỗi được ghi lại rồi chạy tiếp; hết lượt thì chạy lại
các ô lỗi một lần (trường hợp thí sinh chạy các ô sai thứ tự). Có sẵn get_ipython() và
google.colab giả để code viết trên Jupyter/Colab chạy được.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import uuid
from dataclasses import dataclass, field
from typing import Optional

from nap_ma_nguon import HAM_HIEN_THI, MOC_O

_HARNESS = r'''
import ast, builtins, json, sys, traceback, types
duong_dan, file_ra, ten_bien, notebook = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4] == "1"
HAM_HIEN_THI, MOC_O = %r, %r
g = {"__name__": "__main__", "__builtins__": builtins}
with open(duong_dan, encoding="utf-8") as f:
    ma_nguon = f.read()
loi, loi_o = None, []


def _mo_dun_gia(ten):
    m = types.ModuleType(ten)
    m.__getattr__ = lambda thuoc_tinh: (lambda *a, **k: None)
    sys.modules[ten] = m
    return m


if not notebook:
    try:
        exec(compile(ma_nguon, "bai_lam.py", "exec"), g)
    except SystemExit:
        pass
    except BaseException:
        loi = traceback.format_exc(limit=-3)
else:
    def _hien_thi(x):
        if x is not None:
            print(repr(x))

    class _IPythonGia:
        def __getattr__(self, ten):
            return lambda *a, **k: None

    g[HAM_HIEN_THI] = _hien_thi
    g[MOC_O] = lambda so: None
    g["display"] = lambda *a, **k: print(*a)
    g["get_ipython"] = lambda: _IPythonGia()
    colab = _mo_dun_gia("google.colab")
    for ten in ("drive", "files", "output", "auth", "userdata"):
        setattr(colab, ten, _mo_dun_gia("google.colab." + ten))
    if "google" not in sys.modules:
        try:
            import google
        except ImportError:
            sys.modules["google"] = types.ModuleType("google")
    sys.modules["google"].colab = colab

    cac_o, hien_tai = [], [0, []]
    for s in ast.parse(ma_nguon).body:
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Call) and isinstance(s.value.func, ast.Name) \
                and s.value.func.id == MOC_O and s.value.args and isinstance(s.value.args[0], ast.Constant):
            cac_o.append(hien_tai)
            hien_tai = [s.value.args[0].value, []]
        else:
            hien_tai[1].append(s)
    cac_o.append(hien_tai)

    def chay_o(than):
        exec(compile(ast.Module(body=than, type_ignores=[]), "bai_lam.ipynb", "exec"), g)

    that_bai, dung = [], False
    for so, than in cac_o:
        if not than:
            continue
        try:
            chay_o(than)
        except SystemExit:
            dung = True
            break
        except BaseException as e:
            that_bai.append((so, than))
            loi_o.append({"o": so, "loi": "%%s: %%s" %% (type(e).__name__, e), "chay_lai_duoc": False})
    if not dung:
        for (so, than), ghi in zip(that_bai, loi_o):
            try:
                chay_o(than)
                ghi["chay_lai_duoc"] = True
            except BaseException:
                pass

bien = {}
for t in ten_bien.split(","):
    if t and t in g:
        try:
            bien[t] = repr(g[t])[:2000]
        except Exception:
            pass
sys.stdout.flush()
with open(file_ra, "w", encoding="utf-8") as f:
    json.dump({"loi": loi, "loi_o": loi_o, "bien": bien}, f)
''' % (HAM_HIEN_THI, MOC_O)


# Giới hạn số tiến trình chạy code cùng lúc: khi nhiều đội nộp/chấm đồng thời, máy quá tải có thể
# làm code đúng bị "quá thời gian". Thời gian chỉ tính từ lúc thật sự được chạy.
SO_TIEN_TRINH_TOI_DA = int(os.environ.get("CHAM_SONG_SONG") or max(2, (os.cpu_count() or 2) // 2))
_luot_chay = threading.BoundedSemaphore(SO_TIEN_TRINH_TOI_DA)


@dataclass
class KetQuaChay:
    stdout: str = ""
    loi: Optional[str] = None
    het_gio: bool = False
    bien: dict = field(default_factory=dict)
    loi_o: list = field(default_factory=list)  # notebook: [{"o", "loi", "chay_lai_duoc"}]


def _giai_ma(b):
    return b.decode("utf-8", errors="replace") if b else ""


def chay(ma_nguon, la_notebook=False, ten_bien=(), thoi_gian=10, thu_lai_khi_het_gio=True):
    """Chạy code, trả về stdout, lỗi (nếu có) và repr các biến cần lấy sau khi chạy.

    Hết giờ thì chạy lại một lần với thời gian gấp đôi trước khi kết luận (tránh trừ oan khi máy
    đang quá tải); code lặp vô hạn thật vẫn bị bắt.
    """
    with _luot_chay:
        kq = _chay_mot_lan(ma_nguon, la_notebook, ten_bien, thoi_gian)
    if kq.het_gio and thu_lai_khi_het_gio:
        with _luot_chay:
            kq = _chay_mot_lan(ma_nguon, la_notebook, ten_bien, thoi_gian * 2)
    return kq


def _chay_mot_lan(ma_nguon, la_notebook, ten_bien, thoi_gian):
    tmp = tempfile.mkdtemp(prefix="cham_")
    try:
        file_bai = os.path.join(tmp, "bai_lam.py")
        file_harness = os.path.join(tmp, "_harness_%s.py" % uuid.uuid4().hex)
        file_ra = os.path.join(tmp, "_kq_%s.json" % uuid.uuid4().hex)
        with open(file_bai, "w", encoding="utf-8") as f:
            f.write(ma_nguon)
        with open(file_harness, "w", encoding="utf-8") as f:
            f.write(_HARNESS)

        env = {"SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "TEMP": tmp, "TMP": tmp, "HOME": tmp}
        lenh = [sys.executable, "-I", "-X", "utf8", file_harness, file_bai, file_ra,
                ",".join(ten_bien), "1" if la_notebook else "0"]
        try:
            p = subprocess.run(lenh, cwd=tmp, env=env, stdin=subprocess.DEVNULL,
                               capture_output=True, timeout=thoi_gian)
        except subprocess.TimeoutExpired as e:
            return KetQuaChay(stdout=_giai_ma(e.stdout), loi="Quá thời gian %d giây" % thoi_gian, het_gio=True)

        kq = KetQuaChay(stdout=_giai_ma(p.stdout))
        if os.path.exists(file_ra):
            with open(file_ra, encoding="utf-8") as f:
                du_lieu = json.load(f)
            kq.loi, kq.bien, kq.loi_o = du_lieu["loi"], du_lieu["bien"], du_lieu["loi_o"]
        else:
            kq.loi = _giai_ma(p.stderr)[-2000:] or "Tiến trình kết thúc bất thường (mã %d)" % p.returncode
        return kq
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
