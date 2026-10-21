data = [9, 1, 7, 1]
tong_chan = 0
tong_le = 0
for i in range(len(data)):
    if i % 2 == 0:
        tong_chan += data[i]
    else:
        tong_le += data[i]
C = tong_chan - tong_le
print("C =", C)
