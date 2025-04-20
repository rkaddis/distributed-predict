

def max_subarray(arr : dict) -> tuple[int,int]:
    """
    Takes in a dict with integer values, and returns starting and ending index of the maximum subarray (subdict?)
    Uses Kadane's algorithm, https://en.wikipedia.org/wiki/Maximum_subarray_problem
    """

    curr_sum = 0
    curr_start = 0
    curr_end = 0
    best_sum = float("-inf")
    best_start = 0
    best_end = 0
    for x in arr.keys():
        if arr[x] > curr_sum + arr[x]:
            curr_start = x
            curr_end = x
            curr_sum = arr[x]
        else:
            curr_sum = curr_sum + arr[x]
            curr_end = x

        if curr_sum > best_sum:
            best_sum = curr_sum
            best_start = curr_start
            best_end = curr_end
        
    return (best_start, best_end)