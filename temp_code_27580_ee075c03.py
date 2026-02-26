n = int(input())
arr = list(map(int, input().split()))

largest = float('-inf')
second_largest = float('-inf')

for x in arr:
    if x > largest:
        second_largest = largest
        largest = x
    elif largest > x > second_largest:
        second_largest = x

if second_largest == float('-inf'):
    print(-1)
else:
    print(second_largest)