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
