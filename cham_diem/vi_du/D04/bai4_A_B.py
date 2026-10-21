import heapq

def ngan_nhat(canh):
    ke = {}
    for u, v, w in canh:
        ke.setdefault(u, []).append((v, w)); ke.setdefault(v, []).append((u, w))
    dist, pq = {"S": 0}, [(0, "S")]
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist[u]:
            continue
        for v, w in ke[u]:
            if d + w < dist.get(v, 10**9):
                dist[v] = d + w; heapq.heappush(pq, (dist[v], v))
    return dist["T"]

canh_A = [("S","A",4),("S","B",9),("A","C",6),("B","C",3),("C","T",10),("A","T",18),("B","T",15)]
canh_B = [("S","A",7),("S","B",5),("A","D",8),("B","D",6),("D","T",9),("A","T",16),("B","T",18)]
print("Khoang cach ngan nhat cua A la", ngan_nhat(canh_A), "(so dinh:", 5, ")")
print("Khoang cach ngan nhat cua B la", ngan_nhat(canh_B), "(so dinh:", 5, ")")
