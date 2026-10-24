# Bai 4 - Thanh vien C: duong di ngan nhat S -> T (Dijkstra)
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


do_thi = {
    "S": {"X": 5, "Y": 7},
    "X": {"S": 5, "Z": 6, "T": 18},
    "Y": {"S": 7, "Z": 6, "T": 16},
    "Z": {"X": 6, "Y": 6, "T": 9},
    "T": {"Z": 9, "X": 18, "Y": 16},
}
edges = [(u, v, w) for u in do_thi for v, w in do_thi[u].items()]
C = duong_ngan_nhat(edges)
print("C =", C)
