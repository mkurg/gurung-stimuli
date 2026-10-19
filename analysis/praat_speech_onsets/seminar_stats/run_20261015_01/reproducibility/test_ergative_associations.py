import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ergative_associations import (
    INDEFINITE, UNMARKED, UNRESOLVED, UNRESOLVED_NOUN, association_summary,
    canonical_noun, code_rows, condition_table, load_condition_tables, normalize, rate, subject_coding,
)


class ErgativeAssociationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.book = json.loads(Path(__file__).with_name("ergative_codebook.json").read_text(encoding="utf-8"))

    def code(self, text):
        return subject_coding(text, self.book)

    def test_confirmed_noun_variants_merge(self):
        for a, b in (("maema", "maemae"), ("nanikolo", "nanikola"), ("rima", "rimae"),
                     ("maemakolo", "maemakola"), ("babukolo", "babukola"),
                     ("kolo", "kola"), ("rimaekolo", "rimaekola")):
            self.assertEqual(self.code(a + " speech")["noun_group"], self.code(b + " speech")["noun_group"])

    def test_case_forms_merge_without_becoming_indefinite(self):
        self.assertEqual(self.code("ma-i speech")["noun_group"], "ma")
        self.assertEqual(self.code("ma-i speech")["indefiniteness"], UNMARKED)
        self.assertEqual(self.code("tsu maema-ye speech")["noun_group"], "maema")

    def test_prefix_and_adjacent_indefinite_word(self):
        for text in ("kri ma-i speech", "tsu rimae kri-ye speech", "rimae kri-? speech"):
            self.assertEqual(self.code(text)["indefiniteness"], INDEFINITE)
        self.assertIn("uncertain_case_on_kri", self.code("rimae kri-? speech")["coding_notes"])

    def test_attached_ri_variants_merge(self):
        for form, noun in (("maemakolori", "maemakolo"), ("tshamiuri", "tshami"),
                           ("rimauri", "rimae"), ("kolori", "kolo"), ("babukolori", "babukolo")):
            result = self.code(form + " speech")
            self.assertEqual((result["noun_group"], result["indefiniteness"]), (noun, INDEFINITE))

    def test_object_indefinite_does_not_classify_subject(self):
        self.assertEqual(self.code("budzyu-yi daraza meleai rimae kri")["indefiniteness"], UNMARKED)
        self.assertEqual(self.code("tsu mi mi salgeimo")["noun_group"], "mi")

    def test_unrecognized_head_stays_unknown_not_definite(self):
        result = self.code("tsu mla speech")
        self.assertEqual((result["noun_group"], result["indefiniteness"]), (UNRESOLVED_NOUN, UNRESOLVED))
        self.assertEqual(self.code("tsu kri")["indefiniteness"], UNRESOLVED)

    def test_literal_ri_rule_flags_lexical_edge_case(self):
        result = self.code("tsuru misteri bana speech")
        self.assertEqual(result["indefiniteness"], INDEFINITE)
        self.assertEqual(result["noun_group"], UNRESOLVED_NOUN)
        self.assertIn("unrecognized_noun_after_ri_removal", result["coding_notes"])

    def test_unconfirmed_spellings_not_merged(self):
        self.assertNotEqual(self.code("phres\u0129kolo speech")["noun_group"], self.code("phr\u1ebdsikolo speech")["noun_group"])
        self.assertEqual(normalize("phr\u02dcesi"), "phr\u1ebdsi")

    def test_alias_cycles_rejected(self):
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            canonical_noun("a", {"noun_aliases": {"a": "b", "b": "a"}})

    def test_duplicate_condition_items_rejected(self):
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            condition_table("item_trigger\n1\n1\n")

    def test_rates_use_trials_and_count_people_uniquely(self):
        rows = [{"ergative": flag, "recording": "001i", "need_help": flag} for flag in (True, True, False)]
        stats = rate(rows)
        self.assertEqual((stats["n"], stats["erg"], stats["zero"], stats["participants"], stats["need_help"]), (3, 2, 1, 1, 2))
        self.assertAlmostEqual(stats["erg_percent"], 200/3)
        self.assertIsNone(rate([])["erg_percent"])

    def test_every_group_reconciles_including_unresolved(self):
        rows = [{"ergative": flag, "recording": "001i", "need_help": False,
                 "noun_group": "ma" if flag else UNRESOLVED_NOUN, "picture_action": "wash dish", "picture_verb": "wash",
                 "indefiniteness": UNMARKED if flag else UNRESOLVED, "coding_notes": []} for flag in (True, False)]
        summary = association_summary(rows, {"generated_at_utc": "2026-10-13"}, self.book)
        for groups in summary["groups"].values():
            self.assertEqual(sum(g["n"] for g in groups), 2)
            self.assertEqual(sum(g["erg"] for g in groups), 1)

    def join_fixture(self):
        row = {"eligible": True, "category": "Tr zero", "session_id": "session", "trial_id": "main-001",
               "experiment_list": 1, "item_trigger": 7, "condition": "tr_coh", "recording": "001i",
               "transcription": "ma-i object speech", "need_help": True}
        trial = {"id": "main-001", "image_set": 3, "stimulus_set": 1,
                 "image_filename": "tr_target.jpg", "scene": "stand wash clothes"}
        condition = {"condition_id": "tr_coh", "transitivity": "transitive", "dataset_number": "3",
                     "stimulus_set": "1", "target_image": "../pictures/tr_target.jpg",
                     "dataset_label": "stand_wash_clothes"}
        snapshot = {"bundles": [{"session": {"session_id": "session", "trials": [trial]}}]}
        return row, snapshot, {1: {7: condition}}

    def test_join_keeps_manual_outcome_despite_case_ending_and_help(self):
        row, snapshot, tables = self.join_fixture()
        result = code_rows([row], snapshot, self.book, tables)[0]
        self.assertFalse(result["ergative"])
        self.assertEqual(result["noun_group"], "ma")
        self.assertEqual(result["picture_action"], "wash clothes")
        self.assertEqual(result["picture_verb"], "wash")
        self.assertIn("visible_case_ending_but_not_flagged_erg", result["coding_notes"])
        self.assertIn("need_help_flag_kept_in_analysis", result["coding_notes"])

    def test_join_skips_ineligible_and_intransitive(self):
        row, snapshot, tables = self.join_fixture()
        rows = [{**row, "eligible": False}, {**row, "category": "Itr"}]
        self.assertEqual(code_rows(rows, snapshot, self.book, tables), [])

    def test_join_rejects_picture_and_scene_mismatches(self):
        row, snapshot, tables = self.join_fixture()
        wrong = copy.deepcopy(tables)
        wrong[1][7]["dataset_number"] = "99"
        with self.assertRaisesRegex(ValueError, "Picture/condition"):
            code_rows([row], snapshot, self.book, wrong)
        wrong = copy.deepcopy(tables)
        wrong[1][7]["dataset_label"] = "stand_drink_tea"
        with self.assertRaisesRegex(ValueError, "Scene-label"):
            code_rows([row], snapshot, self.book, wrong)

    def test_condition_hash_checked_even_with_portable_path_override(self):
        name = "isolated_main_list1_all_120.csv"
        content = b"item_trigger\n7\n"
        snapshot = {"bundles": [{"session": {"recording": "001i", "list": 1,
                    "sources": [{"path": "C:\\old-device\\" + name,
                                 "sha256": hashlib.sha256(content).hexdigest()}]}}]}
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / name
            path.write_bytes(content)
            tables, sources = load_condition_tables(snapshot, Path(tmp))
            self.assertIn(7, tables[1])
            path.write_bytes(b"item_trigger\n8\n")
            with self.assertRaisesRegex(ValueError, "changed since snapshot"):
                load_condition_tables(snapshot, Path(tmp))


if __name__ == "__main__":
    unittest.main()
