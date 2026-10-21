import heapq
import math

# ================= BAI 2 =================
# A (vi pham: dung sorted)
data = [5, 19, 8, 13, 7]
s = sorted(data)
print("Bai 2 - A:", s[-1] - s[0])

# B
data = [1, 2, 5, 16, 19]
l1 = l2 = n1 = n2 = None
for x in data:
    if l1 is None or x > l1:
        l2, l1 = l1, x
    elif l2 is None or x > l2:
        l2 = x
    if n1 is None or x < n1:
        n2, n1 = n1, x
    elif n2 is None or x < n2:
        n2 = x
print("Bai 2 - B:", l2 - n2)

# C
data = [9, 1, 7, 1]
chan = le = 0
for i in range(len(data)):
    if i % 2 == 0:
        chan += data[i]
    else:
        le += data[i]
print("Bai 2 - C:", chan - le)

# ================= BAI 3 =================
activities = ["AI", "data", "AI", "ROBOT", "ai", "DATA", "Ai", "STEM", "AI"]
dem_a = {}
for a in activities:
    dem_a[a.upper()] = dem_a.get(a.upper(), 0) + 1
print("Bai 3 - A:", max(dem_a.values()))

text = "UNETI, Data, data, AI, DATA, STEM, data, ROBOT, DATA"
dem_b = {}
for w in text.split(","):
    dem_b[w.strip().upper()] += 1          # loi: chua khoi tao -> KeyError
print("Bai 3 - B:", max(dem_b.values()))

records = [("DSC", 2024), ("STEM", 2024), ("DSC", 2025), ("AC", 2025), ("DSC", 2026),
           ("BOOK", 2026), ("DSC", 2026), ("STEM", 2026), ("DSC", 2026)]
dem_c = {}
for ten, nam in records:
    dem_c[ten] = dem_c.get(ten, 0) + 1
print("Bai 3 - C:", max(dem_c.values()))

# ================= BAI 4 =================
def dijkstra(edges, s, t):
    g = {}
    for u, v, w in edges:
        g.setdefault(u, []).append((v, w))
        g.setdefault(v, []).append((u, w))
    dist = {s: 0}
    pq = [(0, s)]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in g[u]:
            if d + w < dist.get(v, math.inf):
                dist[v] = d + w
                heapq.heappush(pq, (dist[v], v))
    return dist[t]

print("Bai 4 - A:", dijkstra([("S", "A", 4), ("S", "B", 9), ("A", "C", 6), ("B", "C", 3),
                              ("C", "T", 10), ("A", "T", 18), ("B", "T", 15)], "S", "T"))
print("Bai 4 - B:", dijkstra([("S", "A", 7), ("S", "B", 5), ("A", "D", 8), ("B", "D", 6),
                              ("D", "T", 9), ("A", "T", 16), ("B", "T", 18)], "S", "T"))
print("Bai 4 - C:", dijkstra([("S", "X", 3), ("S", "Y", 8), ("X", "Z", 7), ("Y", "Z", 4),
                              ("Z", "T", 10), ("X", "T", 18), ("Y", "T", 15)], "S", "T"))

# ================= BAI 5 =================
def du_doan(train, P, k=3):
    kc = [(math.sqrt((x - P[0]) ** 2 + (y - P[1]) ** 2), nhan) for x, y, nhan in train]
    kc.sort()
    phieu = {}
    for _, nhan in kc[:k]:
        phieu[nhan] = phieu.get(nhan, 0) + 1
    return max(phieu, key=phieu.get)


def main():
    train = [(1, 1, 9), (2, 2, 9), (2, 3, 9), (8, 8, 3), (9, 9, 3)]
    P = (3, 3)
    print("Bai 5 - A:", du_doan(train, P))

    train = [(1, 7, 4), (2, 8, 4), (7, 2, 9), (8, 3, 9), (7, 4, 9)]
    P = (6, 3)
    print("Bai 5 - B:", du_doan(train, P))

    train = [(2, 1, 9), (3, 2, 9), (4, 2, 9), (8, 7, 6), (9, 8, 6)]
    P = (4, 3)
    print("Bai 5 - C:", du_doan(train, P))


if __name__ == "__main__":
    main()
