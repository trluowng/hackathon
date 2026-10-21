from collections import Counter
activities = ["AI", "data", "AI", "ROBOT", "ai", "DATA", "Ai", "STEM", "AI"]
dem = Counter(a.upper() for a in activities)
ten, A = dem.most_common(1)[0]
print("A =", A)
