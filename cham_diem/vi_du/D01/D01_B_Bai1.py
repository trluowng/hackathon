# Bai 1 - Thanh vien B: dem so chan trong doan [1, n]
n = 28

B = 0
for x in range(1, n + 1):
    if x % 2 == 0:
        B += 1
print("B =", B)
