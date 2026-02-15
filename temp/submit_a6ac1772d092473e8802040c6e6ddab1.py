# Write your solution here
# Example solution:
nums = list(map(int, input().split()))
n = len(nums)
present = set(nums)
missing = []
for i in range(1, n + 1):
    if i not in present:
        missing.append(i)
print(' '.join(map(str, missing)))