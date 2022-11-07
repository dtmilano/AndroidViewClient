import sys
from typing import Union

DEBUG_DISTANCE = False


def levenshtein_distance(s: Union[bytes, str], t: Union[bytes, str]) -> int:
    """
    Find the Levenshtein distance between two Strings.

    Python version of Levenshtein distance method implemented in Java at
    U{http://www.java2s.com/Code/Java/Data-Type/FindtheLevenshteindistancebetweentwoStrings.htm}.

    This is the number of changes needed to change one String into
    another, where each change is a single character modification (deletion,
    insertion or substitution).

    The previous implementation of the Levenshtein distance algorithm
    was from U{http://www.merriampark.com/ld.htm}

    Chas Emerick has written an implementation in Java, which avoids an OutOfMemoryError
    which can occur when my Java implementation is used with very large strings.
    This implementation of the Levenshtein distance algorithm
    is from U{http://www.merriampark.com/ldjava.htm}::

        StringUtils.getLevenshteinDistance(null, *)             = IllegalArgumentException
        StringUtils.getLevenshteinDistance(*, null)             = IllegalArgumentException
        StringUtils.getLevenshteinDistance("","")               = 0
        StringUtils.getLevenshteinDistance("","a")              = 1
        StringUtils.getLevenshteinDistance("aaapppp", "")       = 7
        StringUtils.getLevenshteinDistance("frog", "fog")       = 1
        StringUtils.getLevenshteinDistance("fly", "ant")        = 3
        StringUtils.getLevenshteinDistance("elephant", "hippo") = 7
        StringUtils.getLevenshteinDistance("hippo", "elephant") = 7
        StringUtils.getLevenshteinDistance("hippo", "zzzzzzzz") = 8
        StringUtils.getLevenshteinDistance("hello", "hallo")    = 1

    @param s:  the first String, must not be null
    @param t:  the second String, must not be null
    @return: result distance
    @raise ValueError: if either String input C{null}
    """
    if s is None or t is None:
        raise ValueError("Strings must not be None")

    n = len(s)
    m = len(t)

    if n == 0:
        return m
    elif m == 0:
        return n

    if n > m:
        tmp = s
        s = t
        t = tmp
        n = m
        m = len(t)

    p = [0] * (n + 1)
    d = [0] * (n + 1)

    for i in range(0, n + 1):
        p[i] = i

    for j in range(1, m + 1):
        if DEBUG_DISTANCE:
            if j % 100 == 0:
                print("DEBUG:", int(j / (m + 1.0) * 100), "%\r", end=' ', file=sys.stderr)
        t_j = t[j - 1]
        d[0] = j

        for i in range(1, n + 1):
            cost = 0 if s[i - 1] == t_j else 1
            #  minimum of cell to the left+1, to the top+1, diagonally left and up +cost
            d[i] = min(min(d[i - 1] + 1, p[i] + 1), p[i - 1] + cost)

        _d = p
        p = d
        d = _d

    if DEBUG_DISTANCE:
        print("\n", file=sys.stderr)
    return p[n]
