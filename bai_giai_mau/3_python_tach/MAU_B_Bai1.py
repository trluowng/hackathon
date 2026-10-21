"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 1 (Dấu mốc 70 năm) - Thành viên B"""
year = 2026
B = 0
n = year
while n > 0:
    B += n % 10     # cộng chữ số cuối
    n //= 10          # bỏ chữ số cuối
print("B =", B)
