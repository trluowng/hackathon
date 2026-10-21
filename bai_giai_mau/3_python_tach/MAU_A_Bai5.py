"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 5 (UNETI vươn xa) - Thành viên A"""
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


train = [(1, 1, 9), (2, 2, 9), (2, 3, 9), (8, 8, 3), (9, 9, 3)]
P = (3, 3)
A = du_doan_knn(train, P, k=3)
print("A =", A)
