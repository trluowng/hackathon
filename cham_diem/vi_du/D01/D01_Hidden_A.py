# Hidden - Thanh vien A: ma tran zich zac
grid = [['U', 'N', '#'],
        ['I', 'T', 'E']]

ky_tu = []
for i in range(len(grid)):
    hang = grid[i] if i % 2 == 0 else grid[i][::-1]
    for ch in hang:
        if ch != '#':
            ky_tu.append(ch)
MANH_A = "".join(ky_tu)
print("MANH_A =", MANH_A)
