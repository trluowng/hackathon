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


# Bai 3 - Thanh vien B: tu xuat hien nhieu nhat trong chuoi
text = "code, AI, CODE, STEM, Code, ROBOT, code, DATA, CODE"

dem = {}
for tu in text.split(","):
    tu = tu.strip().upper()
    if tu:
        dem[tu] = dem.get(tu, 0) + 1

tu_nhieu = max(dem, key=dem.get)
B = dem[tu_nhieu]
print(tu_nhieu, B)
print("B =", B)


# Bai 3 - Thanh vien C: cau lac bo co nhieu ban ghi nhat
records = [
    ("DSC", 2024), ("STEM", 2024),
    ("DSC", 2025), ("ROBOT", 2025),
    ("DSC", 2026), ("AI", 2026),
    ("DSC", 2026), ("DSC", 2027)
]

dem = {}
for clb, nam in records:
    dem[clb] = dem.get(clb, 0) + 1

clb_nhieu = max(dem, key=dem.get)
C = dem[clb_nhieu]
print(clb_nhieu, C)
print("C =", C)
