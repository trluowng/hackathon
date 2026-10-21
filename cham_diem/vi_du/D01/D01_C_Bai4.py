# Bellman-Ford tren danh sach canh
edges = [("S", "X", 3), ("S", "Y", 8), ("X", "Z", 7), ("Y", "Z", 4),
         ("Z", "T", 10), ("X", "T", 18), ("Y", "T", 15)]
dist = {"S": 0}
for _ in range(len(edges)):
    for u, v, w in edges:
        for a, b in ((u, v), (v, u)):
            if a in dist and dist[a] + w < dist.get(b, float("inf")):
                dist[b] = dist[a] + w
C = dist["T"]
print("C =", C)
