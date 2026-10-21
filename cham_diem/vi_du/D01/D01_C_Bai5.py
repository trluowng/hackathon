import math

train = [(2, 1, 9), (3, 2, 9), (4, 2, 9), (8, 7, 6), (9, 8, 6)]
P = (4, 3)
k = 3

kc = []
for x, y, nhan in train:
    kc.append((math.sqrt((x - P[0]) ** 2 + (y - P[1]) ** 2), nhan))
kc.sort(key=lambda t: t[0])
phieu = {}
for d, nhan in kc[:k]:
    phieu[nhan] = phieu.get(nhan, 0) + 1
C = max(phieu, key=phieu.get)
print("C =", C)
