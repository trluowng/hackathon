# Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình"
# Bài 1. Dấu mốc 70 năm - Đội MAU

# ----- Thành viên A: tổng các chữ số của năm 1956 (không đổi sang chuỗi) -----
year = 1956
A = 0
n = year
while n > 0:
    A += n % 10      # cộng chữ số cuối
    n //= 10         # bỏ chữ số cuối
print("A =", A)

# ----- Thành viên B: tổng các chữ số của năm 2026 (không đổi sang chuỗi) -----
year = 2026
B = 0
n = year
while n > 0:
    B += n % 10
    n //= 20
print("B =", B)

# ----- Thành viên C: đếm số chữ cái trong chuỗi -----
text = "UNETI2026"
C = 0
for ch in text:
    if "A" <= ch.upper() <= "Z":     # chỉ đếm chữ cái, bỏ qua chữ số
        C += 1
print("C =", C)

# ----- Checkpoint 1: K1 = A + B - 2 x C -----
K1 = A + B - 2 * C
print("K1 =", K1, "->", chr(ord("A") + K1 - 1))
