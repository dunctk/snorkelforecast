from datetime import datetime, timedelta
from dateutil import tz

from django.test import SimpleTestCase

from conditions.views import (
    _best_available_hours,
    _build_day_summaries,
    _count_blockers,
    _format_best_window,
    _find_next_safe_window,
)


class ForecastViewHelperTests(SimpleTestCase):
    def test_count_blockers_prioritizes_top_causes(self):
        now = datetime(2026, 6, 24, 9, tzinfo=tz.UTC)
        hours = [
            {"time": now, "score": 0.1, "wave_ok": False, "wind_ok": False, "sst_ok": False, "slack_ok": True, "light_ok": True, "rating": "poor"},
            {"time": now, "wave_ok": False, "wind_ok": True, "sst_ok": False, "slack_ok": False, "light_ok": True, "score": 0.4, "rating": "fair"},
            {"time": now, "wave_ok": True, "wind_ok": False, "sst_ok": True, "slack_ok": False, "light_ok": False, "score": 0.5, "rating": "poor"},
        ]

        blockers = _count_blockers(hours)

        self.assertEqual(blockers[0], {"label": "Waves", "count": 2})
        self.assertEqual(blockers[1], {"label": "Wind", "count": 2})

    def test_count_blockers_does_not_flag_normal_non_slack_tide(self):
        now = datetime(2026, 6, 24, 9, tzinfo=tz.UTC)
        hours = [
            {
                "time": now,
                "score": 0.65,
                "wave_ok": True,
                "wind_ok": True,
                "sst_ok": True,
                "slack_ok": False,
                "tide_score": 0.625,
                "current_velocity": 0.1,
                "light_ok": True,
                "rating": "good",
            },
        ]

        blockers = _count_blockers(hours)

        self.assertEqual(blockers, [])

    def test_count_blockers_flags_strong_current(self):
        now = datetime(2026, 6, 24, 9, tzinfo=tz.UTC)
        hours = [
            {
                "time": now,
                "score": 0.4,
                "wave_ok": True,
                "wind_ok": True,
                "sst_ok": True,
                "slack_ok": False,
                "tide_score": 0.625,
                "current_velocity": 0.6,
                "light_ok": True,
                "rating": "fair",
            },
        ]

        blockers = _count_blockers(hours)

        self.assertEqual(blockers, [{"label": "Tide/current", "count": 1}])

    def test_best_available_orders_by_score_then_time(self):
        now = datetime(2026, 6, 24, 12, tzinfo=tz.UTC)
        hours = [
            {"time": now, "score": 0.3, "rating": "poor", "wave_ok": False},
            {"time": now.replace(hour=11), "score": 0.6, "rating": "fair", "wave_ok": False},
            {"time": now.replace(hour=13), "score": 0.6, "rating": "fair", "wave_ok": True},
        ]

        best = _best_available_hours(hours, limit=2)

        self.assertEqual(len(best), 2)
        self.assertEqual(best[0]["time"], now.replace(hour=13))
        self.assertEqual(best[1]["time"], now.replace(hour=11))

    def test_best_available_excludes_night_hours(self):
        now = datetime(2026, 6, 24, 20, tzinfo=tz.UTC)
        hours = [
            {"time": now, "score": 0.95, "rating": "good", "light_ok": False},
            {"time": now + timedelta(hours=2), "score": 0.60, "rating": "good", "light_ok": True},
        ]

        best = _best_available_hours(hours, limit=1)

        self.assertEqual(len(best), 1)
        self.assertEqual(best[0]["time"], now + timedelta(hours=2))

    def test_find_next_safe_window_ignores_darkness(self):
        now = datetime(2026, 6, 24, 19, tzinfo=tz.UTC)
        hours = [
            {"time": now, "ok": True, "light_ok": False},
            {"time": now + timedelta(hours=1), "ok": True, "light_ok": False},
            {"time": now + timedelta(hours=2), "ok": True, "light_ok": True},
            {"time": now + timedelta(hours=3), "ok": True, "light_ok": True},
        ]

        window = _find_next_safe_window(hours)

        self.assertEqual(window, {"start": now + timedelta(hours=2), "end": now + timedelta(hours=3)})

    def test_build_day_summaries_returns_top_status_per_day(self):
        local_tz = tz.gettz("Europe/Paris")
        noon = datetime(2026, 6, 24, 12, tzinfo=local_tz)
        plus12 = noon.replace(day=25)
        hours = [
            {"time": noon, "rating": "fair", "score": 0.55, "wave_ok": True},
            {"time": noon.replace(hour=13), "rating": "poor", "score": 0.2, "wave_ok": False},
            {"time": plus12, "rating": "good", "score": 0.75, "wave_ok": True},
        ]

        summaries = _build_day_summaries(hours, local_tz=local_tz)

        self.assertEqual(len(summaries), 2)
        self.assertEqual(summaries[0]["status"], "fair")
        self.assertEqual(summaries[1]["status"], "good")

    def test_format_best_window_includes_hours(self):
        now = datetime(2026, 6, 24, 8, tzinfo=tz.UTC)
        window = _format_best_window(
            hours=[{"time": now}],
            next_window={"start": now, "end": now.replace(hour=10)},
        )

        self.assertEqual(window, {"start": now, "end": now.replace(hour=10), "duration_hours": 2, "label": "Good window"})
