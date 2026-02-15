# Write your solution here
# Example solution:
n = list(map(int, input().split()))
x = len(n)
y= set(n)
m = []
for i in range(1, x + 1):
    if i not in y:
        m.append(i)
print(' '.join(map(str, m)))