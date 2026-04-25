# =============================================================================
# sorting.py
# -----------------------------------------------------------------------------
# PURPOSE:
#   Sorting algorithms used by the Emergency Analytics page.
#   Given a list of ambulances or hospitals, sort them by distance/ETA
#   so the system can dispatch the nearest one.
#
# WHY CUSTOM SORTING?
#   Python's built-in sort (Timsort) is great for production, but this is a
#   DAA course project — we implement from scratch to demonstrate the
#   underlying algorithmic principles and compare complexities.
#
# ALGORITHMS IN THIS FILE:
#   1. Merge Sort   — O(n log n) always     — Divide & Conquer, stable
#   2. Quick Sort   — O(n log n) average    — Divide & Conquer, in-place
#   3. Insertion Sort — O(n²) worst case    — included for comparison only
#
# REAL USE IN THIS PROJECT:
#   Ambulance dispatch: sort available ambulances by their Dijkstra distance
#   to the patient → dispatch the closest one (Quick Sort used here).
#
#   Hospital selection: sort all hospitals by their Dijkstra distance from
#   patient → route to the nearest one (Merge Sort used here).
#
#   Emergency Analytics page: sort emergency records by response_time, date,
#   severity using both algorithms and compare their timing side-by-side.
#
# DIVIDE & CONQUER (CLO 6):
#   Both Merge Sort and Quick Sort are canonical Divide & Conquer algorithms.
#   They split the problem into sub-problems, solve them recursively, then
#   combine.  Recurrence relation: T(n) = 2T(n/2) + O(n)  → O(n log n)
#   by the Master Theorem.
# =============================================================================

import time     # for benchmarking execution time
import random   # for Quick Sort random pivot selection


# =============================================================================
# 1. MERGE SORT
# =============================================================================
# Invented by: John von Neumann, 1945.
#
# Core idea (Divide & Conquer):
#   DIVIDE:   Split the array in half.
#   CONQUER:  Recursively sort each half.
#   COMBINE:  Merge the two sorted halves into one sorted array.
#
# Recurrence: T(n) = 2T(n/2) + O(n)
#   By Master Theorem (Case 2): T(n) = O(n log n)
#   - 2T(n/2): two recursive calls on halves
#   - O(n):    merge step scans both halves once
#
# Why STABLE?
#   During the merge step, when two elements are equal we always pick from
#   the LEFT half first → equal elements maintain their original relative order.
#   Stability matters when sorting by one key then another (e.g., sort by
#   name, then by distance — names with equal distances keep alphabetical order).
#
# Trade-off vs Quick Sort:
#   ✓ Always O(n log n) — no worst case
#   ✓ Stable sort
#   ✗ Requires O(n) extra space for the merge buffer
#
# Time:   O(n log n)  best, average, AND worst case
# Space:  O(n)        for auxiliary arrays during merge
#
# Used in this project:
#   Sort hospitals by distance from patient before routing.
#   Emergency Analytics page — compared with Quick Sort.
# =============================================================================

def merge_sort(arr, key=lambda x: x):
    """
    Sort a list using Merge Sort (stable, Divide & Conquer).

    Parameters
    ----------
    arr : list  — list of any objects
    key : callable  — function to extract the sort key from each element
                      e.g., key=lambda h: h["distance"]

    Returns
    -------
    list  — new sorted list (does NOT modify original)
    int   — comparison count (for stats panel)
    """
    comparisons = [0]   # list so inner functions can mutate it (closure trick)

    def _merge_sort(a):
        """Recursive divide-and-conquer core."""

        # BASE CASE: a list of 0 or 1 elements is already sorted.
        # This is what terminates the recursion.
        if len(a) <= 1:
            return a

        # DIVIDE: find the midpoint and split
        mid = len(a) // 2
        left  = _merge_sort(a[:mid])    # sort left half recursively
        right = _merge_sort(a[mid:])    # sort right half recursively

        # COMBINE: merge two sorted halves
        return _merge(left, right)

    def _merge(left, right):
        """
        Merge two sorted lists into one sorted list.
        This is the O(n) "combine" step of Merge Sort.
        """
        result = []
        i = j = 0

        # Compare front elements of left and right; take the smaller one
        while i < len(left) and j < len(right):
            comparisons[0] += 1
            if key(left[i]) <= key(right[j]):
                result.append(left[i])  # take from left (stable: left wins on tie)
                i += 1
            else:
                result.append(right[j])
                j += 1

        # Append remaining elements (one side will be exhausted first)
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    sorted_arr = _merge_sort(list(arr))   # copy input — don't mutate original
    return sorted_arr, comparisons[0]


