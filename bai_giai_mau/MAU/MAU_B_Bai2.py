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
