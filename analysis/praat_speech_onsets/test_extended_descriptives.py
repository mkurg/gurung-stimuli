import unittest
import json
import tempfile
from pathlib import Path

from extended_descriptives import erg_order, order_summary, paired_categories, retention
from seminar_stats import report_date
from package_seminar import FIGURES, figure_names


def row(rec, number, sol, category="Tr ERG", eligible=True):
    return {"recording": rec, "trial_number": number, "sol_ms": sol, "category": category,
            "eligible": eligible, "need_help": False}


class ExtendedTests(unittest.TestCase):
    def test_within_participant_contrasts_do_not_pool_condition_imbalances(self):
        rows = [row("a", 1, 1000), row("a", 2, 1200, "Tr zero"),
                row("b", 1, 2000), row("b", 2, 2100, "Tr zero"), row("b", 3, 2100, "Tr zero")]
        result = paired_categories(rows)
        self.assertEqual(result["paired_n"], 2)
        self.assertEqual(result["equal_participant_mean_difference_ms"], -150)
        self.assertEqual(result["erg_longer_participants"], 0)

    def test_missing_condition_is_not_imputed_as_zero_latency(self):
        result = paired_categories([row("a", 1, 1000), row("b", 1, 2000, "Tr zero")])
        self.assertEqual(result["paired_n"], 0)
        self.assertIsNone(result["equal_participant_mean_difference_ms"])

    def test_speedup_uses_scheduled_positions_not_first_eligible_twenty(self):
        rows = [row("a", 1, 1800), row("a", 21, 9000), row("a", 101, 1200), row("a", 120, 1400)]
        result = order_summary(rows)
        a = next(p for p in result["participants"] if p["selection"] == "All")
        self.assertEqual((a["early_n"], a["late_n"], a["speedup_ms"]), (1, 2, 500))
        self.assertEqual(result["overall"]["All"]["faster_later"], 1)

    def test_cutoff_is_inclusive_and_uses_transitive_denominator(self):
        rows = [row("a", 1, 1200), row("a", 2, 1199, "Tr zero"), row("a", 3, 5000, "Itr")]
        overall, by_person = retention(rows)
        cell = next(p for p in overall if p["minimum_sol_ms"] == 1200)
        self.assertEqual((cell["transitive_retained"], cell["transitive_lost_percent"]), (1, 50))
        self.assertEqual((cell["Tr ERG"], cell["Tr zero"], cell["Itr"]), (1, 0, 1))

    def test_excluded_transitive_breaks_switch_pair(self):
        rows = [row("a", 1, 1000), row("a", 2, 1100, "Itr"), row("a", 3, 1000, "Tr zero", False),
                row("a", 4, 1100, "Tr zero"), row("a", 5, 1000)]
        blocks, switches = erg_order(rows)
        self.assertEqual((switches[0]["valid_adjacent_transitive_pairs"], switches[0]["case_switches"]), (1, 1))
        self.assertEqual(switches[0]["switch_percent"], 100)

    def test_report_date_uses_user_timezone_at_midnight(self):
        self.assertEqual(report_date("2026-10-20T22:11:42+00:00"), "21 October 2026")

    def test_package_includes_extended_figures_only_when_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(figure_names(root), list(FIGURES))
            (root/"extended_summary.json").write_text(json.dumps({"figures": ["13_extra.png"]}), encoding="utf-8")
            self.assertEqual(figure_names(root), [*FIGURES, "13_extra.png"])

    def test_package_rejects_duplicate_and_external_figures(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for names in ([FIGURES[0]], ["../outside.png"]):
                (root/"extended_summary.json").write_text(json.dumps({"figures": names}), encoding="utf-8")
                with self.assertRaises(ValueError):
                    figure_names(root)


if __name__ == "__main__":
    unittest.main()
