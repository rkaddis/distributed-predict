

def max_subarray(arr : dict) -> tuple[int,int]:
    """
    Takes in a dict with integer values, and returns starting and ending index of the maximum subarray (subdict?)
    Uses Kadane's algorithm, https://en.wikipedia.org/wiki/Maximum_subarray_problem
    """

    current_sum = 0
    start_key = 0
    end_key = 0
    for x in arr.keys():
        if arr[x] > current_sum + arr[x]:
            start_key = x
            end_key = x
            current_sum = arr[x]
        else:
            current_sum = current_sum + arr[x]
            end_key = x
        
    return (start_key, end_key)