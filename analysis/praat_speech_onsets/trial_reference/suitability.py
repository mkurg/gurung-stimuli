"""Durable, session-scoped behavioural exclusion decisions."""

import csv
import io
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path


class SuitabilityStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS suitability (
                    session_id TEXT NOT NULL,
                    trial_id TEXT NOT NULL,
                    unsuitable INTEGER NOT NULL CHECK(unsuitable IN (0, 1)),
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY(session_id, trial_id)
                )
            """)
            connection.execute("""
                CREATE TABLE IF NOT EXISTS trial_flags (
                    session_id TEXT NOT NULL,
                    trial_id TEXT NOT NULL,
                    field TEXT NOT NULL CHECK(field IN ('ergative', 'need_help')),
                    marked INTEGER NOT NULL CHECK(marked IN (0, 1)),
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY(session_id, trial_id, field)
                )
            """)

    def read(self, session_id):
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            records = connection.execute(
                "SELECT trial_id, unsuitable, updated_at_utc FROM suitability WHERE session_id = ?",
                (session_id,),
            ).fetchall()
        return {trial_id: {"unsuitable": bool(flag), "updated_at_utc": updated} for trial_id, flag, updated in records}

    def set(self, session_id, trial_id, unsuitable):
        if type(unsuitable) is not bool:
            raise ValueError("unsuitable must be a boolean.")
        updated = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            connection.execute("""
                INSERT INTO suitability(session_id, trial_id, unsuitable, updated_at_utc)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(session_id, trial_id) DO UPDATE SET
                    unsuitable = excluded.unsuitable, updated_at_utc = excluded.updated_at_utc
            """, (session_id, trial_id, int(unsuitable), updated))
        return {"unsuitable": unsuitable, "updated_at_utc": updated}

    def read_flags(self, session_id, field):
        if field not in ("ergative", "need_help"):
            raise ValueError("Unknown trial flag.")
        with closing(sqlite3.connect(self.path, timeout=10)) as connection:
            records = connection.execute(
                "SELECT trial_id, marked, updated_at_utc FROM trial_flags WHERE session_id = ? AND field = ?",
                (session_id, field),
            ).fetchall()
        return {trial_id: {"marked": bool(marked), "updated_at_utc": updated} for trial_id, marked, updated in records}

    def set_flag(self, session_id, trial_id, field, marked):
        if field not in ("ergative", "need_help") or type(marked) is not bool:
            raise ValueError("Expected an ergative/need_help flag and a boolean value.")
        updated = datetime.now(timezone.utc).isoformat()
        with closing(sqlite3.connect(self.path, timeout=10)) as connection, connection:
            connection.execute("""
                INSERT INTO trial_flags(session_id, trial_id, field, marked, updated_at_utc)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id, trial_id, field) DO UPDATE SET
                    marked = excluded.marked, updated_at_utc = excluded.updated_at_utc
            """, (session_id, trial_id, field, int(marked), updated))
        return {"marked": marked, "updated_at_utc": updated}


def suitability_csv(session, decisions, ergative=None, need_help=None):
    output = io.StringIO(newline="")
    columns = ["session_id", "recording", "participant", "experiment_list", "phase", "trial_number", "trial_id",
               "item_trigger", "condition", "stimulus_onset_eeg_s", "trial_end_eeg_s", "psychopy_trial_wav",
               "unsuitable", "decision_saved", "updated_at_utc", "ergative", "ergative_decision_saved",
               "ergative_updated_at_utc", "need_help", "need_help_decision_saved", "need_help_updated_at_utc"]
    writer = csv.DictWriter(output, fieldnames=columns)
    writer.writeheader()
    for trial in session["trials"]:
        decision = decisions.get(trial["id"], {})
        erg = (ergative or {}).get(trial["id"], {})
        help_flag = (need_help or {}).get(trial["id"], {})
        writer.writerow({
            "session_id": session["session_id"], "recording": session["recording"], "participant": session["participant"],
            "experiment_list": session["list"], "phase": trial["kind"], "trial_number": trial["number"],
            "trial_id": trial["id"], "item_trigger": f"S {trial['item']}" if trial["item"] is not None else "",
            "condition": trial["condition"], "stimulus_onset_eeg_s": trial["start"], "trial_end_eeg_s": trial["end"],
            "psychopy_trial_wav": trial["audio_filename"], "unsuitable": int(decision.get("unsuitable", False)),
            "decision_saved": int(bool(decision)), "updated_at_utc": decision.get("updated_at_utc", ""),
            "ergative": int(erg["marked"]) if erg else "", "ergative_decision_saved": int(bool(erg)),
            "ergative_updated_at_utc": erg.get("updated_at_utc", ""),
            "need_help": int(help_flag.get("marked", False)), "need_help_decision_saved": int(bool(help_flag)),
            "need_help_updated_at_utc": help_flag.get("updated_at_utc", ""),
        })
    return output.getvalue().encode("utf-8-sig")
