import math
X = [(1, 1), (2, 2), (2, 3), (8, 8), (9, 9)]
y = [9, 9, 9, 3, 3]
px, py = 3, 3
k = 3
kc = []
for i in range(len(X)):
    d = math.sqrt((X[i][0] - px) ** 2 + (X[i][1] - py) ** 2)
    kc.append((d, y[i]))
kc.sort()
phieu = {}
for d, nhan in kc[:k]:
    phieu[nhan] = phieu.get(nhan, 0) + 1
A = max(phieu, key=phieu.get)
print("A =", A)