# =============================================================================
# 2. QUICK SORT
# =============================================================================
# Invented by: Tony Hoare, 1959.
#
# Core idea (Divide & Conquer):
#   DIVIDE:   Choose a PIVOT element.  Partition the array so that all
#             elements < pivot come before it, and all > pivot come after.
#             The pivot is now in its FINAL sorted position.
#   CONQUER:  Recursively sort the sub-array left of pivot and right of pivot.
#   COMBINE:  Nothing to do — the array is sorted in place!
#
# Recurrence (average case):
#   T(n) = 2T(n/2) + O(n)  → O(n log n)   (pivot splits array roughly in half)
#
# Worst case: O(n²) when pivot is always the smallest or largest element.
#   Example: sorted input with last-element pivot → n² comparisons.
#   FIX: Use RANDOM pivot (randomised Quick Sort) → O(n log n) expected.
#
# Why FASTER than Merge Sort in practice?
#   In-place partitioning → better cache performance (data stays nearby in memory).
#   Smaller constant factor despite same Big-O.
#   Python's built-in sort (Timsort) uses Quick Sort ideas internally.
#
# Trade-offs vs Merge Sort:
#   ✓ In-place: O(log n) space (recursion stack only)
#   ✓ Faster in practice (better cache behavior)
#   ✗ NOT stable (equal elements may swap)
#   ✗ O(n²) worst case (mitigated by random pivot)
#
# Time:   O(n log n) average,  O(n²) worst case (very rare with random pivot)
# Space:  O(log n)  — recursion stack depth
#
# Used in this project:
#   Sort ambulances by distance from patient before dispatch.
#   Emergency Analytics page — compared with Merge Sort.
# =============================================================================

def quick_sort(arr, key=lambda x: x):
    """
    Sort a list using Quick Sort (Divide & Conquer, randomised pivot).

    Parameters
    ----------
    arr : list      — list of any objects (NOT modified in place; a copy is made)
    key : callable  — sort key function

    Returns
    -------
    list  — new sorted list
    int   — comparison count
    """
    comparisons = [0]

    def _quick_sort(a, low, high):
        """
        Recursive Quick Sort on subarray a[low..high] (inclusive).
        """
        if low >= high:
            return  # BASE CASE: 0 or 1 elements — already sorted

        # PARTITION step — returns final position of pivot
        pivot_index = _partition(a, low, high)

        # RECURSE on left and right of pivot
        _quick_sort(a, low, pivot_index - 1)
        _quick_sort(a, pivot_index + 1, high)

    def _partition(a, low, high):
        """
        Lomuto partition scheme with random pivot.

        1. Pick a random pivot (avoids O(n²) on sorted input).
        2. Move pivot to the end temporarily.
        3. Scan left-to-right; move elements smaller than pivot to the front.
        4. Place pivot in its correct final position.

        Returns the final index of the pivot.
        """
        # RANDOM PIVOT: swap a random element into the last position
        rand_idx = random.randint(low, high)
        a[rand_idx], a[high] = a[high], a[rand_idx]

        pivot = a[high]         # pivot is now at the end
        i = low - 1             # i = last index of the "smaller than pivot" region

        for j in range(low, high):
            comparisons[0] += 1
            if key(a[j]) <= key(pivot):
                # a[j] belongs in the "≤ pivot" region → extend it
                i += 1
                a[i], a[j] = a[j], a[i]

        # Place pivot in its final sorted position (right after "≤ pivot" region)
        a[i + 1], a[high] = a[high], a[i + 1]
        return i + 1    # return pivot's final index

    arr_copy = list(arr)    # don't mutate the original
    _quick_sort(arr_copy, 0, len(arr_copy) - 1)
    return arr_copy, comparisons[0]


# =============================================================================
# 3. INSERTION SORT  (included for comparison — used on small lists)
# =============================================================================
# Core idea: like sorting a hand of playing cards.
#   Pick each card and insert it into the correct position among already-sorted cards.
#
# Time:  O(n²) worst/average case,  O(n) best case (already sorted)
# Space: O(1)  — truly in-place
#
# When to use: very small arrays (n < 10-20) where overhead of recursion makes
#   Merge/Quick Sort slower.  Also the basis of Timsort (Python's built-in).
#
# Included here to demonstrate why O(n²) is "bad" on large inputs — the
# Emergency Analytics page can show it taking much longer than Merge/Quick Sort.
# =============================================================================

