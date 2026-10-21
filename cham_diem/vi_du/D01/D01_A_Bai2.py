data = [5, 19, 8, 13, 7]
lon_nhat = data[0]
nho_nhat = data[0]
for x in data:
    if x > lon_nhat:
        lon_nhat = x
    if x < nho_nhat:
        nho_nhat = x
A = lon_nhat - nho_nhat
print("A =", A)
