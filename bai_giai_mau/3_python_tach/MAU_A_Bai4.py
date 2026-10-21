"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 4 (Kết nối những chặng đường) - Thành viên A"""
import heapq


def duong_di_ngan_nhat(canh, nguon="S", dich="T"):
    """Dijkstra trên đồ thị vô hướng, trọng số dương."""
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


canh = [
    ('S', 'A', 4),
    ('S', 'B', 9),
    ('A', 'C', 6),
    ('B', 'C', 3),
    ('C', 'T', 10),
    ('A', 'T', 18),
    ('B', 'T', 15),
]
A = duong_di_ngan_nhat(canh)
print("A =", A)
