activities = [
    "AI", "data", "AI", "ROBOT", "ai",
    "DATA", "Ai", "STEM", "AI"
]
tan_suat = {}
for act in activities:
    key = act.upper()
    tan_suat[key] = tan_suat.get(key, 0) + 1
A = 0
for key in tan_suat:
    if tan_suat[key] > A:
        A = tan_suat[key]
print("A =", A)
