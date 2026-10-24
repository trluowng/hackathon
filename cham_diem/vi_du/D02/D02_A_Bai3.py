# Bai 3 - Thanh vien A: hoat dong pho bien nhat (tu dem bang dict)
events = [
    "AI", "STEM", "ai", "DATA",
    "Ai", "ROBOT", "AI", "ai"
]

dem = {}
for e in events:
    ten = e.strip().upper()
    dem[ten] = dem.get(ten, 0) + 1

ten_nhieu = None
for ten in dem:
    if ten_nhieu is None or dem[ten] > dem[ten_nhieu]:
        ten_nhieu = ten
A = dem[ten_nhieu]
print(ten_nhieu, A)
print("A =", A)
