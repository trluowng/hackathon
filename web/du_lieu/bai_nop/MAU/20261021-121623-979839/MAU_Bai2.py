# Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình"
# Bài 2. Những con số dấu ấn - Đội MAU
# Yêu cầu chung: không dùng sort()/sorted(), tự duyệt danh sách.

# ----- Thành viên A: lớn nhất - nhỏ nhất -----
data = [5, 19, 8, 13, 7]
lon_nhat = nho_nhat = data[0]
for x in data:
    if x > lon_nhat:
        lon_nhat = x
    if x < nho_nhat:
        nho_nhat = x
A = lon_nhat - nho_nhat
print("A =", A)

# ----- Thành viên B: lớn thứ hai - nhỏ thứ hai (không sửa danh sách gốc) -----
data = [1, 2, 5, 16, 19]
lon1 = lon2 = None    # lớn nhất, lớn thứ hai
nho1 = nho2 = None    # nhỏ nhất, nhỏ thứ hai
for x in data:
    if lon1 is None or x > lon1:
        lon1, lon2 = x, lon1
    elif x != lon1 and (lon2 is None or x > lon2):
        lon2 = x
    if nho1 is None or x < nho1:
        nho1, nho2 = x, nho1
    elif x != nho1 and (nho2 is None or x < nho2):
        nho2 = x
B = lon2 - nho2
print("B =", B)

# ----- Thành viên C: tổng vị trí chẵn - tổng vị trí lẻ (đánh số từ 0) -----
data = [9, 1, 7, 1]
tong_chan = tong_le = 0
for i in range(len(data)):
    if i % 2 == 0:
        tong_chan += data[i]
    else:
        tong_le += data[i]
C = tong_chan - tong_le
print("C =", C)

# ----- Checkpoint 2: ba kết quả đúng thì A = B = C = K2 -----
if A == B == C:
    K2 = A
    print("K2 =", K2, "->", chr(ord("A") + K2 - 1))
else:
    print("Chưa khớp: A, B, C =", A, B, C, "- kiểm tra lại")
