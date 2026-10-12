"""Browser-test server with a separate database, never the user's decisions."""

import json
import os
import copy
import hashlib
from http.server import ThreadingHTTPServer

from server import ROOT, build_session, handler_class
from suitability import SuitabilityStore
from annotations import AnnotationReader, textgrid_io
from recording_library import RecordingLibrary, atomic_json, bundle
from import_jobs import ImportJobs

def main():
    config = json.loads((ROOT / "session_config.json").read_text(encoding="utf-8"))
    session, assets = build_session(config)
    qa = ROOT / "qa"
    qa.mkdir(exist_ok=True)
    store = SuitabilityStore(qa / f"test_suitability_{os.getpid()}.sqlite3")
    with open(config["textgrid"], encoding="utf-8-sig") as handle:
        source = textgrid_io.parseTextgridStr(handle.read(), includeEmptyIntervals=True)
    for tier in source["tiers"]:
        if tier["class"] == "TextTier":
            tier["entries"] = [(float(time), label) for time, label in tier["entries"]]
        if tier["name"] == "speech_onset":
            tier["entries"] = [(452.208989, "s")]
        if tier["name"] == "transcription":
            tier["entries"] = [(0, 452.208989, ""), (452.208989, 453.407233, "thagu lurisy\u00f5"), (453.407233, session["duration"], "")]
    textgrid = qa / f"test_annotations_{os.getpid()}.TextGrid"
    textgrid.write_text(textgrid_io.getTextgridAsStr(source, format="long_textgrid", includeBlankSpaces=True), encoding="utf-8")
    config["textgrid"] = str(textgrid)
    reader = AnnotationReader(textgrid, session, qa / f"test_snapshots_{os.getpid()}")
    library_root = qa / f"test_library_{os.getpid()}"
    library = RecordingLibrary(library_root, bundle(session, assets, config, qa / "snapshots", reader), build_session, qa / "snapshots")
    second = copy.deepcopy(session)
    second["session_id"] = hashlib.sha256(b"QA second recording only").hexdigest()
    second["recording"] = "QA-second"
    second["participant"] = "QA"
    second_grid = qa / f"test_second_annotations_{os.getpid()}.TextGrid"
    for tier in source["tiers"]:
        if tier["name"] == "speech_onset":
            tier["entries"] = [(452.608989, "s")]
        if tier["name"] == "transcription":
            tier["entries"] = [(0, 452.608989, ""), (452.608989, 453.407233, "second session transcript"), (453.407233, session["duration"], "")]
    second_grid.write_text(textgrid_io.getTextgridAsStr(source, format="long_textgrid", includeBlankSpaces=True), encoding="utf-8")
    second_config = dict(config, textgrid=str(second_grid))
    library.loader = lambda value: (second, assets)

    def import_fixture(value, log):
        log("QA import fixture; real sources and user database are unchanged.")
        directory = library_root / second["session_id"][:20]
        atomic_json(directory / "config.json", second_config)
        entry = {"session_id": second["session_id"], "recording": second["recording"], "participant": "QA", "list": 1,
                 "main_trials": 120, "protocol": "isolated", "channel": "AUX1"}
        atomic_json(directory / "registration.json", entry)
        return dict(entry, textgrid=str(second_grid), stimtrak_wav=config["stimtrak_wav"])

    jobs = ImportJobs(qa / f"test_import_logs_{os.getpid()}", import_fixture)
    handler = handler_class(session, assets, config, store, reader, library, jobs)
    handler.log_message = lambda *args: None
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    print(json.dumps({"url": f"http://127.0.0.1:{server.server_port}", "textgrid": str(textgrid),
                      "second_session_id": second["session_id"],
                      "import_inputs": {key: config[key] for key in ("vhdr", "audio_dir", "experiment_dir")}}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
