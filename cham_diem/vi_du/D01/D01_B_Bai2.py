data = [1, 2, 5, 16, 19]
lon1 = lon2 = None
nho1 = nho2 = None
for x in data:
    if lon1 is None or x > lon1:
        lon2 = lon1
        lon1 = x
    elif x != lon1 and (lon2 is None or x > lon2):
        lon2 = x
    if nho1 is None or x < nho1:
        nho2 = nho1
        nho1 = x
    elif x != nho1 and (nho2 is None or x < nho2):
        nho2 = x
B = lon2 - nho2
print("B =", B)
