# Bai 1 - Thanh vien C: dem chu cai tieng Anh trong chuoi
text = "UNETI70AI"

C = 0
for ch in text:
    if ("A" <= ch <= "Z") or ("a" <= ch <= "z"):
        C += 1
print("C =", C)
