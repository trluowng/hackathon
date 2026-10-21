import heapq

du_lieu = """
S A 7
S B 5
A D 8
B D 6
D T 9
A T 16
B T 18
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
B = dist["T"]
print("B =", B)
