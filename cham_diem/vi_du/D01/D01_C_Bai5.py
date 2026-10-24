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
