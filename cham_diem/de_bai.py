"""Cấu hình đề Vòng 1: dữ liệu đề cho, hàm tham chiếu của BTC, test ẩn và luật kiểm tra tĩnh.

Đáp án của từng phần KHÔNG ghi tay mà được tính từ hàm tham chiếu trên dữ liệu đề cho,
nên khi thêm test ẩn chỉ cần ghi dữ liệu mới, kết quả mong đợi sẽ tự tính.
"""
import heapq
import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from kiem_tra_tinh import CANH_BAO, LOI, can_dict, can_vong_lap, cam_goi, cam_thu_vien, khong_doi_thanh_chuoi
from thay_du_lieu import CanhDoThi, Chuoi, DanhSach, Diem, DuLieuKNN, So


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


# ---------- Hàm tham chiếu của BTC ----------

def tong_chu_so(year):
    return sum(int(c) for c in str(year))


def dem_chu_cai(text):
    return sum(1 for c in text if "A" <= c.upper() <= "Z")


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


def tan_suat_hoat_dong(activities):
    return _max_tan_suat(a.upper() for a in activities)


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


def knn(train, P, k=3):
    gan_nhat = sorted(train, key=lambda r: math.dist(P, r[:2]))[:k]
    phieu = {}
    for _, _, nhan in gan_nhat:
        phieu[nhan] = phieu.get(nhan, 0) + 1
    return max(phieu, key=phieu.get)


# ---------- Đề thi ----------

_CAM_SORT = cam_goi(LOI, "sort", "sorted", ly_do="đề cấm sort()/sorted()")
_CAM_COUNTER = cam_thu_vien(LOI, "collections.Counter", ly_do="đề yêu cầu tự xây dựng dict")
_CANH_BAO_PANDAS = cam_thu_vien(CANH_BAO, "pandas")
_CAM_SKLEARN = cam_thu_vien(LOI, "sklearn", ly_do="đề cấm scikit-learn")
_CANH_BAO_THU_VIEN_DO_THI = cam_thu_vien(CANH_BAO, "networkx", "scipy.sparse.csgraph")

_G1 = [("S", "A", 2), ("S", "B", 5), ("A", "B", 1), ("A", "C", 7), ("B", "C", 2), ("C", "T", 3), ("B", "T", 9)]
_G2 = [("S", "X", 5), ("X", "T", 5), ("S", "T", 9), ("S", "Y", 1), ("Y", "X", 1)]

