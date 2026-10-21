"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 5 (UNETI vươn xa) - Thành viên C"""
import math


def du_doan_knn(train, P, k=3):
    """Gán nhãn chiếm đa số trong k điểm gần P nhất (khoảng cách Euclidean)."""
    khoang_cach = []
    for x, y, nhan in train:
        d = math.sqrt((x - P[0]) ** 2 + (y - P[1]) ** 2)
        khoang_cach.append((d, nhan))
    khoang_cach.sort(key=lambda t: t[0])      # sắp xếp theo khoảng cách tăng dần
    phieu = {}
    for d, nhan in khoang_cach[:k]:           # chọn k điểm gần nhất
        phieu[nhan] = phieu.get(nhan, 0) + 1
    return max(phieu, key=phieu.get)          # bỏ phiếu đa số


train = [(2, 1, 9), (3, 2, 9), (4, 2, 9), (8, 7, 6), (9, 8, 6)]
P = (4, 3)
C = du_doan_knn(train, P, k=3)
print("C =", C)
