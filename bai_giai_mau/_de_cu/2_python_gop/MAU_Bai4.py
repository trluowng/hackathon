# Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình"
# Bài 4. Kết nối những chặng đường - Đội MAU
# Đồ thị vô hướng, trọng số dương: tìm tổng trọng số nhỏ nhất từ S đến T bằng Dijkstra.
import heapq


def duong_di_ngan_nhat(canh, nguon="S", dich="T"):
    ke = {}
    for u, v, w in canh:
        ke.setdefault(u, []).append((v, w))
        ke.setdefault(v, []).append((u, w))
    khoang_cach = {nguon: 0}
    hang_doi = [(0, nguon)]
    while hang_doi:
        d, u = heapq.heappop(hang_doi)
        if d > khoang_cach[u]:
            continue
        for v, w in ke[u]:
            if d + w < khoang_cach.get(v, float("inf")):
                khoang_cach[v] = d + w
                heapq.heappush(hang_doi, (d + w, v))
    return khoang_cach[dich]


# ----- Thành viên A -----
canh = [
    ("S", "A", 4), ("S", "B", 9), ("A", "C", 6), ("B", "C", 3),
    ("C", "T", 10), ("A", "T", 18), ("B", "T", 15),
]
A = duong_di_ngan_nhat(canh)
print("A =", A)

# ----- Thành viên B -----
canh = [
    ("S", "A", 7), ("S", "B", 5), ("A", "D", 8), ("B", "D", 6),
    ("D", "T", 9), ("A", "T", 16), ("B", "T", 18),
]
B = duong_di_ngan_nhat(canh)
print("B =", B)

# ----- Thành viên C -----
canh = [
    ("S", "X", 3), ("S", "Y", 8), ("X", "Z", 7), ("Y", "Z", 4),
    ("Z", "T", 10), ("X", "T", 18), ("Y", "T", 15),
]
C = duong_di_ngan_nhat(canh)
print("C =", C)

# ----- Checkpoint 4: ba kết quả đúng thì A = B = C = K4 -----
if A == B == C:
    K4 = A
    print("K4 =", K4, "->", chr(ord("A") + K4 - 1))
else:
    print("Chưa khớp: A, B, C =", A, B, C, "- kiểm tra lại")
