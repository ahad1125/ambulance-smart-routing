# =============================================================================
# string_matching.py
# -----------------------------------------------------------------------------
# PURPOSE:
#   String matching (pattern search) algorithms for the Hospital Search page.
#   Given a search query, find matching hospital names or patient records using
#   two different algorithms and compare their performance.
#
# ALGORITHMS IN THIS FILE:
#   1. KMP (Knuth-Morris-Pratt) — O(n + m)   — failure function / LPS array
#   2. Rabin-Karp               — O(n + m)   — rolling hash window
#   3. Naive (Brute Force)      — O(n · m)   — included for comparison
#
# WHY NOT JUST USE Python's 'in' OPERATOR?
#   Python's built-in string search is already optimised, but this is a DAA
#   project.  We implement from scratch to demonstrate the algorithms and
#   compare the number of character comparisons each approach makes.
#
# TERMINOLOGY:
#   text    : the string we're searching IN       (length n)
#   pattern : the string we're searching FOR      (length m)
#   match   : a position in 'text' where 'pattern' starts
#
# REAL USE IN THIS PROJECT:
#   Hospital Search page: user types a query → KMP and Rabin-Karp both
#   search through all hospital names, return matches + comparison counts.
#   The page shows which algorithm found the match with fewer comparisons.
# =============================================================================


# =============================================================================
# 1. NAIVE (BRUTE FORCE) STRING MATCHING
# =============================================================================
# Core idea:
#   Try every possible starting position in text.
#   At each position, compare pattern character by character.
#   If all characters match → found a match at this position.
#
# Why is it slow?
#   After a partial match fails, we DISCARD all information about characters
#   we've already compared and restart from the next position.
#   KMP and Rabin-Karp avoid this wasted work.
#
# Time complexity: O(n · m)
#   - n possible starting positions in text
#   - m character comparisons at each position in worst case
#   Worst case example: text = "AAAAAAB", pattern = "AAAB"
#   → nearly m comparisons at each of n positions
#
# Space complexity: O(1)
#
# Included for: the comparison page to show why O(nm) is worse than O(n+m).
# =============================================================================

def naive_search(text, pattern):
    """
    Find all occurrences of pattern in text using brute force.

    Returns
    -------
    dict with matches (start positions), comparisons, complexity
    """
    n, m = len(text), len(pattern)
    matches = []
    comparisons = 0

    # Try every possible starting position (0 to n-m inclusive)
    for i in range(n - m + 1):
        j = 0

        # Compare pattern to text starting at position i
        while j < m:
            comparisons += 1
            if text[i + j] != pattern[j]:
                break       # mismatch — stop comparing, try next position
            j += 1

        if j == m:
            matches.append(i)   # full match found at position i

    return {
        "matches": matches,
        "match_count": len(matches),
        "comparisons": comparisons,
        "complexity": "O(n · m)",
        "algorithm": "Naive (Brute Force)"
    }


# =============================================================================
# 2. KMP — KNUTH-MORRIS-PRATT
# =============================================================================
# History: Donald Knuth, James Morris, Vaughan Pratt, 1977.
#
# Core idea:
#   When a mismatch occurs at position j in the pattern, we DON'T restart
#   from scratch.  Instead, we use pre-computed information about the pattern
#   to SKIP ahead intelligently.
#
# The key insight — the LPS array (Longest Proper Prefix which is also Suffix):
#   lps[j] = length of the longest proper prefix of pattern[0..j] that is
#             also a suffix of pattern[0..j].
#
#   Example: pattern = "ABCAB"
#   lps[0] = 0  ("A" has no proper prefix-suffix)
#   lps[1] = 0  ("AB" — no proper prefix is also a suffix)
#   lps[2] = 0  ("ABC")
#   lps[3] = 1  ("ABCA" — prefix "A" = suffix "A" → length 1)
#   lps[4] = 2  ("ABCAB" — prefix "AB" = suffix "AB" → length 2)
#
# How lps is used during search:
#   If text[i] != pattern[j] (mismatch at position j in pattern):
#     Instead of resetting j to 0, set j = lps[j-1]
#     This skips the characters we KNOW already matched (the suffix that is
#     also a prefix) — we don't need to re-compare them.
#
# Why O(n + m)?
#   - Building lps[] scans pattern once: O(m)
#   - Searching scans text once (i never goes backward): O(n)
#   Total: O(n + m)
#
# Space: O(m)  — the lps array
#
# Used in this project:
#   Hospital search with exact/substring matching, patient record search.
# =============================================================================

