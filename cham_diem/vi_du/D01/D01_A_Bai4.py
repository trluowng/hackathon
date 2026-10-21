# Dijkstra tren danh sach ke dang dict
import heapq

graph = {
    "S": {"A": 4, "B": 9},
    "A": {"S": 4, "C": 6, "T": 18},
    "B": {"S": 9, "C": 3, "T": 15},
    "C": {"A": 6, "B": 3, "T": 10},
    "T": {"C": 10, "A": 18, "B": 15},
}

dist = {u: float("inf") for u in graph}
dist["S"] = 0
pq = [(0, "S")]
while pq:
    d, u = heapq.heappop(pq)
    if d > dist[u]:
        continue
    for v, w in graph[u].items():
        if d + w < dist[v]:
            dist[v] = d + w
            heapq.heappush(pq, (dist[v], v))

A = dist["T"]
print("A =", A)
