"""Cấu hình đề Vòng 1: dữ liệu đề cho, hàm tham chiếu của BTC, test ẩn và luật kiểm tra tĩnh.

Đáp án của từng phần KHÔNG ghi tay mà được tính từ hàm tham chiếu trên dữ liệu đề cho,
nên khi thêm test ẩn chỉ cần ghi dữ liệu mới, kết quả mong đợi sẽ tự tính.

DE_THI[1..5]: 5 bài thi (có điểm). DE_THI["H"]: Hidden Challenge (không cộng điểm, kết quả là chuỗi).
"""
import heapq
import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from kiem_tra_tinh import CANH_BAO, LOI, can_dict, can_vong_lap, cam_goi, cam_thu_vien, khong_doi_thanh_chuoi
from thay_du_lieu import CanhDoThi, Chuoi, DanhSach, Diem, DuLieuKNN, LuoiKyTu, So

HIDDEN_BAI = "H"


@dataclass
class PhanThi:
    dau_vao: dict                  # tên -> kiểu dữ liệu (thay_du_lieu), giữ giá trị gốc của đề
    tham_chieu: Callable           # hàm của BTC, nhận đúng các tên trong dau_vao
    test_an: list                  # mỗi test: {tên: giá trị mới}
    luat: list = field(default_factory=list)
    giu_nguyen: Optional[str] = None   # biến đầu vào không được bị sửa sau khi chạy

    @property
    def goc(self):
        return {ten: kieu.goc for ten, kieu in self.dau_vao.items()}

    @property
    def dap_an(self):
        return self.tham_chieu(**self.goc)

    @property
    def la_chuoi(self):
        """Kết quả là chuỗi (Hidden Challenge) thay vì số."""
        return isinstance(self.dap_an, str)


# ---------- Hàm tham chiếu của BTC ----------

def tong_chu_so(n):
    return sum(int(c) for c in str(n))


def dem_so_chan(n):
    return sum(1 for x in range(1, n + 1) if x % 2 == 0)


def dem_chu_cai(text):
    return sum(1 for c in text if "A" <= c <= "Z" or "a" <= c <= "z")


def max_tru_min(data):
    return max(data) - min(data)


def lon2_tru_nho2(data):
    khac_nhau = sorted(set(data))
    return khac_nhau[-2] - khac_nhau[1]


def chan_tru_le(data):
    return sum(data[0::2]) - sum(data[1::2])


def _max_tan_suat(cac_tu):
    dem = {}
    for t in cac_tu:
        dem[t] = dem.get(t, 0) + 1
    return max(dem.values())


def tan_suat_hoat_dong(events):
    return _max_tan_suat(e.strip().upper() for e in events)


def tan_suat_chuoi(text):
    return _max_tan_suat(t.strip().upper() for t in text.split(",") if t.strip())


def tan_suat_clb(records):
    return _max_tan_suat(r[0] for r in records)