def build_lps(pattern):
    """
    Build the LPS (Longest Proper Prefix which is also Suffix) array.
    This is the preprocessing step of KMP.  Takes O(m) time and O(m) space.

    lps[i] tells us: if a mismatch occurs right after matching pattern[0..i],
    we can immediately resume comparison at pattern[lps[i]] — skipping the
    re-comparison of the overlapping prefix.

    Example trace for pattern = "AABAA":
      i=0: lps[0] = 0  (single char, no proper prefix)
      i=1: pattern[1]='A' = pattern[0]='A' → lps[1] = 1
      i=2: pattern[2]='B' ≠ pattern[1]='A', pattern[2]≠pattern[0] → lps[2]=0
      i=3: pattern[3]='A' = pattern[0]='A' → lps[3] = 1
      i=4: pattern[4]='A' = pattern[1]='A' → lps[4] = 2
      lps = [0, 1, 0, 1, 2]
    """
    m = len(pattern)
    lps = [0] * m

    length = 0  # length of the previous longest prefix-suffix
    i = 1       # start from index 1 (lps[0] is always 0)

    while i < m:
        if pattern[i] == pattern[length]:
            # Characters match → extend the current prefix-suffix
            length += 1
            lps[i] = length
            i += 1
        else:
            if length != 0:
                # Mismatch after some matches.
                # Don't increment i — try shorter prefix-suffix (fall back)
                length = lps[length - 1]
                # Intuition: the last 'length' chars of lps[length-1] still match
            else:
                # No prefix-suffix of length > 0
                lps[i] = 0
                i += 1

    return lps


def kmp_search(text, pattern, case_sensitive=False):
    """
    Find all occurrences of pattern in text using KMP algorithm.

    Parameters
    ----------
    text           : str  — the full text to search (e.g., hospital name)
    pattern        : str  — the search query
    case_sensitive : bool — default False (for hospital name search)

    Returns
    -------
    dict with matches (start positions), comparisons, lps array, complexity
    """
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()

    n, m = len(text), len(pattern)

    if m == 0:
        return {"matches": [], "match_count": 0, "comparisons": 0,
                "lps": [], "complexity": "O(n + m)", "algorithm": "KMP"}

    # --- Preprocessing: build LPS array ---
    lps = build_lps(pattern)   # O(m) preprocessing

    matches = []
    comparisons = 0
    i = 0   # index into text
    j = 0   # index into pattern

    # --- Search phase ---
    while i < n:
        comparisons += 1

        if text[i] == pattern[j]:
            i += 1
            j += 1
        else:
            if j != 0:
                # Mismatch: use LPS to skip ahead (DON'T move i backward)
                j = lps[j - 1]
                # No comparisons[0] increment here — we're just resetting j
            else:
                # j == 0 and mismatch: pattern[0] ≠ text[i], just advance text
                i += 1

        if j == m:
            # Full match found: pattern ends at text[i-1], starts at i-m
            matches.append(i - m)
            j = lps[j - 1]     # look for next match (overlapping matches allowed)

    return {
        "matches": matches,
        "match_count": len(matches),
        "comparisons": comparisons,
        "lps": lps,
        "complexity": "O(n + m)",
        "algorithm": "KMP"
    }


