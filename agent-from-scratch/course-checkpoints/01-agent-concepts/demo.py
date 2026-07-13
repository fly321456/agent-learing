steps = [
    ("THINK", "I need a calculation"),
    ("ACT", "calculator(6 * 7)"),
    ("OBSERVE", "42"),
    ("FINISH", "answer=42"),
]

for phase, detail in steps:
    print(f"{phase} -> {detail}")

