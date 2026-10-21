# Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình"
# Bài 3. Nhịp sống UNETI - Đội MAU
# Yêu cầu chung: không dùng collections.Counter, tự xây dựng bảng tần suất bằng dict.

# ----- Thành viên A: hoạt động xuất hiện nhiều nhất (chuẩn hóa chữ in hoa) -----
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
print("Hoạt động nhiều nhất:", pho_bien)
print("A =", A)

# ----- Thành viên B: từ xuất hiện nhiều nhất (tách theo dấu phẩy, bỏ khoảng trắng) -----
text = "UNETI, Data, data, AI, DATA, STEM, data, ROBOT, DATA"
tan_suat = {}
for tu in text.split(","):
    tu = tu.strip().upper()
    if tu:
        tan_suat[tu] = tan_suat.get(tu, 0) + 1
pho_bien, B = None, 0
for tu, so_lan in tan_suat.items():
    if so_lan > B:
        pho_bien, B = tu, so_lan
print("Từ nhiều nhất:", pho_bien)
print("B =", B)

# ----- Thành viên C: CLB có nhiều bản ghi nhất (chỉ dùng tên CLB) -----
records = [
    ("DSC", 2024), ("STEM", 2024), ("DSC", 2025),
    ("AC", 2025), ("DSC", 2026), ("BOOK", 2026),
    ("DSC", 2026), ("STEM", 2026), ("DSC", 2026)
]
tan_suat = {}
for clb, nam in records:
    tan_suat[clb] = tan_suat.get(clb, 0) + 1
pho_bien, C = None, 0
for clb, so_lan in tan_suat.items():
    if so_lan > C:
        pho_bien, C = clb, so_lan
print("CLB nhiều nhất:", pho_bien)
print("C =", C)

# ----- Checkpoint 3: ba kết quả đúng thì A = B = C = K3 -----
if A == B == C:
    K3 = A
    print("K3 =", K3, "->", chr(ord("A") + K3 - 1))
else:
    print("Chưa khớp: A, B, C =", A, B, C, "- kiểm tra lại")
