arr = list(map(int, input().split()))
n = len(arr)

# Marking technique
for i in range(n):
    idx = abs(arr[i]) - 1
    if arr[idx] > 0:
        arr[idx] = -arr[idx]

# Missing numbers are the ones with positive values
missing = []
for i in range(n):
    if arr[i] > 0:
        missing.append(i + 1)

print(*missing)