# =============================================================================
# 3. RABIN-KARP
# =============================================================================
# History: Michael Rabin & Richard Karp, 1987.
#
# Core idea:
#   Instead of comparing characters one by one, compute a HASH of the pattern
#   and compare it to hashes of each window of text[i..i+m-1].
#   If hashes match, do a character-by-character verification.
#
# Rolling hash (the clever part):
#   Recomputing the hash from scratch for each window would be O(m) per
#   window → O(nm) total.  Instead, we use a ROLLING HASH:
#
#   hash(text[i+1..i+m]) = (hash(text[i..i+m-1])
#                           - text[i] * base^(m-1)) * base
#                           + text[i+m]
#
#   Sliding the window adds the new char and removes the old char in O(1).
#
# Why modulo?
#   hash values grow exponentially with m (base^m).
#   We take mod a large prime to keep numbers small.
#   This introduces HASH COLLISIONS — two different strings can have the
#   same hash.  We verify with actual comparison on collision.
#
# Spurious hits:
#   A hash match that turns out NOT to be a real match is a "spurious hit".
#   With a good prime and base, these are rare but always verified.
#
# Time complexity: O(n + m) average, O(n·m) worst case (all spurious hits)
# Space: O(1)  — no extra array needed (unlike KMP's lps)
#
# Best for: multiple pattern search (compute all pattern hashes once).
#           Here we use it for single pattern — primarily for comparison.
#
# Used in this project:
#   Hospital search — compared side-by-side with KMP on comparison count.
# =============================================================================

BASE = 256          # number of characters in alphabet (ASCII)
MOD = 101           # a prime number for modulo hashing
                    # (small prime is fine for demo; production uses 10^9+7)

def rabin_karp_search(text, pattern, case_sensitive=False):
    """
    Find all occurrences of pattern in text using Rabin-Karp.

    Parameters
    ----------
    text           : str
    pattern        : str
    case_sensitive : bool  — default False

    Returns
    -------
    dict with matches, comparisons, hash_comparisons, spurious_hits, complexity
    """
    if not case_sensitive:
        text = text.lower()
        pattern = pattern.lower()

    n, m = len(text), len(pattern)

    if m == 0 or m > n:
        return {"matches": [], "match_count": 0, "comparisons": 0,
                "hash_comparisons": 0, "spurious_hits": 0,
                "complexity": "O(n + m)", "algorithm": "Rabin-Karp"}

    # --- Precompute h = base^(m-1) mod MOD ---
    # This is used when removing the leading character from the rolling hash.
    # h = BASE^(m-1) % MOD
    h = 1
    for _ in range(m - 1):
        h = (h * BASE) % MOD

    # --- Compute initial hash values ---
    # Hash of pattern and first window of text
    pattern_hash = 0
    window_hash = 0

    for k in range(m):
        pattern_hash = (BASE * pattern_hash + ord(pattern[k])) % MOD
        window_hash  = (BASE * window_hash  + ord(text[k]))    % MOD

    matches = []
    hash_comparisons = 0    # number of times we compared hashes
    char_comparisons = 0    # number of character-level comparisons
    spurious_hits = 0       # hash matches that weren't real matches

    # --- Slide the window through text ---
    for i in range(n - m + 1):
        hash_comparisons += 1

        if pattern_hash == window_hash:
            # Hash match — verify character by character (could be spurious hit)
            match = True
            for k in range(m):
                char_comparisons += 1
                if text[i + k] != pattern[k]:
                    match = False
                    spurious_hits += 1
                    break

            if match:
                matches.append(i)

        # --- Compute rolling hash for next window ---
        # Remove leading char (text[i]), add new trailing char (text[i+m])
        if i < n - m:
            window_hash = (BASE * (window_hash - ord(text[i]) * h) + ord(text[i + m])) % MOD
            # Make hash positive (Python handles negative mod, but let's be explicit)
            if window_hash < 0:
                window_hash += MOD

    return {
        "matches": matches,
        "match_count": len(matches),
        "hash_comparisons": hash_comparisons,
        "char_comparisons": char_comparisons,
        "total_comparisons": hash_comparisons + char_comparisons,
        "spurious_hits": spurious_hits,
        "complexity": "O(n + m) average, O(n·m) worst case",
        "algorithm": "Rabin-Karp"
    }


# =============================================================================
# SEARCH HOSPITALS  —  main function called by the API view
# =============================================================================

