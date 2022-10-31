import pytest

from com.dtmilano.android.viewclient import ViewClient


def test_levenshtein_distance():
    with pytest.raises(ValueError):
        ViewClient.levenshtein_distance(None, "any")
    with pytest.raises(ValueError):
        ViewClient.levenshtein_distance("any", None)
    assert ViewClient.levenshtein_distance("", "") == 0
    assert ViewClient.levenshtein_distance(b"", b"") == 0
    assert ViewClient.levenshtein_distance("", "a") == 1
    assert ViewClient.levenshtein_distance("aaapppp", "") == 7
    assert ViewClient.levenshtein_distance("frog", "fog") == 1
    assert ViewClient.levenshtein_distance("fly", "ant") == 3
    assert ViewClient.levenshtein_distance("elephant", "hippo") == 7
    assert ViewClient.levenshtein_distance("hippo", "elephant") == 7
    assert ViewClient.levenshtein_distance("hippo", "zzzzzzzz") == 8
    assert ViewClient.levenshtein_distance("hippo", b"zzzzzzzz") == 8
    assert ViewClient.levenshtein_distance(b"hippo", "zzzzzzzz") == 8
    assert ViewClient.levenshtein_distance(b"hippo", b"zzzzzzzz") == 8
    assert ViewClient.levenshtein_distance("hello", "hallo") == 1
