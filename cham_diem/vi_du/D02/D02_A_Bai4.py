# Bai 4 - Thanh vien A: duong di ngan nhat S -> T (Dijkstra)
import heapq


def duong_ngan_nhat(canh, S="S", T="T"):
    ke = {}
    for u, v, w in canh:
        ke.setdefault(u, []).append((v, w))
        ke.setdefault(v, []).append((u, w))
    kc = {S: 0}
    hang = [(0, S)]
    while hang:
        d, u = heapq.heappop(hang)
        if d > kc[u]:
            continue
        if u == T:
            return d
        for v, w in ke[u]:
            if d + w < kc.get(v, float("inf")):
                kc[v] = d + w
                heapq.heappush(hang, (kc[v], v))
    return None


edges = [("S", "A", 6), ("S", "B", 9), ("A", "C", 5), ("B", "C", 4),
         ("C", "T", 9), ("A", "T", 19), ("B", "T", 18)]
A = duong_ngan_nhat(edges) + khong_co
print("A =", A)
