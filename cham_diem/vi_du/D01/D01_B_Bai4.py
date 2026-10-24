# Bai 4 - Thanh vien B: liet ke cac duong di don tu S den T, lay tong nho nhat
du_lieu = """
S A 8
S B 4
A D 7
B D 6
D T 10
A T 20
B T 19
"""

ke = {}
for dong in du_lieu.strip().splitlines():
    u, v, w = dong.split()
    ke.setdefault(u, []).append((v, int(w)))
    ke.setdefault(v, []).append((u, int(w)))

tot_nhat = None


def di(u, da_qua, tong):
    global tot_nhat
    if u == "T":
        if tot_nhat is None or tong < tot_nhat:
            tot_nhat = tong
        return
    for v, w in ke[u]:
        if v not in da_qua:
            di(v, da_qua | {v}, tong + w)


di("S", {"S"}, 0)
B = tot_nhat
print("B =", B)
