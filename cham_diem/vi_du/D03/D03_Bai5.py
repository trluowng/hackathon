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


# Bai 5 - Thanh vien C: KNN k = 1, Manhattan (diem va nhan de rieng)
diem = [(3, 5), (5, 6), (1, 2), (6, 9)]
nhan = [9, 3, 7, 4]
P = (3, 6)

gan_nhat = 0
for i in range(1, len(diem)):
    d_i = abs(diem[i][0] - P[0]) + abs(diem[i][1] - P[1])
    d_min = abs(diem[gan_nhat][0] - P[0]) + abs(diem[gan_nhat][1] - P[1])
    if d_i < d_min:
        gan_nhat = i
C = nhan[gan_nhat]
print("C =", C)
