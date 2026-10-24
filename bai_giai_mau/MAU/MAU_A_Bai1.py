# Bai 1 - Thanh vien A: tong cac chu so cua n (khong chuyen n thanh chuoi)
n = 4728

A = 0
so = n
while so > 0:
    A += so % 10
    so //= 10
print("A =", A)
