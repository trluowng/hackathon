import heapq

du_lieu = """
S A 4
S B 9
A C 6
B C 3
C T 10
A T 18
B T 15
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
A = dist["T"]
print("A =", A)
