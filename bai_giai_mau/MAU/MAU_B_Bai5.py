# Bai 5 - Thanh vien B: KNN k = 1, Manhattan
def du_doan(train, P):
    """KNN k = 1, khoang cach Manhattan."""
    nhan_gan_nhat = None
    kc_nho_nhat = None
    for x, y, nhan in train:
        d = abs(x - P[0]) + abs(y - P[1])
        if kc_nho_nhat is None or d < kc_nho_nhat:
            kc_nho_nhat = d
            nhan_gan_nhat = nhan
    return nhan_gan_nhat


train = [(6, 4, 9), (3, 3, 5), (8, 7, 2), (9, 9, 6)]
P = (6, 5)
B = du_doan(train, P)
print("B =", B)