def insertion_sort(arr, key=lambda x: x):
    """
    Sort using Insertion Sort — O(n²) worst case. Shown for comparison.
    """
    comparisons = 0
    arr_copy = list(arr)

    for i in range(1, len(arr_copy)):
        current = arr_copy[i]
        j = i - 1

        # Shift elements right until we find the insertion position
        while j >= 0 and key(arr_copy[j]) > key(current):
            comparisons += 1
            arr_copy[j + 1] = arr_copy[j]
            j -= 1

        if j >= 0:
            comparisons += 1    # count the final comparison that stopped the loop

        arr_copy[j + 1] = current

    return arr_copy, comparisons


# =============================================================================
# BENCHMARK HELPER
# =============================================================================
# Runs both algorithms on the same data and returns timing + comparison stats.
# Used by the Emergency Analytics page API endpoint.
# =============================================================================

def benchmark_sort(data, key=lambda x: x):
    """
    Run Merge Sort and Quick Sort on the same data and return comparison stats.

    Parameters
    ----------
    data : list  — the unsorted list
    key  : callable  — sort key

    Returns
    -------
    dict with timing and comparison counts for each algorithm
    """
    results = {}

    for name, sort_fn in [("merge_sort", merge_sort), ("quick_sort", quick_sort)]:
        start_time = time.perf_counter()           # high-resolution timer
        sorted_arr, comparisons = sort_fn(data, key=key)
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        results[name] = {
            "sorted": sorted_arr,
            "comparisons": comparisons,
            "time_ms": round(elapsed_ms, 4),
            "n": len(data),
            "complexity_avg": "O(n log n)",
            "complexity_worst": "O(n log n)" if name == "merge_sort" else "O(n²)",
            "space": "O(n)" if name == "merge_sort" else "O(log n)",
            "stable": name == "merge_sort",
        }

    return results


# =============================================================================
# STANDALONE TEST  (run:  python sorting.py)
# =============================================================================

if __name__ == "__main__":
    import random as rnd

    # --- Basic correctness test ---
    test_data = [64, 25, 12, 22, 11, 90, 3, 77, 45, 18]
    print("=== Sorting Correctness Test ===")
    print(f"  Input:       {test_data}")

    ms_result, ms_cmp = merge_sort(test_data)
    qs_result, qs_cmp = quick_sort(test_data)
    is_result, is_cmp = insertion_sort(test_data)

    print(f"  Merge Sort:  {ms_result}  ({ms_cmp} comparisons)")
    print(f"  Quick Sort:  {qs_result}  ({qs_cmp} comparisons)")
    print(f"  Insert Sort: {is_result}  ({is_cmp} comparisons)")

    assert ms_result == sorted(test_data), "❌ Merge Sort wrong"
    assert qs_result == sorted(test_data), "❌ Quick Sort wrong"
    assert is_result == sorted(test_data), "❌ Insertion Sort wrong"
    print("  ✅ All correct")

    # --- Test with dict objects (like real DB records) ---
    print("\n=== Sorting hospital records by distance ===")
    hospitals = [
        {"id": 1, "name": "Services Hospital", "distance": 4.2},
        {"id": 2, "name": "Jinnah Hospital",   "distance": 2.1},
        {"id": 3, "name": "Mayo Hospital",     "distance": 5.8},
        {"id": 4, "name": "Shaukat Khanum",    "distance": 1.3},
        {"id": 5, "name": "Children's Hospital","distance": 3.7},
    ]

    sorted_hospitals, _ = merge_sort(hospitals, key=lambda h: h["distance"])
    for h in sorted_hospitals:
        print(f"  {h['distance']:.1f} km — {h['name']}")

    # --- Benchmark comparison ---
    print("\n=== Benchmark (n=500 random integers) ===")
    big_data = [rnd.randint(1, 10000) for _ in range(500)]
    bench = benchmark_sort(big_data)

    for alg, stats in bench.items():
        print(f"  {alg:12} — time: {stats['time_ms']:.3f}ms  "
              f"comparisons: {stats['comparisons']}  "
              f"stable: {stats['stable']}")
