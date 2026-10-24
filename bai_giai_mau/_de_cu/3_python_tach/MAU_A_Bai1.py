"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 1 (Dấu mốc 70 năm) - Thành viên A"""
year = 1956
A = 0
n = year
while n > 0:
    A += n % 10     # cộng chữ số cuối
    n //= 10          # bỏ chữ số cuối
print("A =", A)
