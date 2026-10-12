# Manual Speech-Onset Annotation From BrainVision/StimTrak Recordings

## Quick Workflow

Use `START_WORKFLOW.cmd` for the shared recording library and its folder-plus
button to import each new isolated-task recording, starting with AUX extraction.
`ADD_RECORDING.cmd` is the file-dialog alternative. All later recordings are
selected in the same page, with their own annotation files and flags.

**The current step-by-step guide is [WORKFLOW.md](WORKFLOW.md).** It covers import,
Praat annotation/save, Need help/Ergative/Unsuitable tags, combined export and
backups. The detailed converter background below is retained for reference.

Start with the original BrainVision recording. Use MNE-Python to extract the microphone channel and copy the existing marker onsets into a Praat TextGrid. Annotate speech onsets in a separate tier of that TextGrid.

The WAV stores the sound samples. The accompanying TextGrid stores trigger labels and your speech-onset annotations. Keep both files together. The original .vhdr/.eeg/.vmrk files remain the source recording.

Selected workflow: the StimTrak microphone extracted from AUX1 is the timing source of truth. Annotate on that unchanged EEG sample timeline. Consult PsychoPy audio only to identify unclear speech; do not use its timestamps to position points or shift the imported triggers. The alternate PsychoPy-alignment work is archived and is not part of this pipeline.

## 1. Locate the recording files

Find the original continuous recording's .vhdr header, its linked .eeg data file, and its linked .vmrk marker file. Keep them together with their original filenames. A .vhdr alone contains no speech waveform.

You can open the .vhdr in Notepad to inspect DataFile=, MarkerFile=, SamplingInterval=, and [Channel Infos]. The sampling interval is in microseconds; sampling rate in Hz is 1,000,000 divided by SamplingInterval. The microphone channel might be named StimTrak, Mic, Audio, or AUX, but the name alone does not establish what was connected. Confirm its identity using the acquisition setup or the person who recorded the data.

Do not use an EEG file that has already been averaged, segmented into trials, or processed with EEG filters for this extraction. Acquisition filters and bandwidth limits already present in the original recording cannot be undone by converting it.

## 2. Install the software

Install MNE-Python using the Windows standalone installer from https://mne.tools/stable/install/installers.html. It includes Python and dependencies. For this converter, you can use the MNE-Python Prompt directly; a separate code editor is not required.

Install Praat if needed from https://www.fon.hum.uva.nl/praat/download_win.html.

## 3. Run the supplied converter

Open the MNE-Python Prompt from the Windows Start menu. Run the following command on this computer:

```text
python "C:\Users\Sofya\.codex\visualizations\2026\10\01\01a0f928-a873-74b1-8256-3834dc087ebe\praat_speech_onsets\brainvision_to_praat.py"
```

At the first prompt, enter the full path to the recording's .vhdr. In File Explorer, right-click that file and choose Copy as path, then paste the path into the prompt and press Enter. Quotation marks surrounding this pasted path are accepted.

The converter lists every recorded channel with a number. Enter the microphone channel number or exact channel name and press Enter. For your 072i recording, enter AUX1. Choose the channel containing the continuous microphone signal. A digital trigger channel does not contain speech audio.

The converter reads the entire selected channel, scales it by a single constant for playback, and saves it as mono 16-bit PCM WAV. It does not crop, filter, or resample the data. It reads in blocks to avoid loading all EEG channels into memory. It creates a new export folder and never overwrites an earlier export.

The output folder is printed in the prompt. By default, it is under a praat_export folder beside your recording. For a recording named participant01, the files are:

| File | Contents |
| --- | --- |
| participant01.wav | Full microphone channel |
| participant01.TextGrid | Populated triggers point tier, empty speech_onset point tier, and empty transcription interval tier |
| participant01_markers.tsv | Every original marker, including sample position, type, code, size, channel, date, and computed time |
| participant01_export.json | Source filenames, sample rate, sample count, normalization, and conversion details |

Trigger onset times are calculated as (original sample position - 1) / sampling rate. Markers occurring at the same sample appear together in one TextGrid point; each marker remains its own row in the TSV. Interval markers appear by their onset in the point tier; their duration remains in the TSV. New Segment markers are retained. Times follow the stored sample timeline, rather than reconstructing wall-clock gaps across recording pauses.

The converter stops if it cannot find the linked files, if a marker is outside the data, or if the sampling rate cannot be stored exactly as an integer WAV rate. Resolve that issue before annotating.

TextGrid trigger labels now show compact codes such as S 200 and S 73, without
the Mk identifier or Stimulus prefix. Marker IDs and full descriptions remain
in the marker TSV and original .vmrk. Non-code startup/comment points keep their
original times with blank labels. The shortened-label grid for the current
recording's watched file is 072i_transcription.TextGrid, whose trigger labels
were shortened with a backup while preserving manual annotations.

## 4. Open the sound and existing triggers in Praat

In the Praat Objects window, use Open > Read from file... to open the exported WAV. For a long recording, use Open > Open long sound file... instead.

Use Open > Read from file... again to open the matching TextGrid. Hold Ctrl and select both the Sound (or LongSound) and TextGrid objects, then click View & Edit.

The editor should show the microphone waveform and three tiers: triggers, speech_onset, and transcription. The first two are point tiers; transcription is an interval tier. The triggers tier is already populated. Use this existing TextGrid; creating a fresh empty one would omit the imported triggers.

## 5. Check the export before annotating

Inspect and listen to several responses near the beginning, middle, and end. Confirm that the selected channel actually contains the participant's speech. Low EEG sampling rates may make playback sound muffled and limit acoustic detail; changing the declared WAV rate to make it sound clearer would change the timing.

