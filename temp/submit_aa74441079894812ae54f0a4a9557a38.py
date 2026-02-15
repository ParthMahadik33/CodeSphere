# Write your solution here
# Example solution:
nums = list(map(int, input().split()))
length = len(nums)
present = set(nums)
missing = []
for i in range(1, length + 1):
    if i not in present:
        missing.append(i)
print(' '.join(map(str, missing)))