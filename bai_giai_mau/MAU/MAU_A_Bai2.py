# Bai 2 - Thanh vien A: lon nhat - nho nhat (khong dung sort, max, min)
data = [8, 11, 15, 22, 10]

lon = nho = data[0]
for x in data:
    if x > lon:
        lon = x
    if x < nho:
        nho = x
A = lon - nho
print("A =", A)
