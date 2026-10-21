import math

train = [(1, 7, 4), (2, 8, 4), (7, 2, 9), (8, 3, 9), (7, 4, 9)]
P = (6, 3)
k = 3

kc = []
for x, y, nhan in train:
    kc.append((math.sqrt((x - P[0]) ** 2 + (y - P[1]) ** 2), nhan))
kc.sort(key=lambda t: t[0])
phieu = {}
for d, nhan in kc[:k]:
    phieu[nhan] = phieu.get(nhan, 0) + 1
B = max(phieu, key=phieu.get)
print("B =", B)
