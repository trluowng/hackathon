"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 3 (Nhịp sống UNETI) - Thành viên B"""
text = "UNETI, Data, data, AI, DATA, STEM, data, ROBOT, DATA"
tan_suat = {}
for tu in text.split(","):
    tu = tu.strip().upper()
    if tu:
        tan_suat[tu] = tan_suat.get(tu, 0) + 1
pho_bien, B = None, 0
for ten, so_lan in tan_suat.items():
    if so_lan > B:
        pho_bien, B = ten, so_lan
print("Xuất hiện nhiều nhất:", pho_bien)
print("B =", B)
