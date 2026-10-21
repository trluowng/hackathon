"""Olympic AI UNETI 2026 - Vòng 1 "UNETI 70: Giải mã hành trình" - Bài 2 (Những con số dấu ấn) - Thành viên B"""
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
