import sys

data = sys.stdin.read().strip().split()

n = int(data[0])
arr = list(map(int, data[1:n+1]))

if n < 2:
    print(-1)
else:
    first = float('-inf')
    second = float('-inf')

    for num in arr:
        if num > first:
            second = first
            first = num
        elif num > second and num != first:
            second = num

    if second == float('-inf'):
        print(-1)
    else:
        print(second)
