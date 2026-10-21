# Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình"
# Bài 5. UNETI vươn xa - Đội MAU
# KNN tự cài đặt (k = 3), không dùng scikit-learn.
import math


def du_doan_knn(train, P, k=3):
    # 1. Khoảng cách Euclidean từ P đến toàn bộ dữ liệu huấn luyện
    khoang_cach = []
    for x, y, nhan in train:
        d = math.sqrt((x - P[0]) ** 2 + (y - P[1]) ** 2)
        khoang_cach.append((d, nhan))
    # 2. Sắp xếp theo khoảng cách tăng dần
    khoang_cach.sort(key=lambda t: t[0])
    # 3. Chọn k điểm gần nhất, 4. bỏ phiếu đa số
    phieu = {}
    for d, nhan in khoang_cach[:k]:
        phieu[nhan] = phieu.get(nhan, 0) + 1
    return max(phieu, key=phieu.get)


# ----- Thành viên A -----
train = [(1, 1, 9), (2, 2, 9), (2, 3, 9), (8, 8, 3), (9, 9, 3)]
P = (3, 3)
A = du_doan_knn(train, P, k=3)
print("A =", A)

# ----- Thành viên B -----
train = [(1, 7, 4), (2, 8, 4), (7, 2, 9), (8, 3, 9), (7, 4, 9)]
P = (6, 3)
B = du_doan_knn(train, P, k=3)
print("B =", B)

# ----- Thành viên C -----
train = [(2, 1, 9), (3, 2, 9), (4, 2, 9), (8, 7, 6), (9, 8, 6)]
P = (4, 3)
C = du_doan_knn(train, P, k=3)
print("C =", C)

# ----- Checkpoint 5: ba kết quả đúng thì A = B = C = K5 -----
if A == B == C:
    K5 = A
    print("K5 =", K5, "->", chr(ord("A") + K5 - 1))
else:
    print("Chưa khớp: A, B, C =", A, B, C, "- kiểm tra lại")
