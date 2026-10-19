import unittest

from action_sol_stats import group_summary


def row(rec, action, sol, kind="transitive"):
    return {"recording": rec, "picture_action": action, "sol_ms": sol,
            "transitivity": kind, "category": "Tr zero" if kind == "transitive" else "Itr", "need_help": False}


class ActionSolTests(unittest.TestCase):
    def test_mean_median_counts_and_people(self):
        data = group_summary([row("a", "eat", 1000), row("a", "eat", 1500), row("b", "eat", 2000)])["transitive"]
        group = data["groups"][0]
        self.assertEqual((group["n"], group["participants"], group["mean_ms"], group["median_ms"]), (3, 2, 1500, 1500))

    def test_participant_centering_removes_constant_speed_offset(self):
        rows = [row("a", "eat", 1000), row("a", "plant", 1500), row("b", "eat", 2000), row("b", "plant", 2500)]
        groups = group_summary(rows)["transitive"]["groups"]
        self.assertEqual(groups[1]["participant_centered_mean_ms"] - groups[0]["participant_centered_mean_ms"], 500)
        self.assertEqual(groups[0]["participant_centered_mean_ms"], 1500)

    def test_centering_and_means_keep_transitivity_separate(self):
        rows = [row("a", "eat", 1000), row("a", "plant", 1500), row("a", "run", 5000, "intransitive")]
        data = group_summary(rows)
        self.assertEqual(data["transitive"]["participant_means_ms"]["a"], 1250)
        self.assertEqual(data["intransitive"]["participant_means_ms"]["a"], 5000)

    def test_paired_comparison_requires_both_actions(self):
        data = group_summary([row("a", "eat", 1000), row("a", "plant", 1500), row("b", "eat", 900)])["transitive"]
        comparison = data["posthoc_extreme_comparison"]
        self.assertEqual(comparison["paired_participants"], 1)
        self.assertEqual(comparison["slower_action_longer_count"], 1)
        self.assertEqual(comparison["participants"][0]["slow_minus_fast_ms"], 500)

    def test_no_data_has_clear_error(self):
        with self.assertRaisesRegex(ValueError, "No eligible"):
            group_summary([])


if __name__ == "__main__":
    unittest.main()
