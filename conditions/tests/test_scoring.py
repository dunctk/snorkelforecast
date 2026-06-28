from django.test import SimpleTestCase
from conditions.snorkel import _rating_from_score, _tide_score, _calculate_score


class RatingTest(SimpleTestCase):
    def test_rating_thresholds(self):
        self.assertEqual(_rating_from_score(0.73), "excellent")
        self.assertEqual(_rating_from_score(0.72), "excellent")
        self.assertEqual(_rating_from_score(0.71), "good")
        self.assertEqual(_rating_from_score(0.55), "good")
        self.assertEqual(_rating_from_score(0.45), "fair")
        self.assertEqual(_rating_from_score(0.35), "fair")
        self.assertEqual(_rating_from_score(0.34), "poor")

    def test_rating_poor_on_low_score(self):
        self.assertEqual(_rating_from_score(0.2), "poor")
        self.assertEqual(_rating_from_score(0.0), "poor")


class TideScoreTest(SimpleTestCase):
    def test_high_slack_best(self):
        score = _tide_score(0.5, 0.1, True, True, 1.0)
        self.assertAlmostEqual(score, 1.0)

    def test_near_high_with_current(self):
        score = _tide_score(0.5, 0.4, True, True, 1.0)
        self.assertAlmostEqual(score, 0.8)

    def test_rising_tide(self):
        score = _tide_score(0.3, 0.1, False, True, 1.0)
        self.assertAlmostEqual(score, 0.7)

    def test_falling_tide(self):
        score = _tide_score(0.3, 0.1, False, False, 1.0)
        self.assertAlmostEqual(score, 0.625)

    def test_neutral_no_data(self):
        score = _tide_score(None, None, False, None, None)
        self.assertAlmostEqual(score, 0.5)

    def test_strong_current_penalty(self):
        score = _tide_score(0.5, 0.8, False, True, 1.0)
        self.assertAlmostEqual(score, 0.25)

    def test_very_low_tide(self):
        score = _tide_score(-0.8, 0.1, False, True, 1.0)
        self.assertAlmostEqual(score, 0.0)

    def test_large_tidal_range_penalty(self):
        score = _tide_score(0.5, 0.1, True, True, 2.5)
        self.assertAlmostEqual(score, 0.75)

    def test_combined_penalties_clamped(self):
        score = _tide_score(-0.6, 0.8, False, True, 2.5)
        self.assertAlmostEqual(score, 0.0)


class CalculateScoreTest(SimpleTestCase):
    def test_perfect_conditions(self):
        score = _calculate_score(0.0, 0.0, 25.0, 1.0, light_ok=True)
        self.assertAlmostEqual(score, 1.0)

    def test_no_data_returns_zero(self):
        self.assertEqual(_calculate_score(None, 2.0, 25.0, 0.5, light_ok=True), 0.0)
        self.assertEqual(_calculate_score(0.3, None, 25.0, 0.5, light_ok=True), 0.0)
        self.assertEqual(_calculate_score(0.3, 2.0, None, 0.5, light_ok=True), 0.0)

    def test_darkness_returns_zero(self):
        self.assertEqual(_calculate_score(0.3, 2.0, 25.0, 0.5, light_ok=False), 0.0)

    def test_bad_tide_lowers_score(self):
        good_tide = _calculate_score(0.3, 2.0, 25.0, 1.0, True, None)
        bad_tide = _calculate_score(0.3, 2.0, 25.0, 0.0, True, None)
        self.assertGreater(good_tide, bad_tide)

    def test_weighted_sum_bounds(self):
        score = _calculate_score(0.3, 2.0, 25.0, 0.5, True, None)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 1.0)

    def test_clear_sky_has_no_cloud_penalty(self):
        baseline = _calculate_score(0.3, 2.0, 25.0, 1.0, light_ok=True)
        cloudy = _calculate_score(0.3, 2.0, 25.0, 1.0, True, 0.0)
        missing_cloud = _calculate_score(0.3, 2.0, 25.0, 1.0, True, None)
        self.assertAlmostEqual(baseline, cloudy)
        self.assertAlmostEqual(baseline, missing_cloud)

    def test_cloudy_conditions_penalize_score(self):
        clear = _calculate_score(0.3, 2.0, 25.0, 1.0, True, 0.0)
        overcast = _calculate_score(0.3, 2.0, 25.0, 1.0, True, 100.0)
        self.assertLess(overcast, clear)

    def test_cloud_penalty_is_a_minor_modifier(self):
        clear = _calculate_score(0.12, 2.5, 24.0, 0.8, True, 0.0)
        overcast = _calculate_score(0.12, 2.5, 24.0, 0.8, True, 100.0)
        self.assertAlmostEqual(clear - overcast, 0.12)
        self.assertEqual(_rating_from_score(overcast), "excellent")

    def test_near_ideal_conditions_rate_excellent(self):
        score = _calculate_score(0.2, 4.0, 24.0, 0.625, True, 20.0)
        self.assertEqual(_rating_from_score(score), "excellent")
