# ===== BAI 1 - DAU MOC 70 NAM =====

# --- Thanh vien A ---
year = 1956
n = year
A = 0
while n > 0:
    A += n % 10
    n //= 10
print("A =", A)

# --- Thanh vien B ---
year = 2026
n = year
B = 0
while n > 0:
    B += n % 10
    n //= 10
print("B =", B)

# --- Thanh vien C ---
text = "UNETI2026"
C = 0
for ch in text:
    if ch.isalpha():
        C += 1
print("C =", C)

K1 = A + B - 2 * C
print("K1 =", K1, "->", chr(64 + K1))
