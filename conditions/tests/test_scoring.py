from conditions.snorkel import _rating_from_score


def test_rating_thresholds_with_slack():
    assert _rating_from_score(0.81, True) == "excellent"
    assert _rating_from_score(0.8, True) == "excellent"
    assert _rating_from_score(0.75, True) == "good"
    assert _rating_from_score(0.6, True) == "good"
    assert _rating_from_score(0.45, True) == "fair"
    assert _rating_from_score(0.4, True) == "fair"
    assert _rating_from_score(0.39, True) == "poor"


def test_rating_capped_without_slack():
    # excellent and good are capped to fair when slack is not OK
    assert _rating_from_score(0.95, False) == "fair"
    assert _rating_from_score(0.7, False) == "fair"
    # fair and poor remain as-is
    assert _rating_from_score(0.45, False) == "fair"
    assert _rating_from_score(0.2, False) == "poor"

