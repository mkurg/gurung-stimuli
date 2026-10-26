import struct
import tempfile
import unittest
import wave
from pathlib import Path

from server import attach_full_playback, validate_full_recording


class FullPlaybackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="full-playback-test-")
        self.root = Path(self.temp.name)
        self.samples = struct.pack("<1000h", *range(1000))
        self.full = self.root / "full_session.wav"
        self.write_wav(self.full, self.samples)
        self.trials, self.segments = [], []
        for name, kind, start in (("main-001", "main", 100), ("practice-07", "practice", 400)):
            path = self.root / (name + ".wav")
            self.write_wav(path, self.samples[start * 2:(start + 100) * 2])
            self.trials.append({"id": name, "kind": kind, "number": int(name.split('-')[-1]),
                                "audio_filename": path.name, "audio_path": str(path)})
            self.segments.append({"stem": path.stem, "status": "written", "onset_sample": str(start + 10),
                                  "stop_sample": str(start + 90), "clip_start_sample": str(start),
                                  "clip_end_sample": str(start + 100), "n_frames": "100"})

    def tearDown(self):
        self.temp.cleanup()

    def write_wav(self, path, frames):
        with wave.open(str(path), "wb") as wav:
            wav.setparams((1, 2, 100, 0, "NONE", "not compressed"))
            wav.writeframes(frames)

    def add_main(self, number, start):
        path = self.root / f"main-{number:03d}.wav"
        self.write_wav(path, self.samples[start * 2:(start + 100) * 2])
        trial = {"id": path.stem, "kind": "main", "number": number,
                 "audio_filename": path.name, "audio_path": str(path)}
        segment = {"stem": path.stem, "status": "written", "onset_sample": str(start + 10),
                   "stop_sample": str(start + 90), "clip_start_sample": str(start),
                   "clip_end_sample": str(start + 100), "n_frames": "100"}
        self.trials.append(trial)
        self.segments.append(segment)
        return trial, segment

    def test_all_valid_clips_still_match_exactly(self):
        result = attach_full_playback(self.trials, self.segments, self.full)
        self.assertEqual(result["verified_segments"], 2)
        self.assertNotIn("unreadable_practice_wavs", result)
        self.assertEqual(self.trials[1]["playback"]["trial_start"], 4.1)

    def test_damaged_practice_clip_uses_full_window_without_modifying_source(self):
        path = Path(self.trials[1]["audio_path"])
        damaged = b"damaged WAV header" * 5
        path.write_bytes(damaged)
        result = attach_full_playback(self.trials, self.segments, self.full)
        self.assertEqual(result["verified_segments"], 1)
        self.assertEqual(result["logged_segments"], 2)
        self.assertEqual(result["unreadable_practice_wavs"][0]["trial_id"], "practice-07")
        self.assertTrue(result["unreadable_practice_wavs"][0]["sha256"])
        self.assertIn("unreadable", self.trials[1]["short_audio_warning"])
        self.assertEqual(self.trials[1]["playback"]["start"], 1.1)
        self.assertEqual(path.read_bytes(), damaged)

    def test_damaged_main_clip_is_not_silently_accepted(self):
        path = Path(self.trials[0]["audio_path"])
        path.write_bytes(b"damaged header")
        with self.assertRaisesRegex(ValueError, "Cannot read trial WAV.*main-001.wav"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_damaged_main_uses_full_window_only_with_two_verified_neighboring_mains(self):
        trial, _ = self.add_main(2, 300)
        self.add_main(3, 600)
        damaged = b"damaged main WAV"
        path = Path(trial["audio_path"])
        path.write_bytes(damaged)
        result = attach_full_playback(self.trials, self.segments, self.full)
        self.assertEqual(result["verified_segments"], 3)
        self.assertEqual(result["logged_segments"], 4)
        fallback = result["unreadable_main_wavs"][0]
        self.assertEqual(fallback["trial_id"], "main-002")
        self.assertEqual(fallback["validated_by_trials"], ["main-001", "main-003"])
        self.assertTrue(fallback["sha256"])
        self.assertEqual(trial["playback"]["trial_start"], 3.1)
        self.assertAlmostEqual(trial["playback"]["start"], .1)
        self.assertEqual(trial["playback"]["end"], 6.9)
        self.assertIn("EEG timing is unchanged", trial["short_audio_warning"])
        self.assertEqual(path.read_bytes(), damaged)

    def test_damaged_main_requires_immediate_neighbors_not_distant_or_practice_clips(self):
        trial, _ = self.add_main(2, 300)
        self.add_main(4, 600)
        Path(trial["audio_path"]).write_bytes(b"bad header")
        with self.assertRaisesRegex(ValueError, "immediately before and after"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_two_consecutive_damaged_mains_do_not_validate_each_other(self):
        trial, _ = self.add_main(2, 300)
        following, _ = self.add_main(3, 600)
        for candidate in (trial, following):
            Path(candidate["audio_path"]).write_bytes(b"bad header")
        with self.assertRaisesRegex(ValueError, "immediately before and after"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_main_fallback_requires_chronological_log_windows(self):
        trial, _ = self.add_main(2, 600)
        self.add_main(3, 300)
        Path(trial["audio_path"]).write_bytes(b"bad header")
        with self.assertRaisesRegex(ValueError, "not chronological around main-002"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_readable_main_with_wrong_samples_still_stops_import(self):
        trial, _ = self.add_main(2, 300)
        self.add_main(3, 600)
        self.write_wav(Path(trial["audio_path"]), b"\0\0" * 100)
        with self.assertRaisesRegex(ValueError, "samples do not match.*main-002"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_valid_header_but_different_samples_still_rejects_even_practice(self):
        self.write_wav(Path(self.trials[1]["audio_path"]), b"\0\0" * 100)
        with self.assertRaisesRegex(ValueError, "samples do not match.*practice-07"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_practice_fallback_requires_valid_contained_bounds(self):
        Path(self.trials[1]["audio_path"]).write_bytes(b"bad header")
        self.segments[1]["stop_sample"] = "501"
        with self.assertRaisesRegex(ValueError, "not contained.*practice-07"):
            attach_full_playback(self.trials, self.segments, self.full)

    def test_full_recording_errors_name_file_and_reject_truncation(self):
        self.full.write_bytes(b"bad header")
        with self.assertRaisesRegex(ValueError, "Cannot read WAV.*full_session.wav"):
            validate_full_recording(self.full)
        self.write_wav(self.full, self.samples)
        with self.full.open("r+b") as handle:
            handle.truncate(self.full.stat().st_size - 2)
        with self.assertRaisesRegex(ValueError, "truncated"):
            validate_full_recording(self.full)

    def test_no_validating_short_clip_is_rejected(self):
        practice = self.trials[1]
        Path(practice["audio_path"]).write_bytes(b"bad header")
        with self.assertRaisesRegex(ValueError, "No readable short WAVs"):
            attach_full_playback([practice], [self.segments[1]], self.full)


if __name__ == "__main__":
    unittest.main()
