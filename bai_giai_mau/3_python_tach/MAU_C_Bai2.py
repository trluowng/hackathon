"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 2 (Những con số dấu ấn) - Thành viên C"""
data = [9, 1, 7, 1]
tong_chan = tong_le = 0
for i in range(len(data)):
    if i % 2 == 0:
        tong_chan += data[i]
    else:
        tong_le += data[i]
C = tong_chan - tong_le
print("C =", C)
