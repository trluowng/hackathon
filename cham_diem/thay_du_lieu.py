"""Tìm dữ liệu đầu vào của đề trong mã nguồn thí sinh và thay bằng dữ liệu test ẩn.

Thí sinh có thể viết cùng một dữ liệu theo nhiều hình dạng (list tuple, chuỗi nhiều dòng,
dict kề, tách X / nhãn...). Mỗi kiểu dữ liệu dưới đây biết:
  - khop(gia_tri): literal trong code có phải dữ liệu đề cho không, và ở hình dạng (vai trò) nào;
  - dung_lai(gia_tri, vai_tro, moi): dựng dữ liệu mới theo đúng hình dạng thí sinh đã viết.
"""
import ast
import copy
import re


def _la_so(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _tuple_hoa(x):
    if isinstance(x, (list, tuple)):
        return tuple(_tuple_hoa(i) for i in x)
    return x


def _kieu_trong(v):
    """Kiểu của phần tử con (list/tuple) để dựng lại cho giống; None nếu phần tử không phải dãy."""
    if v and isinstance(v[0], (list, tuple)):
        return type(v[0])
    return None


def _dung_day(kieu_ngoai, kieu_trong, phan_tu):
    return kieu_ngoai(kieu_trong(x) if kieu_trong else x for x in phan_tu)


class So:
    def __init__(self, goc):
        self.goc = goc

    def khop(self, v):
        return "so" if _la_so(v) and v == self.goc else None

    def dung_lai(self, v, vai_tro, moi):
        return moi


class Chuoi:
    def __init__(self, goc):
        self.goc = goc

    def khop(self, v):
        return "chuoi" if isinstance(v, str) and v == self.goc else None

    def dung_lai(self, v, vai_tro, moi):
        return moi


class DanhSach:
    def __init__(self, goc):
        self.goc = goc

    def khop(self, v):
        if isinstance(v, (list, tuple)) and _tuple_hoa(v) == _tuple_hoa(self.goc):
            return "day"
        return None

    def dung_lai(self, v, vai_tro, moi):
        return _dung_day(type(v), _kieu_trong(v), moi)


class LuoiKyTu:
    """Ma trận ký tự; dạng chuẩn: list chuỗi, mỗi chuỗi một hàng (vd ["UN#", "ITE"]).

    Nhận cả: list các list ký tự | list chuỗi hàng | chuỗi nhiều dòng (ký tự có thể cách nhau bằng khoảng trắng).
    """

    def __init__(self, goc):
        self.goc = list(goc)

    @staticmethod
    def _hang_cua_chuoi(s):
        return ["".join(d.split()) for d in s.splitlines() if d.strip()]

    def khop(self, v):
        if isinstance(v, str):
            return "chuoi" if "\n" in v.strip() and self._hang_cua_chuoi(v) == self.goc else None
        if not isinstance(v, (list, tuple)) or len(v) != len(self.goc):
            return None
        if all(isinstance(h, str) for h in v):
            return "hang" if list(v) == self.goc else None
        if all(isinstance(h, (list, tuple)) and all(isinstance(c, str) and len(c) == 1 for c in h) for h in v):
            return "luoi" if ["".join(h) for h in v] == self.goc else None
        return None

    def dung_lai(self, v, vai_tro, moi):
        if vai_tro == "hang":
            return type(v)(moi)
        if vai_tro == "luoi":
            return _dung_day(type(v), type(v[0]), [list(h) for h in moi])
        dong_mau = next(d for d in v.splitlines() if d.strip())
        thut_le = dong_mau[: len(dong_mau) - len(dong_mau.lstrip())]
        cach = " " if len(dong_mau.split()) > 1 else ""
        dau, cuoi = v[: len(v) - len(v.lstrip())], v[len(v.rstrip()):]
        if thut_le and dau.endswith(thut_le):
            dau = dau[: len(dau) - len(thut_le)]
        return dau + "\n".join(thut_le + cach.join(h) for h in moi) + cuoi


# ---------- Đồ thị ----------

def _doc_chuoi_canh(s):
    canh = []
    for dong in s.splitlines():
        dong = dong.strip()
        if not dong:
            continue
        t = [x for x in re.split(r"[\s,;]+", dong) if x]
        if len(t) != 3:
            return None
        try:
            w = float(t[2])
        except ValueError:
            return None
        canh.append((t[0], t[1], int(w) if w.is_integer() else w))
    return canh or None


def _viet_chuoi_canh(s, moi):
    dong_mau = next(d for d in s.splitlines() if d.strip())
    thut_le = dong_mau[: len(dong_mau) - len(dong_mau.lstrip())]
    m = re.search(r"\S([\s,;]+)\S", dong_mau.strip())
    ngan_cach = m.group(1) if m else " "
    dau = s[: len(s) - len(s.lstrip())]
    if thut_le and dau.endswith(thut_le):
        dau = dau[: len(dau) - len(thut_le)]
    cuoi = s[len(s.rstrip()):]
    noi_dung = "\n".join(thut_le + ngan_cach.join([str(a), str(b), str(w)]) for a, b, w in moi)
    return dau + noi_dung + cuoi


def _canh_tu_dict(d):
    """{u: {v: w}} hoặc {u: [(v, w), ...]} -> (danh sách cạnh vô hướng, có ghi cả hai chiều không)."""
    co_huong = []
    for u, ke in d.items():
        if isinstance(ke, dict):
            cap = list(ke.items())
        elif isinstance(ke, (list, tuple)) and all(isinstance(p, (list, tuple)) and len(p) == 2 for p in ke):
            cap = [tuple(p) for p in ke]
        else:
            return None, False
        for dinh, w in cap:
            if not _la_so(w):
                return None, False
            co_huong.append((u, dinh, w))
    tap_huong = set(co_huong)
    hai_chieu = all((b, a, w) in tap_huong for a, b, w in co_huong)
    try:
        vo_huong = sorted({(min(a, b), max(a, b), w) for a, b, w in co_huong})
    except TypeError:
        return None, False
    return vo_huong, hai_chieu


def _viet_dict_canh(v, moi):
    _, hai_chieu = _canh_tu_dict(v)
    dang_dict = any(isinstance(ke, dict) for ke in v.values())
    kieu_cap = tuple
    for ke in v.values():
        if not dang_dict and ke:
            kieu_cap = type(ke[0])
            break
    ket_qua = {}
    for a, b, _ in moi:
        for dinh in (a, b):
            ket_qua.setdefault(dinh, {} if dang_dict else [])
    for a, b, w in moi:
        for x, y in [(a, b)] + ([(b, a)] if hai_chieu else []):
            if dang_dict:
                ket_qua[x][y] = w
            else:
                ket_qua[x].append(kieu_cap((y, w)))
    return ket_qua


class CanhDoThi:
    """Đồ thị vô hướng có trọng số; dạng chuẩn: list (đỉnh 1, đỉnh 2, trọng số)."""

    def __init__(self, goc):
        self.goc = goc
        self._tap_goc = self._tap(goc)

    @staticmethod
    def _tap(canh):
        try:
            return sorted((min(u, v), max(u, v), w) for u, v, w in canh)
        except (TypeError, ValueError):
            return None

    def khop(self, v):
        if isinstance(v, str):
            canh = _doc_chuoi_canh(v)
            return "chuoi" if canh and self._tap(canh) == self._tap_goc else None
        if isinstance(v, (list, tuple)) and v and all(
            isinstance(c, (list, tuple)) and len(c) == 3 and _la_so(c[2]) for c in v
        ):
            return "day" if self._tap(v) == self._tap_goc else None
        if isinstance(v, dict) and v:
            canh, _ = _canh_tu_dict(v)
            return "dict" if canh is not None and self._tap(canh) == self._tap_goc else None
        return None

    def dung_lai(self, v, vai_tro, moi):
        if vai_tro == "chuoi":
            return _viet_chuoi_canh(v, moi)
        if vai_tro == "day":
            return _dung_day(type(v), _kieu_trong(v), moi)
        return _viet_dict_canh(v, moi)


# ---------- KNN ----------

class DuLieuKNN:
    """Dữ liệu huấn luyện; dạng chuẩn: list (x, y, nhãn).

    Nhận cả: list (x, y, nhãn) | list điểm (x, y) + list nhãn riêng | dict {(x, y): nhãn}.
    """

    def __init__(self, goc):
        self.goc = [tuple(r) for r in goc]

    def khop(self, v):
        if isinstance(v, dict):
            try:
                if {tuple(k): n for k, n in v.items()} == {(x, y): n for x, y, n in self.goc}:
                    return "dict"
            except TypeError:
                pass
            return None
        if not isinstance(v, (list, tuple)) or not v:
            return None
        t = _tuple_hoa(v)
        if t == tuple(self.goc):
            return "bo3"
        if t == tuple((x, y) for x, y, _ in self.goc):
            return "diem"
        if t == tuple(n for _, _, n in self.goc):
            return "nhan"
        return None

    def dung_lai(self, v, vai_tro, moi):
        if vai_tro == "dict":
            return {(x, y): n for x, y, n in moi}
        if vai_tro == "bo3":
            return _dung_day(type(v), _kieu_trong(v), moi)
        if vai_tro == "diem":
            return _dung_day(type(v), _kieu_trong(v), [(x, y) for x, y, _ in moi])
        return type(v)(n for _, _, n in moi)


class Diem:
    def __init__(self, goc):
        self.goc = tuple(goc)

    def khop(self, v):
        if isinstance(v, (list, tuple)) and len(v) == 2 and all(_la_so(c) for c in v) and tuple(v) == self.goc:
            return "diem"
        return None

    def dung_lai(self, v, vai_tro, moi):
        return type(v)(moi)


# ---------- Thay trong AST ----------

_KHONG = object()
_LITERAL = (ast.Constant, ast.List, ast.Tuple, ast.Dict, ast.Set)


def _so_trong_day(cay):
    """id các hằng số nằm trực tiếp trong list/tuple/dict/set: không coi là dữ liệu kiểu So
    (vd 2026 trong ("DSC", 2026) không phải year = 2026)."""
    ket_qua = set()
    for n in ast.walk(cay):
        if isinstance(n, (ast.List, ast.Tuple, ast.Dict, ast.Set)):
            ket_qua.update(id(c) for c in ast.iter_child_nodes(n) if isinstance(c, ast.Constant))
    return ket_qua


def _khop(kieu, v, node, trong_day):
    if isinstance(kieu, So) and id(node) in trong_day:
        return None
    return kieu.khop(v)


class _ThayThe(ast.NodeTransformer):
    def __init__(self, dau_vao, thay_doi, trong_day):
        self.dau_vao = dau_vao
        self.thay_doi = thay_doi or {}
        self.trong_day = trong_day
        self.tim_thay = set()

    def visit(self, node):
        if isinstance(node, ast.JoinedStr):
            return node
        if isinstance(node, _LITERAL):
            try:
                v = ast.literal_eval(node)
            except Exception:
                v = _KHONG
            if v is not _KHONG:
                for ten, kieu in self.dau_vao.items():
                    vai_tro = _khop(kieu, v, node, self.trong_day)
                    if not vai_tro:
                        continue
                    self.tim_thay.add(ten)
                    if ten in self.thay_doi:
                        moi = kieu.dung_lai(v, vai_tro, self.thay_doi[ten])
                        return ast.copy_location(ast.parse(repr(moi), mode="eval").body, node)
                    return node
        return super().visit(node)


def node_du_lieu(cay, dau_vao):
    """Các node literal chứa dữ liệu đề cho, trên chính cây truyền vào."""
    ket_qua = []
    trong_day = _so_trong_day(cay)

    class _Tim(ast.NodeVisitor):
        def visit(self, node):
            if isinstance(node, ast.JoinedStr):
                return
            if isinstance(node, _LITERAL):
                try:
                    v = ast.literal_eval(node)
                except Exception:
                    v = _KHONG
                if v is not _KHONG and any(_khop(k, v, node, trong_day) for k in dau_vao.values()):
                    ket_qua.append(node)
                    return
            self.generic_visit(node)

    _Tim().visit(cay)
    return ket_qua


def cac_literal(cay):
    """Mọi literal trong code (trừ trong f-string) kèm giá trị - tính một lần để dò nhiều phần."""
    ket_qua = []

    def di(node):
        if isinstance(node, ast.JoinedStr):
            return
        if isinstance(node, _LITERAL):
            try:
                ket_qua.append((node, ast.literal_eval(node)))
            except Exception:
                pass
        for con in ast.iter_child_nodes(node):
            di(con)

    di(cay)
    return ket_qua, _so_trong_day(cay)


def co_du_lieu(literal, dau_vao):
    """Code (đã tính sẵn bằng cac_literal) có chứa dữ liệu đề cho của phần này không."""
    cac_lit, trong_day = literal
    return any(_khop(kieu, v, node, trong_day) for node, v in cac_lit for kieu in dau_vao.values())


def tim_du_lieu(cay, dau_vao):
    """Tên các dữ liệu đầu vào của đề tìm thấy trong code."""
    t = _ThayThe(dau_vao, None, _so_trong_day(cay))
    t.visit(cay)
    return t.tim_thay


def thay_du_lieu(cay, dau_vao, thay_doi):
    """Trả về (cây AST mới đã thay dữ liệu, tập tên dữ liệu tìm thấy)."""
    ban_sao = copy.deepcopy(cay)
    t = _ThayThe(dau_vao, thay_doi, _so_trong_day(ban_sao))
    cay_moi = ast.fix_missing_locations(t.visit(ban_sao))
    return cay_moi, t.tim_thay
