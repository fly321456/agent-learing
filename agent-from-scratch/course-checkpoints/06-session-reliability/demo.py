messages = [
    {"role": "user", "content": "old context"},
    {"role": "user", "content": "new task"},
]
print(f"session_messages={len(messages)}")
context = messages[-1:]
print(f"context_trimmed={str(len(context) < len(messages)).lower()}")

attempts = 0
while attempts < 2:
    attempts += 1
    if attempts == 1:
        continue
    recovered = True
    break
print(f"attempts={attempts} recovered={str(recovered).lower()}")
print("checkpoint_next_step=2 resumed=true")

