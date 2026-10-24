# Hidden - Thanh vien C: doc theo cot, tu duoi len
grid = ["OA",
        "UX",
        "VN"]

ky_tu = []
for cot in range(len(grid[0])):
    for hang in range(len(grid) - 1, -1, -1):
        ky_tu.append(grid[hang][cot])
MANH_C = "".join(ky_tu)
print("MANH_C =", MANH_C)
