import unittest

from participant_erg_sol import association_summary, correlation, participant_summary


def row(rec, category, sol, eligible=True):
    return {"recording": rec, "category": category, "sol_ms": sol,
            "eligible": eligible, "need_help": True, "ergative_flag_saved": False}


class ParticipantErgSolTests(unittest.TestCase):
    def test_same_eligible_transitive_trials_supply_both_measures(self):
        rows = [row("a", "Tr ERG", 1000), row("a", "Tr zero", 2000),
                row("a", "Itr", 9000), row("a", "Tr ERG", 8000, False)]
        p = participant_summary(rows)[0]
        self.assertEqual(p["transitive_n"], 2)
        self.assertEqual(p["erg_percent"], 50)
        self.assertEqual(p["distance_from_50_pp"], 0)
        self.assertEqual(p["transitive_mean_sol_ms"], 1500)
        self.assertEqual(p["transitive_median_sol_ms"], 1500)
        self.assertEqual(p["need_help_n"], 2)
        self.assertEqual(p["zero_without_saved_decision_n"], 1)

    def test_balance_distance_is_symmetric(self):
        people = participant_summary([row("erg", "Tr ERG", 1000), row("zero", "Tr zero", 2000)])
        self.assertEqual([p["distance_from_50_pp"] for p in people], [50, 50])
        self.assertEqual([p["erg_percent"] for p in people], [100, 0])

    def test_no_usable_transitives_does_not_invent_a_rate(self):
        self.assertEqual(participant_summary([row("a", "Itr", 1000)]), [])

    def test_correlations_are_participant_level_and_leave_one_out(self):
        people = [{"recording": str(i), "erg_percent": i, "distance_from_50_pp": 50-i,
                   "transitive_mean_sol_ms": 1000+10*i, "transitive_median_sol_ms": 900+10*i}
                  for i in range(4)]
        result = association_summary(people)
        self.assertAlmostEqual(result["erg_percent"]["transitive_mean_sol_ms"]["pearson_r"], 1)
        self.assertAlmostEqual(result["distance_from_50_pp"]["transitive_mean_sol_ms"]["pearson_r"], -1)
        self.assertEqual(len(result["erg_percent"]["transitive_mean_sol_ms"]["leave_one_out_r"]), 4)

    def test_undefined_correlation_is_not_zero(self):
        self.assertIsNone(correlation([{"x": 1, "y": i} for i in range(3)], "x", "y"))
        self.assertIsNone(correlation([{"x": 1, "y": 1}], "x", "y"))


if __name__ == "__main__":
    unittest.main()