Compare at least one marker code and position with the original .vmrk or BrainVision Analyzer, using the sampling-rate formula above. Check that the output duration in the JSON matches the WAV duration and equals sample count / sampling rate.

A stimulus trigger does not have to coincide with speech onset: the response normally follows it. A StimTrak threshold trigger can also occur after the earliest acoustic evidence because of its threshold. Preserve those existing trigger positions and place the independently judged speech onset in the speech_onset tier.

If you selected the wrong channel, rerun the converter and choose the correct microphone channel. It will create another export folder.

## 6. Annotate each speech onset

Find the relevant trial trigger, then select a region spanning the response and zoom to that selection. Listen to a short stretch containing the start of the response. Use the waveform and, when available and useful, the spectrogram to locate the onset.

Use your study's agreed onset definition consistently. For an acoustic-onset definition, place the point at the earliest reliable acoustic evidence of the intended spoken response. Depending on the first sound, this can be vowel periodicity, frication, or a stop release. Do not automatically use the first voiced portion for every word, because responses may begin with an unvoiced consonant. Handle initial breaths, hesitations, false starts, and uncertain cases according to the study protocol. A silent initial stop closure generally cannot be identified reliably from audio alone.

Click the speech_onset tier, position the cursor at the chosen time, and press Enter (or use the Boundary/Point menu command to add a point). Select the point and enter s for a clear onset or u for an uncertain onset. Each point's timestamp is saved independently; trial IDs can be assigned later by matching to the relevant preceding trigger. Do not place an invented onset for a missing response.

Leave the imported triggers at their recorded positions. Zoom back out and repeat for the next trial. Review difficult cases and a sample of the completed annotations for consistency.

To transcribe sentences, select the transcription tier and insert boundaries at the beginning and end of each spoken sentence. Click inside the resulting sentence interval and type its full transcription into the text field above the waveform. Leave intervals containing silence empty. Transcription intervals and speech-onset points are stored separately in the same TextGrid.

### Consult PsychoPy when speech is unclear

The local `trial_reference` interface now brings the participant picture,
playable PsychoPy full-session context and EEG trigger list together. Launch it with
`START_WORKFLOW.cmd`. Search
by S code, Mk marker ID, trial number or a time in seconds from Praat. All shown
trigger times are original EEG times; the audio player uses its own file time
and is for listening only. Playback uses the full recording from 3 seconds before
the trial starts until 3 seconds after it finishes, located using PsychoPy's
recording sample indices. The original short WAV name remains visible for reference.
See `trial_reference/README.md` for mapping checks
and configuring another participant. No original audio or annotations are edited.

Keep the StimTrak Sound/LongSound and its TextGrid as the annotation editor.
Consult the full-session PsychoPy window in the web interface, not the poorly
cut short WAV. Use the trial identifier, item and response to confirm the match.

Use the clearer recording to determine what was spoken, which sound starts the response, or whether a breath/hesitation is present. Then return to the StimTrak waveform and place the onset on its timeline. Do not copy a time from PsychoPy or assume the two files have the same clock, duration or offset.

If the onset still cannot be identified reliably in StimTrak, mark the trial Need help in the interface and review it under your study protocol. Do not manufacture a precise timestamp from an unverified PsychoPy offset. Every point in speech_onset is counted, even one labelled u: that label does not automatically exclude an uncertain onset. Use s for a clear onset; annotate sentence text in transcription as before.

## 7. Save and resume

In the editor, use File > Save TextGrid as text file... and save to the exact
watched annotation filename shown under Praat files in the interface. New imports
use participant01_annotations.TextGrid and keep participant01.TextGrid as an empty
baseline. Current 072i uses 072i_transcription.TextGrid. Do not save under another
name unless you intentionally update its recording config.

To resume, open the exported WAV and that same watched annotation TextGrid
together. Keep original BrainVision files and all workflow/export files. A point
added in Praat does not change the original .vmrk; use the analysis CSV for the
marked onset times and latencies.

For a continuous export, response latency in milliseconds is 1000 * (speech onset time - relevant stimulus trigger time). Match the correct trial and trigger type before computing it.

Both times are now on the original EEG sample timeline, so no cross-recording time conversion is needed. The same converter and annotation steps can be repeated for each recording after the remaining experiment data are downloaded.

## References

- BrainVision file structure: https://pressrelease.brainproducts.com/recorder-tips-2/
- BrainVision marker fields and timing: https://pressrelease.brainproducts.com/markers/
- BrainVision format specification: https://www.brainproducts.com/download/specification-of-brainvision-core-data-format-1-0/
- MNE BrainVision reader: https://mne.tools/stable/generated/mne.io.read_raw_brainvision.html
- Praat annotation workflow: https://www.fon.hum.uva.nl/praat/manual/Intro_7__Annotation.html
- Praat TextGrid editing: https://www.fon.hum.uva.nl/praat/manual/TextGridEditor.html

Verification: eight converter checks and 52 annotation/library/server/flag checks passed. A complete import using the installed MNE reader on the real 072i EEG produced a WAV byte-for-byte identical to the existing AUX export, validated all 130 PsychoPy segments, and left the user's saved annotations unchanged. Playwright verified playback with context, saved Praat updates, invalid-grid export rejection, independent flags, recording import/switching, combined export and desktop/tablet/mobile layouts. Earlier Praat 7.0.02 checks verified compact labels without changing point times or other tiers. These checks validate the pipeline, not the microphone's acoustic quality or an annotator's onset criterion.
