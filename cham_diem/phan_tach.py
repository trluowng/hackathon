"""Tách vùng code của từng phần khi một file chứa nhiều phần (gộp A/B/C, hoặc gộp nhiều bài).

Neo của một phần là câu lệnh chứa dữ liệu đề cho của phần đó. Từ neo, lan truyền xuôi theo
tên biến (lát cắt dữ liệu) để biết câu lệnh nào thuộc phần đó:
  year = 1956          <- neo phần A
  n = year             <- đọc biến của A  -> thuộc A
  while n > 0: ...     <- đọc n           -> thuộc A
  year = 2026          <- gán lại year bằng dữ liệu khác -> year không còn thuộc A
"""
import ast
import copy

_DINH_NGHIA = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def ban_do_cha(cay):
    cha = {}
    for n in ast.walk(cay):
        for c in ast.iter_child_nodes(n):
            cha[c] = n
    return cha


def _chua(cau_lenh, node, cha):
    while node is not None:
        if node is cau_lenh:
            return True
        node = cha.get(node)
    return False


def _neo(than, cac_node, cha):
    """Chỉ số các câu lệnh trong `than` có chứa một trong các node dữ liệu."""
    return {i for i, s in enumerate(than) if any(_chua(s, n, cha) for n in cac_node)}


def _doc_ghi(cau_lenh):
    """(tên được đọc, tên được ghi) của một câu lệnh."""
    if isinstance(cau_lenh, _DINH_NGHIA):
        # Định nghĩa hàm/lớp: ghi tên của nó, đọc các biến toàn cục mà thân hàm dùng.
        tham_so = {a.arg for a in ast.walk(cau_lenh) if isinstance(a, ast.arg)}
        cuc_bo = {n.id for n in ast.walk(cau_lenh) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
        doc = {n.id for n in ast.walk(cau_lenh) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
        return doc - tham_so - cuc_bo, {cau_lenh.name}
    doc, ghi = set(), set()
    for n in ast.walk(cau_lenh):
        if isinstance(n, ast.Name):
            (doc if isinstance(n.ctx, ast.Load) else ghi).add(n.id)
        elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
            doc.add(n.target.id)
        elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name):
            ghi.add(n.func.value.id)  # obj.method(...) có thể sửa obj
        elif isinstance(n, (ast.Subscript, ast.Attribute)) and isinstance(n.ctx, ast.Store):
            goc = n.value
            while isinstance(goc, (ast.Subscript, ast.Attribute)):
                goc = goc.value
            if isinstance(goc, ast.Name):
                ghi.add(goc.id)
    # Biến vòng lặp (for x in ..., [... for x in ...]) do chính câu lệnh gán, không đọc từ phần khác
    rang_buoc = {n.id for v in ast.walk(cau_lenh) if isinstance(v, (ast.For, ast.comprehension))
                 for n in ast.walk(v.target) if isinstance(n, ast.Name)}
    return doc - rang_buoc, ghi


def _lat_cat(than, chi_so_neo):
    """Chỉ số các câu lệnh trong `than` thuộc lát cắt bắt đầu từ các neo."""
    if not chi_so_neo:
        return set()
    nhiem, thuoc = set(), set()
    for i in range(min(chi_so_neo), len(than)):
        doc, ghi = _doc_ghi(than[i])
        if i in chi_so_neo or doc & nhiem:
            thuoc.add(i)
            nhiem |= ghi
        else:
            nhiem -= ghi
    return thuoc


def _them_khoi_tao(than, thuoc, cam=frozenset()):
    """Thêm các câu lệnh gán gần nhất trước đó cho biến mà lát cắt đọc (vd dem = {} trước vòng lặp).

    Không thêm câu lệnh thuộc `cam` (code của phần khác).
    """
    them = set(thuoc)
    doi = True
    while doi:
        doi = False
        ghi_gan_nhat = {}
        for i, s in enumerate(than):
            doc, ghi = _doc_ghi(s)
            if i in them:
                for ten in doc:
                    j = ghi_gan_nhat.get(ten)
                    if j is not None and j not in them and j not in cam:
                        them.add(j)
                        doi = True
            for ten in ghi:
                ghi_gan_nhat[ten] = i
    return them


def _than_chua(cau_lenh, cha):
    cha_node = cha.get(cau_lenh)
    for truong in ("body", "orelse", "finalbody"):
        than = getattr(cha_node, truong, None)
        if isinstance(than, list) and any(s is cau_lenh for s in than):
            return than
    return None


def vung_code(cay, node_phan, node_khac=()):
    """Cây AST chỉ gồm code của phần này: lát cắt + hàm/lớp nó gọi + import nó dùng."""
    cha = ban_do_cha(cay)
    cau_lenh = node_phan[0]
    while not isinstance(cau_lenh, ast.stmt):
        cau_lenh = cha[cau_lenh]
    than = _than_chua(cau_lenh, cha)
    neo = _neo(than, node_phan, cha)
    # Câu lệnh cũng nằm trong lát cắt của phần khác (vd đoạn tổng hợp đọc kết quả mọi phần)
    # không phải code riêng của phần này.
    thuoc_khac = _lat_cat(than, _neo(than, node_khac, cha) - neo) if node_khac else set()
    thuoc = (_lat_cat(than, neo) - thuoc_khac) | neo
    thuoc = _them_khoi_tao(than, thuoc, cam=thuoc_khac)
    nut = [than[i] for i in sorted(thuoc)]

    dinh_nghia = {}
    for n in ast.walk(cay):
        if isinstance(n, _DINH_NGHIA):
            dinh_nghia.setdefault(n.name, []).append(n)
    tat_ca_du_lieu = list(node_phan) + list(node_khac)
    da_co = {id(x) for x in nut}
    hang_doi = list(nut)
    while hang_doi:
        for c in ast.walk(hang_doi.pop()):
            if not isinstance(c, ast.Call):
                continue
            ten = c.func.id if isinstance(c.func, ast.Name) else getattr(c.func, "attr", None)
            for d in dinh_nghia.get(ten, []):
                # Bỏ qua hàm bao ngoài chứa dữ liệu (vd main() chứa mọi phần)
                if id(d) in da_co or any(_chua(d, n, cha) for n in tat_ca_du_lieu):
                    continue
                da_co.add(id(d))
                nut.append(d)
                hang_doi.append(d)

    ten_dung = {n.id for x in nut for n in ast.walk(x) if isinstance(n, ast.Name)}
    for n in ast.walk(cay):
        if isinstance(n, (ast.Import, ast.ImportFrom)):
            rang_buoc = {(a.asname or a.name).split(".")[0] for a in n.names}
            if rang_buoc & ten_dung:
                nut.insert(0, n)
    return ast.Module(body=nut, type_ignores=[])


def _cat_than(than, node_phan, node_khac, cha):
    neo_phan = _neo(than, node_phan, cha)
    if not neo_phan:
        return None
    neo_khac = [k for k in (_neo(than, ns, cha) for ns in node_khac) if k]
    chung = neo_phan & set().union(*neo_khac) if neo_khac else set()

    ket_qua = list(than)
    for i in chung:
        # Nhiều phần cùng nằm trong một câu lệnh (vd cùng trong main()): đi sâu vào thân.
        s = than[i]
        if not isinstance(getattr(s, "body", None), list):
            return None
        than_moi = _cat_than(s.body, node_phan, node_khac, cha)
        if than_moi is None:
            return None
        s_moi = copy.copy(s)
        s_moi.body = than_moi or [ast.Pass()]
        ket_qua[i] = s_moi

    thuoc_khac = set()
    for k in neo_khac:
        thuoc_khac |= _lat_cat(than, k - chung)
    return [ket_qua[i] for i in range(len(than)) if i in chung or i in neo_phan or i not in thuoc_khac]


def tach_chuong_trinh(cay, node_phan, node_khac):
    """Chương trình chỉ gồm phần này + code dùng chung (bỏ code thuộc riêng phần khác).

    Trả về None nếu không tách được; khi đó chạy cả file.
    """
    than = _cat_than(cay.body, node_phan, node_khac, ban_do_cha(cay))
    if than is None:
        return None
    return ast.fix_missing_locations(ast.Module(body=than, type_ignores=[]))
