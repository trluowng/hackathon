import heapq

du_lieu = """
S X 3
S Y 8
X Z 7
Y Z 4
Z T 10
X T 18
Y T 15
"""

graph = {}
for line in du_lieu.strip().splitlines():
    u, v, w = line.split()
    graph.setdefault(u, []).append((v, int(w)))
    graph.setdefault(v, []).append((u, int(w)))

dist = {u: float("inf") for u in graph}
dist["S"] = 0
heap = [(0, "S")]
while heap:
    d, u = heapq.heappop(heap)
    if d > dist[u]:
        continue
    for v, w in graph[u]:
        if d + w < dist[v]:
            dist[v] = d + w
            heapq.heappush(heap, (dist[v], v))
C = dist["T"]
print("C =", C)
