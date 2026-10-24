"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 3 (Nhịp sống UNETI) - Thành viên C"""
records = [
    ("DSC", 2024), ("STEM", 2024), ("DSC", 2025),
    ("AC", 2025), ("DSC", 2026), ("BOOK", 2026),
    ("DSC", 2026), ("STEM", 2026), ("DSC", 2026)
]
tan_suat = {}
for clb, nam in records:      # chỉ dùng tên CLB
    tan_suat[clb] = tan_suat.get(clb, 0) + 1
pho_bien, C = None, 0
for ten, so_lan in tan_suat.items():
    if so_lan > C:
        pho_bien, C = ten, so_lan
print("Xuất hiện nhiều nhất:", pho_bien)
print("C =", C)
