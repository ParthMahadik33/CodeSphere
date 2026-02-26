arr = list(map(int, input().split()))
n = len(arr)


for i in range(n):
    idx = abs(arr[i]) - 1
    if arr[idx] > 0:
        arr[idx] = -arr[idx]


missing = []
for i in range(n):
    if arr[i] > 0:
        missing.append(i + 1)

print(*missing)