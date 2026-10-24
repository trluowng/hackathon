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


# Bai 2 - Thanh vien B: lon thu hai - nho thu hai (phan biet), khong sua danh sach goc
data = [4, 10, 19, 18, 2]

lon1 = lon2 = None
nho1 = nho2 = None
for x in data:
    if lon1 is None or x > lon1:
        lon1, lon2 = x, lon1
    elif x != lon1 and (lon2 is None or x > lon2):
        lon2 = x
    if nho1 is None or x < nho1:
        nho1, nho2 = x, nho1
    elif x != nho1 and (nho2 is None or x < nho2):
        nho2 = x
B = lon2 - nho2
print("B =", B)


# Bai 2 - Thanh vien C: tong vi tri chan - tong vi tri le
data = [10, 1, 6, 1]

tong_chan = 0
tong_le = 0
for i in range(len(data)):
    if i % 2 == 0:
        tong_chan += data[i]
    else:
        tong_le += data[i]
C = tong_chan - tong_le
print("C =", C)