DE_THI = {
    1: {
        "A": PhanThi({"year": So(1956)}, tong_chu_so,
                     [{"year": 1999}, {"year": 2000}, {"year": 70}],
                     [can_vong_lap(), khong_doi_thanh_chuoi("year")]),
        "B": PhanThi({"year": So(2026)}, tong_chu_so,
                     [{"year": 1975}, {"year": 1987}],
                     [can_vong_lap(), khong_doi_thanh_chuoi("year")]),
        "C": PhanThi({"text": Chuoi("UNETI2026")}, dem_chu_cai,
                     [{"text": "OLYMPIC2026AI"}, {"text": "AI70UNETI"}]),
    },
    2: {
        "A": PhanThi({"data": DanhSach([5, 19, 8, 13, 7])}, max_tru_min,
                     [{"data": [12, 3, 27, 8, 15]}, {"data": [-4, 12, 6, 0]}],
                     [_CAM_SORT, cam_goi(CANH_BAO, "max", "min", ly_do="đề yêu cầu tự duyệt từng phần tử")]),
        "B": PhanThi({"data": DanhSach([1, 2, 5, 16, 19])}, lon2_tru_nho2,
                     [{"data": [7, 3, 15, 1, 9]}, {"data": [20, 4, 11, 30, 2, 17]}],
                     [_CAM_SORT], giu_nguyen="data"),
        "C": PhanThi({"data": DanhSach([9, 1, 7, 1])}, chan_tru_le,
                     [{"data": [4, 8, 15, 16, 23]}, {"data": [10, 3, 6, 2, 1, 5]}],
                     [_CAM_SORT]),
    },
    3: {
        "A": PhanThi({"activities": DanhSach(["AI", "data", "AI", "ROBOT", "ai", "DATA", "Ai", "STEM", "AI"])},
                     tan_suat_hoat_dong,
                     [{"activities": ["ROBOT", "robot", "AI", "Robot", "stem", "ROBOT", "ai"]},
                      {"activities": ["stem", "STEM", "Data", "data", "DATA", "Ai"]}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
        "B": PhanThi({"text": Chuoi("UNETI, Data, data, AI, DATA, STEM, data, ROBOT, DATA")}, tan_suat_chuoi,
                     [{"text": "AI, ai , Stem, AI,ROBOT, Ai, data"},
                      {"text": "robot , ROBOT,stem, Robot, uneti"}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
        "C": PhanThi({"records": DanhSach([("DSC", 2024), ("STEM", 2024), ("DSC", 2025),
                                           ("AC", 2025), ("DSC", 2026), ("BOOK", 2026),
                                           ("DSC", 2026), ("STEM", 2026), ("DSC", 2026)])},
                     tan_suat_clb,
                     [{"records": [("AC", 2024), ("BOOK", 2025), ("AC", 2025), ("AC", 2026), ("DSC", 2026)]},
                      {"records": [("STEM", 2024), ("STEM", 2025), ("BOOK", 2025),
                                   ("STEM", 2026), ("BOOK", 2026), ("STEM", 2026)]}],
                     [_CAM_COUNTER, can_dict(), _CANH_BAO_PANDAS]),
    },
    4: {
        "A": PhanThi({"edges": CanhDoThi([("S", "A", 4), ("S", "B", 9), ("A", "C", 6), ("B", "C", 3),
                                          ("C", "T", 10), ("A", "T", 18), ("B", "T", 15)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
        "B": PhanThi({"edges": CanhDoThi([("S", "A", 7), ("S", "B", 5), ("A", "D", 8), ("B", "D", 6),
                                          ("D", "T", 9), ("A", "T", 16), ("B", "T", 18)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
        "C": PhanThi({"edges": CanhDoThi([("S", "X", 3), ("S", "Y", 8), ("X", "Z", 7), ("Y", "Z", 4),
                                          ("Z", "T", 10), ("X", "T", 18), ("Y", "T", 15)])},
                     duong_ngan_nhat, [{"edges": _G1}, {"edges": _G2}], [_CANH_BAO_THU_VIEN_DO_THI]),
    },
    5: {
        # Test 1 đổi nhãn (bắt hard-code nhãn), test 2 đổi điểm cần dự đoán sang cụm còn lại.
        "A": PhanThi({"train": DuLieuKNN([(1, 1, 9), (2, 2, 9), (2, 3, 9), (8, 8, 3), (9, 9, 3)]), "P": Diem((3, 3))},
                     knn,
                     [{"train": [(1, 1, 5), (2, 2, 5), (2, 3, 5), (8, 8, 8), (9, 9, 8)]}, {"P": (8, 7)}],
                     [_CAM_SKLEARN]),
        "B": PhanThi({"train": DuLieuKNN([(1, 7, 4), (2, 8, 4), (7, 2, 9), (8, 3, 9), (7, 4, 9)]), "P": Diem((6, 3))},
                     knn,
                     [{"train": [(1, 7, 2), (2, 8, 2), (7, 2, 1), (8, 3, 1), (7, 4, 1)]}, {"P": (2, 7)}],
                     [_CAM_SKLEARN]),
        "C": PhanThi({"train": DuLieuKNN([(2, 1, 9), (3, 2, 9), (4, 2, 9), (8, 7, 6), (9, 8, 6)]), "P": Diem((4, 3))},
                     knn,
                     [{"train": [(2, 1, 4), (3, 2, 4), (4, 2, 4), (8, 7, 3), (9, 8, 3)]}, {"P": (8, 8)}],
                     [_CAM_SKLEARN]),
    },
}

DAP_AN_K = {1: 21, 2: 14, 3: 5, 4: 20, 5: 9}
MANH_KHOA = "UNETI"
TU_KHOA = "UNETI"
MAT_KHAU = "UNETI70"
HIDDEN = {"A": "UNETI 70", "B": "NAM VUON", "C": "XA"}
THONG_DIEP = "UNETI 70 NAM VUON XA"


def tinh_checkpoint(bai, a, b, c):
    if bai == 1:
        return a + b - 2 * c
    return a if a == b == c else None


# Đáp án tính từ hàm tham chiếu phải khớp đáp án chính thức của BTC,
# và mỗi test ẩn phải cho kết quả KHÁC đáp án đề (nếu trùng thì code hard-code vẫn qua test).
for _bai, _k in DAP_AN_K.items():
    assert tinh_checkpoint(_bai, *(DE_THI[_bai][tv].dap_an for tv in "ABC")) == _k, "Sai cấu hình bài %d" % _bai
    for _tv in "ABC":
        _phan = DE_THI[_bai][_tv]
        for _test in _phan.test_an:
            assert _phan.tham_chieu(**{**_phan.goc, **_test}) != _phan.dap_an, \
                "Test ẩn %s của bài %d phần %s cho kết quả trùng đáp án đề" % (_test, _bai, _tv)
