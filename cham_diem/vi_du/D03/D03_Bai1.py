# Bai 1 - Thanh vien A: tong cac chu so cua n (khong chuyen n thanh chuoi)
n = 4728

A = 0
so = n
while so > 0:
    A += so % 10
    so //= 10
print("A =", A)


# Bai 1 - Thanh vien B: dem so chan trong doan [1, n]
n = 28

B = 0
for x in range(1, n + 1):
    if x % 2 == 0:
        B += 1
print("B =", B)


# Bai 1 - Thanh vien C: dem chu cai tieng Anh trong chuoi
text = "UNETI70AI"

C = 0
for ch in text:
    if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
        C += 1
print("C =", C)
