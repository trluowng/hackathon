year = 1956
n = year
A = 0
while n > 0:
    A += n % 10
    n //= 10
print("A =", A)
