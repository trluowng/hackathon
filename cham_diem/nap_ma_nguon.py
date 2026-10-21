"""Đọc bài làm .py hoặc .ipynb thành mã nguồn Python chạy được.

Notebook: chỉ lấy các ô code theo thứ tự và BỎ QUA output đã lưu khi chấm (file .ipynb là JSON,
output sửa tay được nên không dùng làm bằng chứng). Output đã lưu chỉ được giữ lại để đối chiếu.
Cú pháp riêng của Jupyter (%magic, !lệnh, x = !lệnh, obj?) bị vô hiệu hóa; %%time/%%timeit/%%capture
giữ lại thân ô; biểu thức cuối mỗi ô được in ra giống cách Jupyter hiển thị.
Mỗi ô được đánh dấu bằng câu lệnh MOC_O(n) để khi chạy, harness chạy từng ô riêng.
"""
import ast
import json
import re
from dataclasses import dataclass

HAM_HIEN_THI = "_hien_thi_ket_qua_"
MOC_O = "_o_code_"
_MAGIC_GIU_THAN = ("%%time", "%%timeit", "%%capture", "%%prun")


class LoiNapFile(Exception):
    pass


@dataclass
class BaiLam:
    ma_nguon: str
    la_notebook: bool
    output_da_luu: str = ""


def _noi(x):
    return "".join(x) if isinstance(x, list) else (x or "")


def _la_print(node):
    return isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("print", "display")


def nap(duong_dan):
    if duong_dan.lower().endswith(".ipynb"):
        return _nap_notebook(duong_dan)
    for ma_hoa in ("utf-8-sig", "cp1258", "latin-1"):
        try:
            with open(duong_dan, encoding=ma_hoa) as f:
                return BaiLam(f.read(), False)
        except UnicodeDecodeError:
            continue
    raise LoiNapFile("Không đọc được file")


def _nap_notebook(duong_dan):
    try:
        with open(duong_dan, encoding="utf-8") as f:
            nb = json.load(f)
    except (ValueError, UnicodeDecodeError) as e:
        raise LoiNapFile("File .ipynb không hợp lệ: %s" % e)

    cac_o = nb.get("cells") or [c for ws in nb.get("worksheets", []) for c in ws.get("cells", [])]
    phan, output = [], []
    so_o = 0
    for o in cac_o:
        if o.get("cell_type") != "code":
            continue
        so_o += 1
        for out in o.get("outputs", []):
            if "text" in out:
                output.append(_noi(out["text"]))
            elif "text/plain" in out.get("data", {}):
                output.append(_noi(out["data"]["text/plain"]))

        src = _noi(o.get("source", "")).lstrip("\n")
        if src.lstrip().startswith("%%"):
            dong_dau, _, than = src.lstrip().partition("\n")
            if dong_dau.split()[0] not in _MAGIC_GIU_THAN:
                continue  # %%bash, %%html, %%writefile...: không phải code Python
            src = than
        dong = []
        for d in src.splitlines():
            s = d.lstrip()
            thut_le = d[: len(d) - len(s)]
            gan_magic = re.match(r"^([\w, ]+?)\s*=\s*[!%]", s)
            if s.startswith(("%", "!")) or re.match(r"^\?*[\w.]+\?{1,2}$|^\?+[\w.]+$", s):
                d = thut_le + "pass  # " + s
            elif gan_magic:
                d = thut_le + gan_magic.group(1) + " = None  # " + s
            dong.append(d)
        try:
            cay = ast.parse("\n".join(dong))
        except SyntaxError as e:
            raise LoiNapFile("Ô code thứ %d lỗi cú pháp: %s" % (so_o, e.msg))

        if cay.body and isinstance(cay.body[-1], ast.Expr) and not _la_print(cay.body[-1].value):
            cuoi = cay.body[-1]
            cay.body[-1] = ast.copy_location(
                ast.Expr(ast.Call(ast.Name(HAM_HIEN_THI, ast.Load()), [cuoi.value], [])), cuoi
            )
            ast.fix_missing_locations(cay)
        phan.append("%s(%d)\n%s" % (MOC_O, so_o, ast.unparse(cay)))

    if not phan:
        raise LoiNapFile("Notebook không có ô code nào")
    return BaiLam("\n\n".join(phan), True, "\n".join(output))
