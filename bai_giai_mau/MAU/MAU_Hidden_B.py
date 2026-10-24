# Hidden - Thanh vien B: khoi phuc thu tu
data = [(4, 'A'), (1, '7'), (5, 'M'), (3, 'N'), (2, '0')]

data_sap_xep = sorted(data, key=lambda cap: cap[0])
MANH_B = "".join(ch for vi_tri, ch in data_sap_xep)
print("MANH_B =", MANH_B)
