#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import sys
import time
from collections import Counter
from datetime import datetime
from pathlib import Path


DISCOURSE_CONDITION_CODES = {
    "tr_coh": 1,
    "tr_ic": 2,
    "it_coh": 3,
    "it_ic": 4,
}
ISOLATED_TRANSITIVITY_CODES = {
    "transitive": 1,
    "intransitive": 2,
}
SMOKE_SEQUENCE = [
    (150, "rest_state_test"),
    (198, "discourse_context_present_test"),
    (199, "discourse_before_target_test"),
    (200, "target_onset_test"),
    (1, "condition_low_test"),
    (4, "condition_high_test"),
    (120, "item_high_test"),
    (201, "discourse_after_target_test"),
    (202, "trial_end_test"),
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def as_int(value: str, label: str) -> int:
    try:
        return int(str(value).strip())
    except Exception as err:
        raise AssertionError(f"{label} is not an integer: {value!r}") from err


def expect(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def check_image(repo: Path, package_dir: Path, image_value: str, row_label: str, errors: list[str]) -> None:
    if not image_value:
        return
    image_path = (package_dir / image_value).resolve()
    expect(image_path.is_file(), f"{row_label}: missing image {image_value}", errors)
    expect(image_path.suffix.lower() in {".jpg", ".jpeg"}, f"{row_label}: image is not JPEG: {image_value}", errors)


def validate_discourse(repo: Path, errors: list[str]) -> None:
    package_dir = repo / "psychopy_gurung_v1"
    for list_id in (1, 2):
        path = package_dir / "Conds" / f"main_list{list_id}_all_240.csv"
        expect(path.is_file(), f"missing discourse list file: {path}", errors)
        if not path.is_file():
            continue
        rows = read_rows(path)
        expect(len(rows) == 240, f"discourse list {list_id}: expected 240 rows, got {len(rows)}", errors)
        condition_counts = Counter()
        item_counts = Counter()
        for row_index, row in enumerate(rows, start=1):
            row_label = f"discourse list {list_id} row {row_index} {row.get('trial_id', '')}"
            condition_id = row.get("condition_id", "")
            expected_condition = DISCOURSE_CONDITION_CODES.get(condition_id)
            actual_condition = as_int(row.get("condition_trigger", ""), f"{row_label} condition_trigger")
            expect(expected_condition == actual_condition, f"{row_label}: condition trigger {actual_condition}, expected {expected_condition}", errors)
            dataset_number = as_int(row.get("dataset_number", ""), f"{row_label} dataset_number")
            stimulus_set = as_int(row.get("stimulus_set", ""), f"{row_label} stimulus_set")
            expected_item = ((dataset_number - 1) * 4) + stimulus_set
            actual_item = as_int(row.get("item_trigger", ""), f"{row_label} item_trigger")
            expect(expected_item == actual_item, f"{row_label}: item trigger {actual_item}, expected {expected_item}", errors)
            expect(1 <= actual_item <= 120, f"{row_label}: item trigger outside 1..120: {actual_item}", errors)
            condition_counts[actual_condition] += 1
            item_counts[actual_item] += 1
            for field in ("img1", "img2", "img3", "img4"):
                check_image(repo, package_dir, row.get(field, ""), f"{row_label} {field}", errors)
        expect(condition_counts == Counter({1: 60, 2: 60, 3: 60, 4: 60}), f"discourse list {list_id}: condition counts wrong: {dict(condition_counts)}", errors)
        expect(set(item_counts) == set(range(1, 121)), f"discourse list {list_id}: item triggers are not exactly 1..120", errors)
        repeated_wrong = {code: count for code, count in item_counts.items() if count != 2}
        expect(not repeated_wrong, f"discourse list {list_id}: each item trigger should occur twice, got {repeated_wrong}", errors)
        for block_id in range(1, 7):
            block_path = package_dir / "Conds" / f"main_list{list_id}_block{block_id}.csv"
            expect(block_path.is_file(), f"missing discourse block file: {block_path}", errors)
            if block_path.is_file():
                block_rows = read_rows(block_path)
                expect(len(block_rows) == 40, f"discourse list {list_id} block {block_id}: expected 40 rows, got {len(block_rows)}", errors)


def validate_isolated(repo: Path, errors: list[str]) -> None:
    package_dir = repo / "psychopy_gurung_isolated"
    for list_id in (1, 2):
        path = package_dir / "Conds" / f"isolated_main_list{list_id}_all_120.csv"
        expect(path.is_file(), f"missing isolated list file: {path}", errors)
        if not path.is_file():
            continue
        rows = read_rows(path)
        expect(len(rows) == 120, f"isolated list {list_id}: expected 120 rows, got {len(rows)}", errors)
        condition_counts = Counter()
        item_counts = Counter()
        target_images = Counter()
        for row_index, row in enumerate(rows, start=1):
            row_label = f"isolated list {list_id} row {row_index} {row.get('trial_id', '')}"
            transitivity = row.get("transitivity", "")
            expected_condition = ISOLATED_TRANSITIVITY_CODES.get(transitivity)
            actual_condition = as_int(row.get("condition_trigger", ""), f"{row_label} condition_trigger")
            expect(expected_condition == actual_condition, f"{row_label}: condition trigger {actual_condition}, expected {expected_condition}", errors)
            dataset_number = as_int(row.get("dataset_number", ""), f"{row_label} dataset_number")
            stimulus_set = as_int(row.get("stimulus_set", ""), f"{row_label} stimulus_set")
            expected_item = ((dataset_number - 1) * 4) + stimulus_set
            actual_item = as_int(row.get("item_trigger", ""), f"{row_label} item_trigger")
            expect(expected_item == actual_item, f"{row_label}: item trigger {actual_item}, expected {expected_item}", errors)
            condition_counts[actual_condition] += 1
            item_counts[actual_item] += 1
            target_image = row.get("target_image", "")
            target_images[target_image] += 1
            check_image(repo, package_dir, target_image, f"{row_label} target_image", errors)
        expect(condition_counts == Counter({1: 60, 2: 60}), f"isolated list {list_id}: condition counts wrong: {dict(condition_counts)}", errors)
        expect(set(item_counts) == set(range(1, 121)), f"isolated list {list_id}: item triggers are not exactly 1..120", errors)
        repeated_items = {code: count for code, count in item_counts.items() if count != 1}
        expect(not repeated_items, f"isolated list {list_id}: each item trigger should occur once, got {repeated_items}", errors)
        repeated_targets = {image: count for image, count in target_images.items() if count != 1}
        expect(not repeated_targets, f"isolated list {list_id}: target images repeated: {repeated_targets}", errors)


def validate_runtime_log(path: Path, require_serial: bool, errors: list[str]) -> None:
    expect(path.is_file(), f"missing trigger log: {path}", errors)
    if not path.is_file():
        return
    rows = read_rows(path)
    expect(bool(rows), f"trigger log is empty: {path}", errors)
    previous_time = None
    codes = Counter()
    for row_index, row in enumerate(rows, start=1):
        row_label = f"trigger log row {row_index}"
        code = as_int(row.get("trigger_code", ""), f"{row_label} trigger_code")
        expect(1 <= code <= 255, f"{row_label}: trigger code outside 1..255: {code}", errors)
        codes[code] += 1
        try:
            core_time = float(row.get("core_time", ""))
        except Exception:
            core_time = None
        expect(core_time is not None, f"{row_label}: missing/non-numeric core_time", errors)
        if core_time is not None and previous_time is not None:
            expect(core_time >= previous_time, f"{row_label}: core_time moved backwards", errors)
        if core_time is not None:
            previous_time = core_time
        if require_serial:
            expect(row.get("serial_sent") == "1", f"{row_label}: serial_sent is not 1", errors)
    print(f"Runtime log {path} contains {len(rows)} triggers; codes: {dict(sorted(codes.items()))}")


def validate(repo: Path, trigger_log: Path | None, require_serial: bool) -> int:
    errors: list[str] = []
    validate_discourse(repo, errors)
    validate_isolated(repo, errors)
    if trigger_log is not None:
        validate_runtime_log(trigger_log, require_serial, errors)
    if errors:
        print("EEG trigger validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("EEG trigger validation OK")
    return 0


def smoke_test(port: str | None, pulse_ms: float, log_dir: Path) -> int:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%Hh%M.%S.%f")[:-3]
    log_path = log_dir / f"trigger_smoke_{timestamp}.csv"
    serial_port = None
    details = "dry_run_no_port"
    if port:
        try:
            import serial
        except Exception as err:
            print(f"Cannot import pyserial, so no hardware trigger was sent: {err}")
            return 1
        try:
            serial_port = serial.Serial(port=port, baudrate=115200, timeout=0)
            details = "serial_open"
        except Exception as err:
            print(f"Could not open {port}: {err}")
            return 1
    fieldnames = ["trigger_index", "wall_time", "perf_counter", "trigger_code", "label", "serial_port", "serial_sent", "pulse_ms", "details"]
    try:
        with log_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            for index, (code, label) in enumerate(SMOKE_SEQUENCE, start=1):
                serial_sent = False
                row_details = details
                if serial_port is not None:
                    try:
                        serial_port.write(bytes([code]))
                        serial_port.flush()
                        if pulse_ms > 0:
                            time.sleep(pulse_ms / 1000.0)
                        serial_port.write(bytes([0]))
                        serial_port.flush()
                        serial_sent = True
                        row_details = "serial_sent"
                    except Exception as err:
                        row_details = f"serial_error={err}"
                writer.writerow(
                    {
                        "trigger_index": index,
                        "wall_time": datetime.now().isoformat(timespec="milliseconds"),
                        "perf_counter": f"{time.perf_counter():.6f}",
                        "trigger_code": code,
                        "label": label,
                        "serial_port": port or "",
                        "serial_sent": "1" if serial_sent else "0",
                        "pulse_ms": f"{pulse_ms:.3f}",
                        "details": row_details,
                    }
                )
                time.sleep(0.050)
    finally:
        if serial_port is not None:
            try:
                serial_port.write(bytes([0]))
                serial_port.close()
            except Exception:
                pass
    print(f"Smoke-test log written: {log_path}")
    if port:
        print(f"Sent {len(SMOKE_SEQUENCE)} test triggers to {port}. Check BrainVision/Recorder marks for the same sequence.")
    else:
        print("Dry run only. Add --port COM4, or the correct COM port, to send hardware triggers.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and smoke-test Gurung EEG trigger setup.")
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1], help="Repository root.")
    parser.add_argument("--log", type=Path, help="Optional eeg_triggers.csv from a real experiment run to validate.")
    parser.add_argument("--require-serial", action="store_true", help="Fail log validation if any row has serial_sent != 1.")
    parser.add_argument("--port", help="Optional COM port for a hardware smoke test, for example COM4.")
    parser.add_argument("--pulse-ms", type=float, default=5.0, help="Pulse duration for the hardware smoke test.")
    parser.add_argument("--smoke-only", action="store_true", help="Only run the COM-port smoke test.")
    parser.add_argument("--validate-only", action="store_true", help="Only run offline CSV/log validation.")
    parser.add_argument("--log-dir", type=Path, default=Path("trigger_test_logs"), help="Where smoke-test logs are written.")
    args = parser.parse_args()

    repo = args.repo.resolve()
    exit_code = 0
    if not args.smoke_only:
        exit_code |= validate(repo, args.log.resolve() if args.log else None, args.require_serial)
    if not args.validate_only:
        exit_code |= smoke_test(args.port, args.pulse_ms, (repo / args.log_dir).resolve())
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
