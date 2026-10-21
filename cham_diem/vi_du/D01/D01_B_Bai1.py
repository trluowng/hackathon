year = 2026
n = year
B = 0
while n > 0:
    B += n % 10
    n //= 10
print("B =", B)