def search_hospitals(hospitals, query):
    """
    Search a list of hospital objects for those whose name matches the query.
    Runs both KMP and Rabin-Karp, returns results from both for comparison.

    Parameters
    ----------
    hospitals : list of dicts  — e.g. [{"id":1, "name":"Services Hospital"}, ...]
    query     : str            — search term

    Returns
    -------
    dict with:
        kmp_results       — list of matching hospital dicts
        rk_results        — same (should be identical matches)
        kmp_stats         — comparison counts for KMP
        rk_stats          — comparison counts for Rabin-Karp
        comparison_table  — side-by-side stats for the comparison panel
    """
    kmp_matches = []
    rk_matches = []
    kmp_total_comparisons = 0
    rk_total_comparisons = 0

    for hospital in hospitals:
        name = hospital["name"]

        # Run KMP on this hospital name
        kmp_result = kmp_search(name, query)
        kmp_total_comparisons += kmp_result["comparisons"]
        if kmp_result["match_count"] > 0:
            kmp_matches.append({**hospital, "match_positions": kmp_result["matches"]})

        # Run Rabin-Karp on this hospital name
        rk_result = rabin_karp_search(name, query)
        rk_total_comparisons += rk_result["total_comparisons"]
        if rk_result["match_count"] > 0:
            rk_matches.append({**hospital, "match_positions": rk_result["matches"]})

    return {
        "query": query,
        "kmp_results": kmp_matches,
        "rk_results": rk_matches,
        "kmp_stats": {
            "algorithm": "KMP",
            "total_comparisons": kmp_total_comparisons,
            "hospitals_searched": len(hospitals),
            "matches_found": len(kmp_matches),
            "complexity": "O(n + m) per hospital"
        },
        "rk_stats": {
            "algorithm": "Rabin-Karp",
            "total_comparisons": rk_total_comparisons,
            "hospitals_searched": len(hospitals),
            "matches_found": len(rk_matches),
            "complexity": "O(n + m) avg per hospital"
        }
    }


# =============================================================================
# STANDALONE TEST  (run:  python string_matching.py)
# =============================================================================

if __name__ == "__main__":

    # --- Test LPS array ---
    print("=== LPS Array Tests ===")
    test_patterns = ["AAAA", "ABCABD", "AABAABAAA", "ABCDE"]
    for p in test_patterns:
        lps = build_lps(p)
        print(f"  pattern={p:12}  lps={lps}")

    # --- Basic search tests ---
    print("\n=== KMP Search ===")
    text = "Services Hospital Lahore, Jinnah Hospital, Mayo Hospital"
    query = "hospital"
    kmp = kmp_search(text, query)
    print(f"  Text:    '{text}'")
    print(f"  Pattern: '{query}'")
    print(f"  Matches at positions: {kmp['matches']}  ({kmp['comparisons']} comparisons)")

    print("\n=== Rabin-Karp Search ===")
    rk = rabin_karp_search(text, query)
    print(f"  Matches at positions: {rk['matches']}")
    print(f"  Hash comparisons: {rk['hash_comparisons']},  "
          f"Char comparisons: {rk['char_comparisons']},  "
          f"Spurious hits: {rk['spurious_hits']}")

    print("\n=== Naive Search (comparison) ===")
    naive = naive_search(text.lower(), query.lower())
    print(f"  Matches at positions: {naive['matches']}  ({naive['comparisons']} comparisons)")

    # All three should find the same positions
    assert kmp["matches"] == rk["matches"] == naive["matches"], "❌ Match mismatch!"
    print("\n✅ All three algorithms found the same matches.")

    # --- Hospital search test ---
    print("\n=== Hospital Search ===")
    hospitals = [
        {"id": 1, "name": "Services Hospital"},
        {"id": 2, "name": "Jinnah Hospital"},
        {"id": 3, "name": "Mayo Hospital"},
        {"id": 4, "name": "Shaukat Khanum Memorial Cancer Hospital"},
        {"id": 5, "name": "Children's Hospital"},
        {"id": 6, "name": "General Hospital"},
    ]
    result = search_hospitals(hospitals, "hospital")
    print(f"  Query: 'hospital'")
    print(f"  KMP found:          {len(result['kmp_results'])} hospitals, "
          f"{result['kmp_stats']['total_comparisons']} comparisons")
    print(f"  Rabin-Karp found:   {len(result['rk_results'])} hospitals, "
          f"{result['rk_stats']['total_comparisons']} comparisons")
    print("  Matching hospitals:")
    for h in result["kmp_results"]:
        print(f"    - {h['name']} (positions: {h['match_positions']})")