def duong_ngan_nhat(edges, nguon="S", dich="T"):
    ke = {}
    for u, v, w in edges:
        ke.setdefault(u, []).append((v, w))
        ke.setdefault(v, []).append((u, w))
    dist = {nguon: 0}
    heap = [(0, nguon)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist[u]:
            continue
        for v, w in ke[u]:
            if d + w < dist.get(v, math.inf):
                dist[v] = d + w
                heapq.heappush(heap, (dist[v], v))
    return dist[dich]


def _manhattan(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def knn1(train, P):
    """KNN k = 1, khoảng cách Manhattan. Dữ liệu đề và test ẩn đều có duy nhất một điểm gần nhất."""
    kc = sorted(_manhattan(P, r) for r in train)
    assert len(kc) < 2 or kc[0] < kc[1], "Dữ liệu KNN có hai điểm gần nhất bằng nhau: %s, %s" % (train, P)
    return min(train, key=lambda r: _manhattan(P, r))[2]


def zich_zac(grid):
    """Hàng chẵn (0, 2, ...) đọc trái -> phải, hàng lẻ phải -> trái, bỏ ký tự đệm #."""
    ra = []
    for i, hang in enumerate(grid):
        ra += list(hang) if i % 2 == 0 else list(hang)[::-1]
    return "".join(c for c in ra if c != "#")


def khoi_phuc_thu_tu(data):
    return "".join(c for _, c in sorted(data, key=lambda x: x[0]))


def doc_cot_tu_duoi(grid):
    ra = []
    for cot in range(len(grid[0])):
        for hang in range(len(grid) - 1, -1, -1):
            ra.append(grid[hang][cot])
    return "".join(c for c in ra if c != "#")


# ---------- Đề thi ----------

_CAM_SORT = cam_goi(LOI, "sort", "sorted", ly_do="đề cấm sort()/sorted()")
_CAM_MAX_MIN = cam_goi(LOI, "max", "min", ly_do="đề cấm max()/min() ở phần A và B")
_CAM_COUNTER = cam_thu_vien(LOI, "collections.Counter", ly_do="đề yêu cầu tự tạo bảng tần suất bằng dict")
_CANH_BAO_PANDAS = cam_thu_vien(CANH_BAO, "pandas")
_CAM_SKLEARN = cam_thu_vien(LOI, "sklearn", ly_do="đề cấm scikit-learn")
_CANH_BAO_THU_VIEN_DO_THI = cam_thu_vien(CANH_BAO, "networkx", "scipy.sparse.csgraph")

_G1 = [("S", "A", 2), ("S", "B", 5), ("A", "B", 1), ("A", "C", 7), ("B", "C", 2), ("C", "T", 3), ("B", "T", 9)]
_G2 = [("S", "X", 5), ("X", "T", 5), ("S", "T", 9), ("S", "Y", 1), ("Y", "X", 1)]

DE_THI = {
    1: {
        "A": PhanThi({"n": So(4728)}, tong_chu_so,
                     [{"n": 9081}, {"n": 505}],
                     [can_vong_lap(), khong_doi_thanh_chuoi("n")]),
        "B": PhanThi({"n": So(28)}, dem_so_chan,
                     [{"n": 41}, {"n": 9}],
                     [can_vong_lap()]),
        "C": PhanThi({"text": Chuoi("UNETI70AI")}, dem_chu_cai,
                     [{"text": "OLYMPIC2026AI"}, {"text": "K70UNETI"}]),
    },
    2: {
        "A": PhanThi({"data": DanhSach([8, 11, 15, 22, 10])}, max_tru_min,
                     [{"data": [3, 27, 12, 8, 15]}, {"data": [-4, 12, 6, 0]}],
                     [can_vong_lap(), _CAM_SORT, _CAM_MAX_MIN]),
        "B": PhanThi({"data": DanhSach([4, 10, 19, 18, 2])}, lon2_tru_nho2,
                     [{"data": [7, 3, 15, 1, 9]}, {"data": [20, 4, 11, 30, 2, 17]}],
                     [can_vong_lap(), _CAM_SORT, _CAM_MAX_MIN], giu_nguyen="data"),
        "C": PhanThi({"data": DanhSach([10, 1, 6, 1])}, chan_tru_le,
                     [{"data": [4, 8, 15, 16, 23]}, {"data": [10, 3, 6, 2, 1, 5]}],
                     [_CAM_SORT]),
    },
    3: {
        "A": PhanThi({"events": DanhSach(["AI", "STEM", "ai", "DATA", "Ai", "ROBOT", "AI", "ai"])},
                     tan_suat_hoat_dong,
                     [{"events": ["ROBOT", "robot", "AI", "Robot", "stem", "ROBOT", "ai"]},
                      {"events": ["stem", "STEM", "Data", "data", "DATA", "Ai"]}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
        "B": PhanThi({"text": Chuoi("code, AI, CODE, STEM, Code, ROBOT, code, DATA, CODE")}, tan_suat_chuoi,
                     [{"text": "AI, ai , Stem, AI,ROBOT, Ai, data"},
                      {"text": "robot , ROBOT,stem, Robot, uneti"}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
        "C": PhanThi({"records": DanhSach([("DSC", 2024), ("STEM", 2024), ("DSC", 2025), ("ROBOT", 2025),
                                           ("DSC", 2026), ("AI", 2026), ("DSC", 2026), ("DSC", 2027)])},
                     tan_suat_clb,
                     [{"records": [("AC", 2024), ("BOOK", 2025), ("AC", 2025), ("AC", 2026), ("DSC", 2026)]},
                      {"records": [("STEM", 2024), ("STEM", 2025), ("BOOK", 2025), ("STEM", 2026),
                                   ("BOOK", 2026), ("STEM", 2026), ("ROBOT", 2027), ("ROBOT", 2027)]}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
    },
    4: {
        "A": PhanThi({"edges": CanhDoThi([("S", "A", 6), ("S", "B", 9), ("A", "C", 5), ("B", "C", 4),
                                          ("C", "T", 9), ("A", "T", 19), ("B", "T", 18)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
        "B": PhanThi({"edges": CanhDoThi([("S", "A", 8), ("S", "B", 4), ("A", "D", 7), ("B", "D", 6),
                                          ("D", "T", 10), ("A", "T", 20), ("B", "T", 19)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
        "C": PhanThi({"edges": CanhDoThi([("S", "X", 5), ("S", "Y", 7), ("X", "Z", 6), ("Y", "Z", 6),
                                          ("Z", "T", 9), ("X", "T", 18), ("Y", "T", 16)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
    },
    5: {
        # Test 1 đổi nhãn của điểm gần nhất (bắt hard-code nhãn 9), test 2 đổi điểm P sang gần điểm khác.
        "A": PhanThi({"train": DuLieuKNN([(4, 5, 9), (2, 2, 3), (7, 6, 2), (1, 8, 4)]), "P": Diem((4, 4))},
                     knn1,
                     [{"train": [(4, 5, 6), (2, 2, 3), (7, 6, 2), (1, 8, 4)]}, {"P": (7, 7)}],
                     [_CAM_SKLEARN]),
        "B": PhanThi({"train": DuLieuKNN([(6, 4, 9), (3, 3, 5), (8, 7, 2), (9, 9, 6)]), "P": Diem((6, 5))},
                     knn1,
                     [{"train": [(6, 4, 1), (3, 3, 5), (8, 7, 2), (9, 9, 6)]}, {"P": (3, 2)}],
                     [_CAM_SKLEARN]),
        "C": PhanThi({"train": DuLieuKNN([(3, 5, 9), (5, 6, 3), (1, 2, 7), (6, 9, 4)]), "P": Diem((3, 6))},
                     knn1,
                     [{"train": [(3, 5, 8), (5, 6, 3), (1, 2, 7), (6, 9, 4)]}, {"P": (1, 3)}],
                     [_CAM_SKLEARN]),
    },
    HIDDEN_BAI: {
        "A": PhanThi({"grid": LuoiKyTu(["UN#", "ITE"])}, zich_zac,
                     [{"grid": ["OLY", "IPM"]}, {"grid": ["#AI", "#07"]}],
                     [can_vong_lap()]),
        "B": PhanThi({"data": DanhSach([(4, "A"), (1, "7"), (5, "M"), (3, "N"), (2, "0")])}, khoi_phuc_thu_tu,
                     [{"data": [(3, "E"), (1, "U"), (2, "N"), (5, "I"), (4, "T")]},
                      {"data": [(2, "I"), (4, "0"), (1, "A"), (3, "7")]}]),
        "C": PhanThi({"grid": LuoiKyTu(["OA", "UX", "VN"])}, doc_cot_tu_duoi,
                     [{"grid": ["AI", "70", "UN"]}, {"grid": ["MA", "AN", "NA"]}],
                     [can_vong_lap()]),
    },
}

CAC_BAI = [1, 2, 3, 4, 5]
DAP_AN_K = {1: 21, 2: 14, 3: 5, 4: 20, 5: 9}
MANH_KHOA = "UNETI"
TU_KHOA = "UNETI"
MAT_KHAU = "UNETI70"
HIDDEN = {"A": "UNETI", "B": "70NAM", "C": "VUONXA"}
THONG_DIEP = "UNETI 70 NAM VUON XA"


def tinh_checkpoint(bai, a, b, c):
    if bai == 1:
        return a + b - 2 * c
    return a if a == b == c else None


# Đáp án tính từ hàm tham chiếu phải khớp đáp án chính thức của BTC,
# và mỗi test ẩn phải cho kết quả KHÁC đáp án đề (nếu trùng thì code hard-code vẫn qua test).
for _bai, _k in DAP_AN_K.items():
    assert tinh_checkpoint(_bai, *(DE_THI[_bai][tv].dap_an for tv in "ABC")) == _k, "Sai cấu hình bài %d" % _bai
for _tv, _manh in HIDDEN.items():
    assert DE_THI[HIDDEN_BAI][_tv].dap_an == _manh, "Sai cấu hình Hidden %s" % _tv
for _bai, _cac_phan in DE_THI.items():
    for _tv, _phan in _cac_phan.items():
        for _test in _phan.test_an:
            assert _phan.tham_chieu(**{**_phan.goc, **_test}) != _phan.dap_an, \
                "Test ẩn %s của bài %s phần %s cho kết quả trùng đáp án đề" % (_test, _bai, _tv)
