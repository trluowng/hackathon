# Bai 5 - Thanh vien A: KNN k = 1, Manhattan
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


train = [(4, 5, 9), (2, 2, 3), (7, 6, 2), (1, 8, 4)]
P = (4, 4)
A = du_doan(train, P)
print("A =", A)
