"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 3 (Nhịp sống UNETI) - Thành viên A"""
activities = [
    "AI", "data", "AI", "ROBOT", "ai",
    "DATA", "Ai", "STEM", "AI"
]
tan_suat = {}
for hoat_dong in activities:
    ten = hoat_dong.upper()
    tan_suat[ten] = tan_suat.get(ten, 0) + 1
pho_bien, A = None, 0
for ten, so_lan in tan_suat.items():
    if so_lan > A:
        pho_bien, A = ten, so_lan
print("Xuất hiện nhiều nhất:", pho_bien)
print("A =", A)
