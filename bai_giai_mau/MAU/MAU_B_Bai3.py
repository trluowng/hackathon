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
