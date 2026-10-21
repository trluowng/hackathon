records = [
    ("DSC", 2024), ("STEM", 2024), ("DSC", 2025),
    ("AC", 2025), ("DSC", 2026), ("BOOK", 2026),
    ("DSC", 2026), ("STEM", 2026), ("DSC", 2026)
]
tan_suat = {}
for clb, nam in records:
    tan_suat[clb] = tan_suat.get(clb, 0) + 1
C = max(tan_suat.values())
print("C =", C)
