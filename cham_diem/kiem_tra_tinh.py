"""Kiểm tra tĩnh (đọc AST, không chạy code) các ràng buộc đề đặt ra cho từng phần.

Mỗi luật là một hàm nhận cây AST, trả về list (mức độ, thông điệp).
LOI: vi phạm yêu cầu đề -> 0 điểm phần đó. CANH_BAO: không trừ điểm, đánh dấu để người xem lại.
Luật có thuộc tính yeu_cau = True là luật "phải có" (khác luật "cấm").
"""
import ast

LOI = "loi"
CANH_BAO = "canh_bao"


def _ten_ham(call):
    f = call.func
    if isinstance(f, ast.Name):
        return f.id
    if isinstance(f, ast.Attribute):
        return f.attr
    return None


def _ten_cham(node):
    """collections.Counter -> 'collections.Counter'."""
    phan = []
    while isinstance(node, ast.Attribute):
        phan.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        phan.append(node.id)
        return ".".join(reversed(phan))
    return None


def _dong(node):
    return " (dòng %d)" % node.lineno if getattr(node, "lineno", None) else ""


def can_vong_lap():
    def kiem_tra(cay):
        if any(isinstance(n, (ast.For, ast.While, ast.comprehension)) for n in ast.walk(cay)):
            return []
        return [(LOI, "Không dùng vòng lặp (for/while) như đề yêu cầu")]
    kiem_tra.yeu_cau = True
    return kiem_tra


def _chi_de_hien_thi(cay):
    """id các node chuyển chuỗi chỉ phục vụ in ra: đối số trực tiếp của print()."""
    ok = set()

    def danh_dau(node):
        if isinstance(node, ast.JoinedStr):
            ok.update(id(v) for v in node.values if isinstance(v, ast.FormattedValue))
        elif isinstance(node, ast.Call) and _ten_ham(node) in ("str", "repr", "format"):
            ok.add(id(node))
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
            danh_dau(node.left)
            danh_dau(node.right)
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            ok.add(id(node))

    for n in ast.walk(cay):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "print":
            for a in n.args:
                danh_dau(a)
    return ok


def khong_doi_thanh_chuoi(ten_bien):
    """Cấm chuyển biến đầu vào (và bí danh kiểu n = year) thành chuỗi để tính toán."""
    def kiem_tra(cay):
        bi_danh = {ten_bien}
        doi = True
        while doi:
            doi = False
            for n in ast.walk(cay):
                if isinstance(n, ast.Assign) and isinstance(n.value, ast.Name) and n.value.id in bi_danh:
                    for t in n.targets:
                        if isinstance(t, ast.Name) and t.id not in bi_danh:
                            bi_danh.add(t.id)
                            doi = True

        def dung_bien(node):
            return any(isinstance(m, ast.Name) and m.id in bi_danh for m in ast.walk(node))

        hien_thi = _chi_de_hien_thi(cay)
        ket_qua = []
        for n in ast.walk(cay):
            if id(n) in hien_thi:
                continue
            doi_so = None
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in ("str", "repr", "format", "ascii"):
                doi_so = n.args
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "format" \
                    and isinstance(n.func.value, ast.Constant):
                doi_so = n.args
            elif isinstance(n, ast.FormattedValue):
                doi_so = [n.value]
            elif isinstance(n, ast.BinOp) and isinstance(n.op, ast.Mod) and isinstance(n.left, ast.Constant) \
                    and isinstance(n.left.value, str):
                doi_so = [n.right]
            if doi_so and any(dung_bien(a) for a in doi_so):
                ket_qua.append((LOI, "Chuyển `%s` thành chuỗi%s - đề cấm" % (ten_bien, _dong(n))))
        return ket_qua
    return kiem_tra


def cam_goi(muc_do, *ten, ly_do=""):
    def kiem_tra(cay):
        ket_qua = []
        for n in ast.walk(cay):
            if isinstance(n, ast.Call) and _ten_ham(n) in ten:
                ket_qua.append((muc_do, "Dùng %s()%s%s" % (_ten_ham(n), _dong(n), " - " + ly_do if ly_do else "")))
        return ket_qua
    return kiem_tra


def cam_thu_vien(muc_do, *mau, ly_do=""):
    """Phát hiện import/dùng thư viện, vd 'sklearn', 'collections.Counter'."""
    def khop(ten):
        return any(ten == m or ten.startswith(m + ".") for m in mau)

    def kiem_tra(cay):
        ket_qua = []
        for n in ast.walk(cay):
            cac_ten = []
            if isinstance(n, ast.Import):
                cac_ten = [a.name for a in n.names]
            elif isinstance(n, ast.ImportFrom):
                mod = n.module or ""
                cac_ten = [mod] + [mod + "." + a.name for a in n.names]
            elif isinstance(n, ast.Attribute):
                t = _ten_cham(n)
                cac_ten = [t] if t else []
            elif isinstance(n, ast.Call) and _ten_ham(n) in ("__import__", "import_module") and n.args \
                    and isinstance(n.args[0], ast.Constant) and isinstance(n.args[0].value, str):
                cac_ten = [n.args[0].value]
            for t in cac_ten:
                if khop(t):
                    ket_qua.append((muc_do, "Dùng %s%s%s" % (t, _dong(n), " - " + ly_do if ly_do else "")))
                    break
        return ket_qua
    return kiem_tra


def can_dict():
    def kiem_tra(cay):
        for n in ast.walk(cay):
            if isinstance(n, (ast.Dict, ast.DictComp)):
                return []
            if isinstance(n, ast.Call) and _ten_ham(n) in ("dict", "defaultdict", "OrderedDict"):
                return []
        return [(LOI, "Không thấy tự xây dựng dictionary như đề yêu cầu")]
    kiem_tra.yeu_cau = True
    return kiem_tra
