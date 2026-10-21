"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 1 (Dấu mốc 70 năm) - Thành viên C"""
text = "UNETI2026"
C = 0
for ch in text:
    if "A" <= ch.upper() <= "Z":   # chỉ đếm chữ cái, bỏ qua chữ số
        C += 1
print("C =", C)
