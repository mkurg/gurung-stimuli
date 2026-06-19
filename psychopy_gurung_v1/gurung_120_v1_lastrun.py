#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2025.2.4),
    on June 19, 2026, at 19:25
If you publish work using this script the most relevant publication is:

    Peirce J, Gray JR, Simpson S, MacAskill M, Höchenberger R, Sogo H, Kastman E, Lindeløv JK. (2019)
        PsychoPy2: Experiments in behavior made easy Behav Res 51: 195.
        https://doi.org/10.3758/s13428-018-01193-y

"""

# --- Import packages ---
from psychopy import locale_setup
from psychopy import prefs
from psychopy import plugins
plugins.activatePlugins()
from psychopy import sound, gui, visual, core, data, event, logging, clock, colors, layout, hardware
from psychopy.tools import environmenttools
from psychopy.constants import (
    NOT_STARTED, STARTED, PLAYING, PAUSED, STOPPED, STOPPING, FINISHED, PRESSED,
    RELEASED, FOREVER, priority
)

import numpy as np  # whole numpy lib is available, prepend 'np.'
from numpy import (sin, cos, tan, log, log10, pi, average,
                   sqrt, std, deg2rad, rad2deg, linspace, asarray)
from numpy.random import random, randint, normal, shuffle, choice as randchoice
import os  # handy system and path functions
import sys  # to get file system encoding

from psychopy.hardware import keyboard

# --- Setup global variables (available in all functions) ---
# create a device manager to handle hardware (keyboards, mice, mirophones, speakers, etc.)
deviceManager = hardware.DeviceManager()
# ensure that relative paths start from the same directory as this script
_thisDir = os.path.dirname(os.path.abspath(__file__))
# store info about the experiment session
psychopyVersion = '2025.2.4'
expName = 'gurung_120_v1'  # from the Builder filename that created this script
expVersion = ''
# a list of functions to run when the experiment ends (starts off blank)
runAtExit = []
# information about this experiment
expInfo = {
    'participant': f"{randint(0, 999999):06.0f}",
    'session': '001',
    'date|hid': data.getDateStr(),
    'expName|hid': expName,
    'expVersion|hid': expVersion,
    'psychopyVersion|hid': psychopyVersion,
}

# --- Define some variables which will change depending on pilot mode ---
'''
To run in pilot mode, either use the run/pilot toggle in Builder, Coder and Runner,
or run the experiment with `--pilot` as an argument. To change what pilot
#mode does, check out the 'Pilot mode' tab in preferences.
'''
# work out from system args whether we are running in pilot mode
PILOTING = core.setPilotModeFromArgs()
# start off with values from experiment settings
_fullScr = True
_winSize = (1200, 800)
# if in pilot mode, apply overrides according to preferences
if PILOTING:
    # force windowed mode
    if prefs.piloting['forceWindowed']:
        _fullScr = False
        # set window size
        _winSize = prefs.piloting['forcedWindowSize']
    # replace default participant ID
    if prefs.piloting['replaceParticipantID']:
        expInfo['participant'] = 'pilot'

def showExpInfoDlg(expInfo):
    """
    Show participant info dialog.
    Parameters
    ==========
    expInfo : dict
        Information about this experiment.

    Returns
    ==========
    dict
        Information about this experiment.
    """
    # show participant info dialog
    dlg = gui.DlgFromDict(
        dictionary=expInfo, sortKeys=False, title=expName, alwaysOnTop=True
    )
    if dlg.OK == False:
        core.quit()  # user pressed cancel
    # return expInfo
    return expInfo


def setupData(expInfo, dataDir=None):
    """
    Make an ExperimentHandler to handle trials and saving.

    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    dataDir : Path, str or None
        Folder to save the data to, leave as None to create a folder in the current directory.
    Returns
    ==========
    psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    """
    # remove dialog-specific syntax from expInfo
    for key, val in expInfo.copy().items():
        newKey, _ = data.utils.parsePipeSyntax(key)
        expInfo[newKey] = expInfo.pop(key)

    # data file name stem = absolute path + name; later add .psyexp, .csv, .log, etc
    if dataDir is None:
        dataDir = _thisDir
    filename = u'data/%s_%s_%s' % (expInfo['participant'], expName, expInfo['date'])
    # make sure filename is relative to dataDir
    if os.path.isabs(filename):
        dataDir = os.path.commonprefix([dataDir, filename])
        filename = os.path.relpath(filename, dataDir)

    # an ExperimentHandler isn't essential but helps with data saving
    thisExp = data.ExperimentHandler(
        name=expName, version=expVersion,
        extraInfo=expInfo, runtimeInfo=None,
        originPath='C:\\Users\\Sofya\\Documents\\Discourse part\\gurung-stimuli\\psychopy_gurung_v1\\gurung_120_v1_lastrun.py',
        savePickle=True, saveWideText=True,
        dataFileName=dataDir + os.sep + filename, sortColumns='time'
    )
    thisExp.setPriority('thisRow.t', priority.CRITICAL)
    thisExp.setPriority('expName', priority.LOW)
    # return experiment handler
    return thisExp


def setupLogging(filename):
    """
    Setup a log file and tell it what level to log at.

    Parameters
    ==========
    filename : str or pathlib.Path
        Filename to save log file and data files as, doesn't need an extension.

    Returns
    ==========
    psychopy.logging.LogFile
        Text stream to receive inputs from the logging system.
    """
    # set how much information should be printed to the console / app
    if PILOTING:
        logging.console.setLevel(
            prefs.piloting['pilotConsoleLoggingLevel']
        )
    else:
        logging.console.setLevel('warning')
    # save a log file for detail verbose info
    logFile = logging.LogFile(filename+'.log')
    if PILOTING:
        logFile.setLevel(
            prefs.piloting['pilotLoggingLevel']
        )
    else:
        logFile.setLevel(
            logging.getLevel('info')
        )

    return logFile


def setupWindow(expInfo=None, win=None):
    """
    Setup the Window

    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    win : psychopy.visual.Window
        Window to setup - leave as None to create a new window.

    Returns
    ==========
    psychopy.visual.Window
        Window in which to run this experiment.
    """
    if PILOTING:
        logging.debug('Fullscreen settings ignored as running in pilot mode.')

    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=-1,
            winType='pyglet', allowGUI=False, allowStencil=False,
            monitor='testMonitor', color=(1.0000, 1.0000, 1.0000), colorSpace='rgb',
            backgroundImage='', backgroundFit='none',
            blendMode='avg', useFBO=True,
            units='height',
            checkTiming=False  # we're going to do this ourselves in a moment
        )
    else:
        # if we have a window, just set the attributes which are safe to set
        win.color = (1.0000, 1.0000, 1.0000)
        win.colorSpace = 'rgb'
        win.backgroundImage = ''
        win.backgroundFit = 'none'
        win.units = 'height'
    if expInfo is not None:
        # get/measure frame rate if not already in expInfo
        if win._monitorFrameRate is None:
            win._monitorFrameRate = win.getActualFrameRate(infoMsg='Attempting to measure frame rate of screen, please wait...')
        expInfo['frameRate'] = win._monitorFrameRate
    win.hideMessage()
    if PILOTING:
        # show a visual indicator if we're in piloting mode
        if prefs.piloting['showPilotingIndicator']:
            win.showPilotingIndicator()
        # always show the mouse in piloting mode
        if prefs.piloting['forceMouseVisible']:
            win.mouseVisible = True

    return win


def setupDevices(expInfo, thisExp, win):
    """
    Setup whatever devices are available (mouse, keyboard, speaker, eyetracker, etc.) and add them to
    the device manager (deviceManager)

    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    win : psychopy.visual.Window
        Window in which to run this experiment.
    Returns
    ==========
    bool
        True if completed successfully.
    """
    # --- Setup input devices ---
    ioConfig = {}
    ioSession = ioServer = eyetracker = None

    # store ioServer object in the device manager
    deviceManager.ioServer = ioServer

    # create a default keyboard (e.g. to check for escape)
    if deviceManager.getDevice('defaultKeyboard') is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='ptb'
        )
    # return True if completed successfully
    return True

def pauseExperiment(thisExp, win=None, timers=[], currentRoutine=None):
    """
    Pause this experiment, preventing the flow from advancing to the next routine until resumed.

    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    timers : list, tuple
        List of timers to reset once pausing is finished.
    currentRoutine : psychopy.data.Routine
        Current Routine we are in at time of pausing, if any. This object tells PsychoPy what Components to pause/play/dispatch.
    """
    # if we are not paused, do nothing
    if thisExp.status != PAUSED:
        return

    # start a timer to figure out how long we're paused for
    pauseTimer = core.Clock()
    # pause any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.pause()
    # make sure we have a keyboard
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        defaultKeyboard = deviceManager.addKeyboard(
            deviceClass='keyboard',
            deviceName='defaultKeyboard',
            backend='PsychToolbox',
        )
    # run a while loop while we wait to unpause
    while thisExp.status == PAUSED:
        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=['escape']):
            endExperiment(thisExp, win=win)
        # dispatch messages on response components
        if currentRoutine is not None:
            for comp in currentRoutine.getDispatchComponents():
                comp.device.dispatchMessages()
        # sleep 1ms so other threads can execute
        clock.time.sleep(0.001)
    # if stop was requested while paused, quit
    if thisExp.status == FINISHED:
        endExperiment(thisExp, win=win)
    # resume any playback components
    if currentRoutine is not None:
        for comp in currentRoutine.getPlaybackComponents():
            comp.play()
    # reset any timers
    for timer in timers:
        timer.addTime(-pauseTimer.getTime())


def run(expInfo, thisExp, win, globalClock=None, thisSession=None):
    """
    Run the experiment flow.

    Parameters
    ==========
    expInfo : dict
        Information about this experiment, created by the `setupExpInfo` function.
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    psychopy.visual.Window
        Window in which to run this experiment.
    globalClock : psychopy.core.clock.Clock or None
        Clock to get global time from - supply None to make a new one.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    # mark experiment as started
    thisExp.status = STARTED
    # update experiment info
    expInfo['date'] = data.getDateStr()
    expInfo['expName'] = expName
    expInfo['expVersion'] = expVersion
    expInfo['psychopyVersion'] = psychopyVersion
    # make sure window is set to foreground to prevent losing focus
    win.winHandle.activate()
    # make sure variables created by exec are available globally
    exec = environmenttools.setExecEnvironment(globals())
    # get device handles from dict of input devices
    ioServer = deviceManager.ioServer
    # get/create a default keyboard (e.g. to check for escape)
    defaultKeyboard = deviceManager.getDevice('defaultKeyboard')
    if defaultKeyboard is None:
        deviceManager.addDevice(
            deviceClass='keyboard', deviceName='defaultKeyboard', backend='PsychToolbox'
        )
    eyetracker = deviceManager.getDevice('eyetracker')
    # make sure we're running in the directory for this experiment
    os.chdir(_thisDir)
    # get filename from ExperimentHandler for convenience
    filename = thisExp.dataFileName
    frameTolerance = 0.001  # how close to onset before 'same' frame
    endExpNow = False  # flag for 'escape' or other condition => quit the exp
    # get frame duration from frame rate in expInfo
    if 'frameRate' in expInfo and expInfo['frameRate'] is not None:
        frameDur = 1.0 / round(expInfo['frameRate'])
    else:
        frameDur = 1.0 / 60.0  # could not measure, so guess

    # Start Code - component code to be run after the window creation

    # --- Initialize components for Routine "Instructions" ---
    Instructions_keep_alive = visual.ImageStim(
        win=win,
        name='Instructions_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)
    # Run 'Begin Experiment' code from instructions_code

    from pathlib import Path
    import csv
    import gc
    import queue
    import random as _gurung_random
    import threading

    try:
        from psychopy.hardware.speaker import SpeakerDevice
    except Exception as _gurung_speaker_import_error:
        SpeakerDevice = None
        print("SpeakerDevice import failed:", _gurung_speaker_import_error)

    try:
        import numpy as _gurung_np
        import sounddevice as _gurung_sd
        import soundfile as _gurung_sf
        G_RECORDING_AVAILABLE = True
    except Exception as _gurung_recording_error:
        G_RECORDING_AVAILABLE = False
        print("Audio recording is unavailable:", _gurung_recording_error)

    try:
        from PIL import Image as _gurung_Image
        from PIL import ImageOps as _gurung_ImageOps
    except Exception as _gurung_image_import_error:
        _gurung_Image = None
        _gurung_ImageOps = None
        print("Image metadata reading is unavailable:", _gurung_image_import_error)

    G_ROOT = Path(_thisDir)
    G_DATA_DIR = G_ROOT / "data"
    G_RECORDINGS_ROOT = G_ROOT / "recordings"
    G_RECORDINGS_DIR = None
    G_DEBUG_LOG = G_ROOT / "debug_gurung_runtime.log"
    G_DATA_DIR.mkdir(exist_ok=True)
    G_RECORDINGS_ROOT.mkdir(exist_ok=True)
    G_IMAGE_ASPECT = 2.0 / 3.0
    G_SEQUENCE_SIDE_STEPS = 2
    G_SEQUENCE_X_MARGIN = 0.02
    G_SEQUENCE_Y_MARGIN = 0.05
    G_SEQUENCE_GAP_RATIO = 0.12
    G_SEQUENCE_SIZE_COUNT = 5
    G_SEQUENCE_JITTER_POSITIONS = (
        (-0.035, -0.018),
        (-0.012, -0.018),
        (0.012, -0.018),
        (0.035, -0.018),
        (-0.035, 0.018),
        (-0.012, 0.018),
        (0.012, 0.018),
        (0.035, 0.018),
    )
    G_SEQUENCE_JITTER_STATE = {"bag": []}
    G_ARROW_MAX_SIZE = 0.045
    G_MAIN_TRIAL_INDEX = 0
    G_PRACTICE_TRIAL_INDEX = 0
    G_SPEAKER = None
    G_FULLSCREEN_CACHE = {"stim": None}
    G_BETWEEN_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}
    G_BETWEEN_STATE = {"images": [], "index": 0}
    G_MAIN_RUNTIME_STATE = {"prepared": False, "files": []}
    G_AUDIO_PROBE_FILES = (
        "Audio/tsakyali.wav",
        "Audio/bucketdog_noerg.wav",
        "Audio/chickencorn_erg.wav",
    )
    G_AUDIO_PROBE_RATE = 0.10
    G_AUDIO_PROBE_LOCK_SEC = 10
    G_AUDIO_SPEAKER_IMAGE = "Stimuli/sound.png"
    G_AUDIO_SPEAKER_SIZE = (0.22, 0.22)
    G_RECORDING_STOP_GRACE_SEC = 0.6
    G_MAIN_BLOCK_SIZE = 40
    G_PRACTICE_TRIAL_COUNT = 10
    G_PRACTICE_PICTURE_AUDIO = {
        1: {
            0: "Audio/tsakyali.wav",
            1: "Audio/bucketdog_noerg.wav",
            2: "Audio/chickencorn_erg.wav",
        },
        2: {
            0: "Audio/tsakyali.wav",
            1: "Audio/bucketdog_noerg.wav",
            2: "Audio/chickencorn_erg.wav",
        },
    }
    G_PRACTICE_AFTER_TRIAL_AUDIO = {
        2: "Audio/practice_end.wav",
        4: "Audio/tsakyali.wav",
        7: "Audio/bucketdog_noerg.wav",
        10: "Audio/chickencorn_erg.wav",
    }
    G_PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS = {2}


    def g_log(message):
        text = f"{core.getTime():.3f} {message}"
        print(text)
        try:
            with G_DEBUG_LOG.open("a", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except Exception:
            pass

    try:
        event.globalKeys.add(key="escape", func=core.quit, name="gurung_escape_quit")
    except Exception as _gurung_global_key_error:
        g_log(f"Global escape key was not registered: {_gurung_global_key_error}")


    def g_is_blank(value):
        if value is None:
            return True
        text = str(value).strip()
        return text == "" or text.lower() in {"none", "nan", "null"}


    def g_text(value):
        if g_is_blank(value):
            return ""
        return str(value).strip()


    def g_float(value, default=0.0):
        if g_is_blank(value):
            return default
        try:
            return float(value)
        except Exception:
            return default


    def g_practice_picture_audio(trial_index, segment_index):
        trial_audio = G_PRACTICE_PICTURE_AUDIO.get(trial_index, {})
        return trial_audio.get(segment_index, "")


    def g_practice_pre_picture_audio(trial_index, segment_index, image_count):
        if trial_index not in G_PRACTICE_PICTURE_AUDIO and segment_index == image_count - 1:
            return "Audio/tsakyali.wav"
        return ""


    def g_int(value, default=0):
        if g_is_blank(value):
            return default
        try:
            return int(float(value))
        except Exception:
            return default


    def g_path(value):
        value = g_text(value)
        if not value:
            return ""
        path = Path(value)
        if path.is_absolute():
            return str(path)
        return str(G_ROOT / path)


    def g_window_aspect(win):
        try:
            return max(float(win.size[0]) / float(win.size[1]), 1.0)
        except Exception:
            return 1.5


    def g_image_aspect(path):
        if _gurung_Image is None:
            return None
        try:
            with _gurung_Image.open(path) as image:
                if _gurung_ImageOps is not None:
                    image = _gurung_ImageOps.exif_transpose(image)
                width, height = image.size
            if width > 0 and height > 0:
                return float(width) / float(height)
        except Exception as err:
            g_log(f"image_aspect_warning {path}: {err}")
        return None


    def g_fullscreen_size(win, image_path):
        screen_aspect = g_window_aspect(win)
        image_aspect = g_image_aspect(image_path)
        if not image_aspect:
            return (screen_aspect, 1.0)
        if image_aspect >= screen_aspect:
            return (screen_aspect, screen_aspect / image_aspect)
        return (image_aspect, 1.0)


    def g_fullscreen_image(win, image_value):
        path = g_path(image_value)
        old_stim = G_FULLSCREEN_CACHE.get("stim")
        if old_stim is not None:
            try:
                old_stim.clearTextures()
            except Exception:
                pass
        g_log(f"load_fullscreen_image {path}")
        stim = visual.ImageStim(
            win,
            image=path,
            pos=(0, 0),
            size=g_fullscreen_size(win, path),
            interpolate=True,
        )
        G_FULLSCREEN_CACHE["stim"] = stim
        return stim


    def g_audio_speaker_image(win):
        return visual.ImageStim(
            win,
            image=g_path(G_AUDIO_SPEAKER_IMAGE),
            pos=(0, 0),
            size=G_AUDIO_SPEAKER_SIZE,
            interpolate=True,
        )


    def g_release_fullscreen_image(stim):
        g_release_stims([stim])
        if G_FULLSCREEN_CACHE.get("stim") is stim:
            G_FULLSCREEN_CACHE["stim"] = None


    def g_init_between_images():
        between_dir = G_ROOT / "BetweenTrials"
        practice_images = set()
        try:
            for row in data.importConditions("Conds/practice.csv"):
                image_value = g_text(row.get("between_image", "")).replace("\\", "/")
                if image_value:
                    practice_images.add(image_value)
        except Exception as err:
            g_log(f"Could not reserve practice between-trial images: {err}")
        images = []
        try:
            for path in sorted(between_dir.iterdir()):
                if path.is_file() and path.suffix.lower() in G_BETWEEN_IMAGE_EXTS:
                    image_value = f"BetweenTrials/{path.name}"
                    if image_value not in practice_images:
                        images.append(image_value)
        except Exception as err:
            raise RuntimeError(f"Could not list between-trial images in {between_dir}: {err}")
        if not images:
            raise RuntimeError(f"No between-trial images found in {between_dir}")
        _gurung_random.shuffle(images)
        G_BETWEEN_STATE["images"] = images
        G_BETWEEN_STATE["index"] = 0
        g_log(f"runtime_between_images_shuffled count={len(images)} reserved_practice={len(practice_images)}")


    def g_next_between_image():
        images = G_BETWEEN_STATE.get("images") or []
        index = int(G_BETWEEN_STATE.get("index") or 0)
        if index >= len(images):
            raise RuntimeError(f"No unused between-trial images remain: used {index}, available {len(images)}")
        image_value = images[index]
        G_BETWEEN_STATE["index"] = index + 1
        g_log(f"runtime_between_image {index + 1}/{len(images)} {image_value}")
        return image_value


    def g_prepare_runtime_main_blocks():
        if G_MAIN_RUNTIME_STATE.get("prepared"):
            return
        rows = list(data.importConditions("Conds/main_all_120.csv"))
        if not rows:
            raise RuntimeError("No main trials found in Conds/main_all_120.csv")
        _gurung_random.shuffle(rows)
        g_assign_runtime_audio_probes(rows)
        fieldnames = list(rows[0].keys())
        block_files = []
        block_sizes = []
        for block_index in range(3):
            block_rows = rows[block_index * 40 : (block_index + 1) * 40]
            block_sizes.append(len(block_rows))
            block_path = G_DATA_DIR / f"runtime_main_block{block_index + 1}.csv"
            with block_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore", lineterminator="\n")
                writer.writeheader()
                for row in block_rows:
                    writer.writerow({field: "" if g_is_blank(row.get(field, "")) else row.get(field, "") for field in fieldnames})
            block_files.append(str(block_path))
        G_MAIN_RUNTIME_STATE["files"] = block_files
        G_MAIN_RUNTIME_STATE["prepared"] = True
        g_log(f"runtime_main_sequences_shuffled count={len(rows)} block_sizes={block_sizes}")


    def g_assign_runtime_audio_probes(rows):
        for row in rows:
            row["audio_probe"] = "0"
            row["between_audio"] = ""
            row["between_audio_lock_sec"] = "0"
        probe_count = int(round(len(rows) * G_AUDIO_PROBE_RATE))
        if probe_count <= 0:
            return
        if probe_count % len(G_AUDIO_PROBE_FILES):
            raise RuntimeError(
                f"Audio probe count {probe_count} cannot be split equally across {len(G_AUDIO_PROBE_FILES)} files"
            )
        block_start_indices = set(range(0, len(rows), G_MAIN_BLOCK_SIZE))
        candidate_indices = [index for index in range(len(rows)) if index not in block_start_indices]
        if probe_count > len(candidate_indices):
            raise RuntimeError(f"Need {probe_count} audio probe slots, only {len(candidate_indices)} are available")
        for audio_value in G_AUDIO_PROBE_FILES:
            audio_path = Path(g_path(audio_value))
            if not audio_path.is_file():
                raise RuntimeError(f"Missing audio probe file: {audio_path}")
        per_audio_count = probe_count // len(G_AUDIO_PROBE_FILES)
        audio_bag = []
        for audio_value in G_AUDIO_PROBE_FILES:
            audio_bag.extend([audio_value] * per_audio_count)
        _gurung_random.shuffle(audio_bag)
        probe_indices = _gurung_random.sample(candidate_indices, probe_count)
        for row_index, audio_value in zip(probe_indices, audio_bag):
            rows[row_index]["audio_probe"] = "1"
            rows[row_index]["between_audio"] = audio_value
            rows[row_index]["between_audio_lock_sec"] = str(G_AUDIO_PROBE_LOCK_SEC)
        counts = {audio_value: audio_bag.count(audio_value) for audio_value in G_AUDIO_PROBE_FILES}
        g_log(f"runtime_main_audio_probes count={probe_count} counts={counts} block_start_audio=0")


    def g_runtime_main_block_file(block_index):
        if not G_MAIN_RUNTIME_STATE.get("prepared"):
            g_prepare_runtime_main_blocks()
        files = G_MAIN_RUNTIME_STATE.get("files") or []
        index = int(block_index) - 1
        if index < 0 or index >= len(files):
            raise RuntimeError(f"Invalid main block index: {block_index}")
        return files[index]


    def g_choose_speaker():
        if SpeakerDevice is None:
            return None
        try:
            devices = SpeakerDevice.getAvailableDevices()
        except Exception as err:
            g_log(f"Could not list speaker devices: {err}")
            return None
        names = [g_text(device.get("deviceName") or device.get("name")) for device in devices]
        g_log(f"Available speaker devices: {names}")
        virtual_terms = ("blackhole", "soundflower", "loopback", "aggregate", "zoom", "teams")
        preferred = []
        fallback = []
        for device in devices:
            name = g_text(device.get("deviceName") or device.get("name"))
            if not name:
                continue
            if any(term in name.lower() for term in virtual_terms):
                fallback.append(name)
            else:
                preferred.append(name)
        for name in preferred + fallback:
            try:
                speaker = SpeakerDevice(name=name, latencyClass=0)
                g_log(f"Using speaker device: {speaker.name}")
                return speaker
            except Exception as err:
                g_log(f"Could not open speaker {name!r}: {err}")
        g_log("No usable speaker found; PsychoPy will use its default audio device.")
        return None


    G_SPEAKER = g_choose_speaker()
    g_init_between_images()
    g_prepare_runtime_main_blocks()


    def g_safe(value):
        text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
        while "__" in text:
            text = text.replace("__", "_")
        return text.strip("._") or "item"


    def g_session_recordings_dir():
        participant = g_safe(expInfo.get("participant", "participant"))
        date_value = g_safe(expInfo.get("date") or expInfo.get("date|hid") or data.getDateStr())
        folder = G_RECORDINGS_ROOT / f"{participant}_{date_value}"
        folder.mkdir(parents=True, exist_ok=True)
        expInfo["recordings_dir"] = str(folder)
        g_log(f"recordings_dir {folder}")
        return folder


    def g_roles_and_paths():
        roles = []
        paths = []
        for idx in range(1, 5):
            image_value = globals().get(f"img{idx}", "")
            role_value = globals().get(f"img{idx}_role", f"img{idx}")
            if not g_is_blank(image_value):
                paths.append(g_path(image_value))
                roles.append(g_text(role_value) or f"img{idx}")
        return roles, paths


    def g_target_index(roles):
        for target_role in ("tr_target", "it_target"):
            if target_role in roles:
                return roles.index(target_role)
        return (len(roles) - 1) / 2


    def g_next_sequence_jitter():
        bag = G_SEQUENCE_JITTER_STATE.get("bag")
        if not bag:
            bag = list(G_SEQUENCE_JITTER_POSITIONS)
            _gurung_random.shuffle(bag)
            G_SEQUENCE_JITTER_STATE["bag"] = bag
        return bag.pop()


    def g_sequence_layout(win, roles):
        sequence_count = max(1, len(roles))
        size_count = max(G_SEQUENCE_SIZE_COUNT, sequence_count)
        jitter_x_max = max(abs(pos[0]) for pos in G_SEQUENCE_JITTER_POSITIONS)
        jitter_y_max = max(abs(pos[1]) for pos in G_SEQUENCE_JITTER_POSITIONS)
        horizontal_room = max(0.1, g_window_aspect(win) - (2 * (G_SEQUENCE_X_MARGIN + jitter_x_max)))
        vertical_room = max(0.1, 1.0 - (2 * (G_SEQUENCE_Y_MARGIN + jitter_y_max)))
        width_from_horizontal = horizontal_room / (size_count + ((size_count - 1) * G_SEQUENCE_GAP_RATIO))
        image_height = min(vertical_room, width_from_horizontal / G_IMAGE_ASPECT)
        image_width = image_height * G_IMAGE_ASPECT
        gap = image_width * G_SEQUENCE_GAP_RATIO
        step = image_width + gap
        row_center = (len(roles) - 1) / 2.0
        jitter_x, jitter_y = g_next_sequence_jitter()
        positions = [((idx - row_center) * step + jitter_x, jitter_y) for idx in range(len(roles))]
        arrow_size = min(G_ARROW_MAX_SIZE, max(0.02, gap * 0.9))
        return (image_width, image_height), positions, (arrow_size, arrow_size), (jitter_x, jitter_y)


    def g_make_sequence(win, roles, paths):
        image_size, positions, arrow_size, jitter = g_sequence_layout(win, roles)
        g_log(f"make_sequence roles={roles} jitter={jitter} paths={paths}")
        images = []
        for path, pos in zip(paths, positions):
            images.append(visual.ImageStim(win, image=path, pos=pos, size=image_size, interpolate=True))
        arrows = []
        for left, right in zip(positions, positions[1:]):
            arrows.append(g_make_arrow(win, ((left[0] + right[0]) / 2, (left[1] + right[1]) / 2), arrow_size))
        return images, arrows


    def g_make_arrow(win, pos, size):
        arrow_width = float(size[0])
        arrow_height = float(size[1])
        shaft_half_height = arrow_height * 0.16
        head_back_x = arrow_width * 0.08
        left_x = -arrow_width / 2.0
        right_x = arrow_width / 2.0
        arrow_color = (-0.25, -0.25, -0.25)
        vertices = [
            (left_x, -shaft_half_height),
            (head_back_x, -shaft_half_height),
            (head_back_x, -arrow_height / 2.0),
            (right_x, 0),
            (head_back_x, arrow_height / 2.0),
            (head_back_x, shaft_half_height),
            (left_x, shaft_half_height),
        ]
        return visual.ShapeStim(
            win,
            vertices=vertices,
            pos=pos,
            fillColor=arrow_color,
            lineColor=arrow_color,
            closeShape=True,
        )


    def g_release_stims(*groups):
        for group in groups:
            if not group:
                continue
            for stim in group:
                try:
                    clear_textures = getattr(stim, "clearTextures", None)
                    if clear_textures is not None:
                        clear_textures()
                except Exception as err:
                    g_log(f"stim_release_warning {err}")
        gc.collect()


    def g_draw_sequence(images, arrows, reveal_count):
        win.color = "white"
        for idx in range(reveal_count):
            images[idx].draw()
        for idx in range(max(0, reveal_count - 1)):
            arrows[idx].draw()


    def g_play_audio(path_value):
        path = g_path(path_value)
        if not path:
            return None
        g_log(f"play_audio {path}")
        if G_SPEAKER is not None:
            audio = sound.Sound(path, speaker=G_SPEAKER)
        else:
            audio = sound.Sound(path)
        audio.play()
        return audio


    class GRecorder:
        def __init__(self, root):
            self.root = Path(root)
            self.root.mkdir(exist_ok=True)
            self.stream = None
            self.segments = []
            self.current_segment = None
            self.lock = threading.Lock()
            self.write_queue = queue.Queue()
            self.close_event = threading.Event()
            self.writer = threading.Thread(target=self._writer_loop, daemon=True)
            self.writer.start()
            self.closer = threading.Thread(target=self._closer_loop, daemon=True)
            self.closer.start()

        def start(self, stem):
            self.stop()
            if not G_RECORDING_AVAILABLE:
                return ""
            self._ensure_stream()
            path = self.root / f"{g_safe(stem)}.wav"
            segment = {"path": path, "frames": [], "stop_after": None}
            with self.lock:
                self.segments.append(segment)
                self.current_segment = segment
            g_log(f"rec_segment_start {path}")
            return str(path)

        def _ensure_stream(self):
            if self.stream is not None:
                return

            def callback(indata, frames, time_info, status):
                if status:
                    g_log(f"rec_callback_status {status}")
                block = indata.copy()
                with self.lock:
                    for segment in self.segments:
                        segment["frames"].append(block)

            g_log("rec_stream_open_start")
            self.stream = _gurung_sd.InputStream(
                samplerate=48000,
                channels=1,
                dtype="float32",
                callback=callback,
            )
            self.stream.start()
            g_log("rec_stream_open_done")

        def stop(self, grace_sec=None):
            if grace_sec is None:
                grace_sec = G_RECORDING_STOP_GRACE_SEC
            with self.lock:
                segment = self.current_segment
                self.current_segment = None
                if segment is not None:
                    segment["stop_after"] = core.getTime() + max(0.0, grace_sec)
            if segment is None:
                return ""
            path = segment["path"]
            g_log(f"rec_segment_stop_requested {path} grace={grace_sec:.3f}")
            self.close_event.set()
            if grace_sec <= 0:
                self._flush_ready_segments(force=True)
            return str(path)

        def _closer_loop(self):
            while True:
                self.close_event.wait(0.02)
                self.close_event.clear()
                self._flush_ready_segments()

        def _flush_ready_segments(self, force=False):
            now = core.getTime()
            ready = []
            with self.lock:
                remaining = []
                for segment in self.segments:
                    stop_after = segment.get("stop_after")
                    if stop_after is not None and (force or now >= stop_after):
                        ready.append(segment)
                    else:
                        remaining.append(segment)
                self.segments = remaining
            for segment in ready:
                path = segment["path"]
                frames = list(segment["frames"])
                if frames:
                    g_log(f"rec_segment_queue_write {path} frames={len(frames)}")
                    self.write_queue.put((str(path), frames))

        def _writer_loop(self):
            while True:
                item = self.write_queue.get()
                if item is None:
                    return
                path, frames = item
                try:
                    audio = _gurung_np.concatenate(frames, axis=0)
                    _gurung_sf.write(path, audio, 48000)
                    g_log(f"rec_segment_written {path}")
                except Exception as err:
                    g_log(f"rec_segment_write_failed {path}: {err}")

        def abort(self):
            self.stop(grace_sec=0.0)
            self._flush_ready_segments(force=True)
            stream = self.stream
            self.stream = None
            if stream is not None:
                def close_stream():
                    try:
                        g_log("rec_stream_abort_start")
                        stream.abort()
                        g_log("rec_stream_abort_done")
                    except Exception as err:
                        g_log(f"rec_stream_abort_failed {err}")
                    try:
                        stream.close()
                        g_log("rec_stream_close_done")
                    except Exception as err:
                        g_log(f"rec_stream_close_failed {err}")

                threading.Thread(target=close_stream, daemon=True).start()


    def g_cleanup():
        try:
            G_RECORDER.abort()
        except Exception as err:
            g_log(f"Recorder cleanup failed: {err}")
        try:
            if G_SPEAKER is not None:
                G_SPEAKER.close()
        except Exception as err:
            g_log(f"Speaker cleanup failed: {err}")


    G_RECORDINGS_DIR = g_session_recordings_dir()
    G_RECORDER = GRecorder(G_RECORDINGS_DIR)


    # --- Initialize components for Routine "PracticeTrial" ---
    PracticeTrial_keep_alive = visual.ImageStim(
        win=win,
        name='PracticeTrial_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "PracticeEnd" ---
    PracticeEnd_keep_alive = visual.ImageStim(
        win=win,
        name='PracticeEnd_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "MainTrial" ---
    MainTrial_keep_alive = visual.ImageStim(
        win=win,
        name='MainTrial_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "Break" ---
    Break_keep_alive = visual.ImageStim(
        win=win,
        name='Break_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "MainTrial" ---
    MainTrial_keep_alive = visual.ImageStim(
        win=win,
        name='MainTrial_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "Break" ---
    Break_keep_alive = visual.ImageStim(
        win=win,
        name='Break_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "MainTrial" ---
    MainTrial_keep_alive = visual.ImageStim(
        win=win,
        name='MainTrial_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # --- Initialize components for Routine "EndExperiment" ---
    EndExperiment_keep_alive = visual.ImageStim(
        win=win,
        name='EndExperiment_keep_alive',
        image='Stimuli/sound.png', mask=None, anchor='center',
        ori=0.0, pos=(0, 0), draggable=False, size=(0.01, 0.01),
        color=[1,1,1], colorSpace='rgb', opacity=0.0,
        flipHoriz=False, flipVert=False,
        texRes=128.0, interpolate=True, depth=0.0)

    # create some handy timers

    # global clock to track the time since experiment started
    if globalClock is None:
        # create a clock if not given one
        globalClock = core.Clock()
    if isinstance(globalClock, str):
        # if given a string, make a clock accoridng to it
        if globalClock == 'float':
            # get timestamps as a simple value
            globalClock = core.Clock(format='float')
        elif globalClock == 'iso':
            # get timestamps in ISO format
            globalClock = core.Clock(format='%Y-%m-%d_%H:%M:%S.%f%z')
        else:
            # get timestamps in a custom format
            globalClock = core.Clock(format=globalClock)
    if ioServer is not None:
        ioServer.syncClock(globalClock)
    logging.setDefaultClock(globalClock)
    if eyetracker is not None:
        eyetracker.enableEventReporting()
    # routine timer to track time remaining of each (possibly non-slip) routine
    routineTimer = core.Clock()
    win.flip()  # flip window to reset last flip timer
    # store the exact time the global clock started
    expInfo['expStart'] = data.getDateStr(
        format='%Y-%m-%d %Hh%M.%S.%f %z', fractionalSecondDigits=6
    )

    # --- Prepare to start Routine "Instructions" ---
    # create an object to store info about Routine Instructions
    Instructions = data.Routine(
        name='Instructions',
        components=[Instructions_keep_alive],
    )
    Instructions.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from instructions_code

    win.color = "white"
    instruction_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
    instruction_audio = g_play_audio("Audio/sequence_instr.wav")
    event.clearEvents()

    # store start times for Instructions
    Instructions.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Instructions.tStart = globalClock.getTime(format='float')
    Instructions.status = STARTED
    thisExp.addData('Instructions.started', Instructions.tStart)
    Instructions.maxDuration = None
    # keep track of which components have finished
    InstructionsComponents = Instructions.components
    for thisComponent in Instructions.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "Instructions" ---
    thisExp.currentRoutine = Instructions
    Instructions.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *Instructions_keep_alive* updates

        # if Instructions_keep_alive is starting this frame...
        if Instructions_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            Instructions_keep_alive.frameNStart = frameN  # exact frame index
            Instructions_keep_alive.tStart = t  # local t and not account for scr refresh
            Instructions_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(Instructions_keep_alive, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'Instructions_keep_alive.started')
            # update status
            Instructions_keep_alive.status = STARTED
            Instructions_keep_alive.setAutoDraw(True)

        # if Instructions_keep_alive is active this frame...
        if Instructions_keep_alive.status == STARTED:
            # update params
            pass
        # Run 'Each Frame' code from instructions_code

        instruction_icon.draw()
        keys = event.getKeys(keyList=["space", "return", "escape"])
        if "escape" in keys:
            core.quit()
        if "return" in keys:
            if instruction_audio:
                instruction_audio.stop()
            instruction_audio = g_play_audio("Audio/sequence_instr.wav")
        if "space" in keys:
            if instruction_audio:
                instruction_audio.stop()
            continueRoutine = False


        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[routineTimer, globalClock],
                currentRoutine=Instructions,
            )
            # skip the frame we paused on
            continue

        # has a Component requested the Routine to end?
        if not continueRoutine:
            Instructions.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if Instructions.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in Instructions.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "Instructions" ---
    for thisComponent in Instructions.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Instructions
    Instructions.tStop = globalClock.getTime(format='float')
    Instructions.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Instructions.stopped', Instructions.tStop)
    thisExp.nextEntry()
    # the Routine "Instructions" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # set up handler to look after randomisation of conditions etc
    PracticeLoop = data.TrialHandler2(
        name='PracticeLoop',
        nReps=1.0,
        method='sequential',
        extraInfo=expInfo,
        originPath=-1,
        trialList=data.importConditions('Conds/practice.csv'),
        seed=None,
        isTrials=True,
    )
    thisExp.addLoop(PracticeLoop)  # add the loop to the experiment
    thisPracticeLoop = PracticeLoop.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisPracticeLoop.rgb)
    if thisPracticeLoop != None:
        for paramName in thisPracticeLoop:
            globals()[paramName] = thisPracticeLoop[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    for thisPracticeLoop in PracticeLoop:
        PracticeLoop.status = STARTED
        if hasattr(thisPracticeLoop, 'status'):
            thisPracticeLoop.status = STARTED
        currentLoop = PracticeLoop
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisPracticeLoop.rgb)
        if thisPracticeLoop != None:
            for paramName in thisPracticeLoop:
                globals()[paramName] = thisPracticeLoop[paramName]

        # --- Prepare to start Routine "PracticeTrial" ---
        # create an object to store info about Routine PracticeTrial
        PracticeTrial = data.Routine(
            name='PracticeTrial',
            components=[PracticeTrial_keep_alive],
        )
        PracticeTrial.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from practice_trial_code

        G_PRACTICE_TRIAL_INDEX += 1
        win.color = "white"
        practice_between_image = g_text(globals().get("between_image", "")) or g_next_between_image()
        practice_previous_trial_index = G_PRACTICE_TRIAL_INDEX - 1
        practice_between_audio_value = g_text(G_PRACTICE_AFTER_TRIAL_AUDIO.get(practice_previous_trial_index, ""))
        practice_between_uses_speaker = practice_previous_trial_index in G_PRACTICE_SPEAKER_SCREEN_AFTER_TRIALS
        practice_between_display_image = G_AUDIO_SPEAKER_IMAGE if practice_between_uses_speaker else practice_between_image
        practice_placeholder = (
            g_audio_speaker_image(win) if practice_between_uses_speaker else g_fullscreen_image(win, practice_between_image)
        )
        practice_roles, practice_paths = g_roles_and_paths()
        practice_images = []
        practice_arrows = []
        practice_segment = 0
        practice_phase = "between"
        practice_between_clock = core.Clock()
        practice_between_audio = None
        practice_between_audio_lock = G_AUDIO_PROBE_LOCK_SEC if practice_between_audio_value else 0.0
        practice_after_placeholder = None
        practice_after_between_image = ""
        practice_after_between_clock = core.Clock()
        practice_after_between_lock = 0.0
        practice_audio = None
        practice_audio_value = ""
        practice_audio_clock = core.Clock()
        practice_audio_duration = 0
        practice_segment_audio_value = ""
        practice_segment_audio_started = False
        practice_segment_audio_lock = 0.0
        if practice_between_audio_value:
            practice_between_audio = g_play_audio(practice_between_audio_value)
        practice_between_clock.reset()
        thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
        thisExp.addData("practice_between_image", g_path(practice_between_display_image))
        thisExp.addData("practice_between_audio", g_path(practice_between_audio_value) if practice_between_audio_value else "")
        event.clearEvents()

        # store start times for PracticeTrial
        PracticeTrial.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        PracticeTrial.tStart = globalClock.getTime(format='float')
        PracticeTrial.status = STARTED
        thisExp.addData('PracticeTrial.started', PracticeTrial.tStart)
        PracticeTrial.maxDuration = None
        # keep track of which components have finished
        PracticeTrialComponents = PracticeTrial.components
        for thisComponent in PracticeTrial.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1

        # --- Run Routine "PracticeTrial" ---
        thisExp.currentRoutine = PracticeTrial
        PracticeTrial.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # if trial has changed, end Routine now
            if hasattr(thisPracticeLoop, 'status') and thisPracticeLoop.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame

            # *PracticeTrial_keep_alive* updates

            # if PracticeTrial_keep_alive is starting this frame...
            if PracticeTrial_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                PracticeTrial_keep_alive.frameNStart = frameN  # exact frame index
                PracticeTrial_keep_alive.tStart = t  # local t and not account for scr refresh
                PracticeTrial_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(PracticeTrial_keep_alive, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'PracticeTrial_keep_alive.started')
                # update status
                PracticeTrial_keep_alive.status = STARTED
                PracticeTrial_keep_alive.setAutoDraw(True)

            # if PracticeTrial_keep_alive is active this frame...
            if PracticeTrial_keep_alive.status == STARTED:
                # update params
                pass
            # Run 'Each Frame' code from practice_trial_code

            if practice_phase == "between":
                practice_placeholder.draw()
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and practice_between_clock.getTime() >= practice_between_audio_lock:
                    if practice_between_audio:
                        practice_between_audio.stop()
                    thisExp.addData("practice_between_rt", practice_between_clock.getTime())
                    g_release_fullscreen_image(practice_placeholder)
                    practice_placeholder = None
                    practice_images, practice_arrows = g_make_sequence(win, practice_roles, practice_paths)
                    practice_pre_audio_value = g_practice_pre_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment, len(practice_images))
                    if practice_pre_audio_value:
                        practice_phase = "practice_audio"
                        practice_audio_value = practice_pre_audio_value
                        practice_audio = g_play_audio(practice_audio_value)
                        practice_audio_clock.reset()
                        practice_audio_duration = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
                        thisExp.addData(f"practice_seg{practice_segment + 1}_pre_audio", g_path(practice_audio_value))
                    else:
                        practice_phase = "segment"
                        practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
                        practice_segment_audio_started = False
                        practice_segment_audio_lock = 0.0
                        practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                        G_RECORDER.start(practice_stem)
                    event.clearEvents()
            elif practice_phase == "segment":
                g_draw_sequence(practice_images, practice_arrows, practice_segment + 1)
                if practice_segment_audio_value and not practice_segment_audio_started:
                    practice_audio_value = practice_segment_audio_value
                    practice_audio = g_play_audio(practice_audio_value)
                    practice_audio_clock.reset()
                    practice_segment_audio_lock = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
                    practice_segment_audio_started = True
                    thisExp.addData(f"practice_seg{practice_segment + 1}_onset_audio", g_path(practice_audio_value))
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and practice_audio_clock.getTime() >= practice_segment_audio_lock:
                    if practice_audio:
                        practice_audio.stop()
                    practice_audio = None
                    audio_file = G_RECORDER.stop()
                    seg = practice_segment + 1
                    thisExp.addData(f"practice_seg{seg}_role", practice_roles[practice_segment])
                    thisExp.addData(f"practice_seg{seg}_audio", audio_file)
                    if practice_segment >= len(practice_images) - 1:
                        practice_audio_value = g_text(G_PRACTICE_AFTER_TRIAL_AUDIO.get(G_PRACTICE_TRIAL_INDEX, ""))
                        if practice_audio_value and G_PRACTICE_TRIAL_INDEX >= G_PRACTICE_TRIAL_COUNT:
                            practice_phase = "practice_after_between"
                            practice_after_between_image = g_next_between_image()
                            practice_after_placeholder = g_fullscreen_image(win, practice_after_between_image)
                            practice_audio = g_play_audio(practice_audio_value)
                            practice_audio_clock.reset()
                            practice_after_between_clock.reset()
                            practice_after_between_lock = G_AUDIO_PROBE_LOCK_SEC
                            thisExp.addData("practice_after_trial_audio", g_path(practice_audio_value))
                            thisExp.addData("practice_after_trial_between_image", g_path(practice_after_between_image))
                        else:
                            continueRoutine = False
                    else:
                        practice_segment += 1
                        practice_pre_audio_value = g_practice_pre_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment, len(practice_images))
                        if practice_pre_audio_value:
                            practice_phase = "practice_audio"
                            practice_audio_value = practice_pre_audio_value
                            practice_audio = g_play_audio(practice_audio_value)
                            practice_audio_clock.reset()
                            practice_audio_duration = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
                            thisExp.addData(f"practice_seg{practice_segment + 1}_pre_audio", g_path(practice_audio_value))
                        else:
                            practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
                            practice_segment_audio_started = False
                            practice_segment_audio_lock = 0.0
                            practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                            G_RECORDER.start(practice_stem)
                    event.clearEvents()
            elif practice_phase == "practice_audio":
                g_draw_sequence(practice_images, practice_arrows, practice_segment)
                if practice_audio_clock.getTime() >= practice_audio_duration:
                    if practice_audio:
                        practice_audio.stop()
                    practice_audio = None
                    practice_phase = "segment"
                    practice_segment_audio_value = g_practice_picture_audio(G_PRACTICE_TRIAL_INDEX, practice_segment)
                    practice_segment_audio_started = False
                    practice_segment_audio_lock = 0.0
                    practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                    G_RECORDER.start(practice_stem)
                    event.clearEvents()
            elif practice_phase == "practice_after_between":
                practice_after_placeholder.draw()
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and practice_after_between_clock.getTime() >= practice_after_between_lock:
                    if practice_audio:
                        practice_audio.stop()
                    practice_audio = None
                    g_release_fullscreen_image(practice_after_placeholder)
                    practice_after_placeholder = None
                    continueRoutine = False
                    event.clearEvents()


            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp,
                    win=win,
                    timers=[routineTimer, globalClock],
                    currentRoutine=PracticeTrial,
                )
                # skip the frame we paused on
                continue

            # has a Component requested the Routine to end?
            if not continueRoutine:
                PracticeTrial.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if PracticeTrial.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in PracticeTrial.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished

            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()

        # --- Ending Routine "PracticeTrial" ---
        for thisComponent in PracticeTrial.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for PracticeTrial
        PracticeTrial.tStop = globalClock.getTime(format='float')
        PracticeTrial.tStopRefresh = tThisFlipGlobal
        thisExp.addData('PracticeTrial.stopped', PracticeTrial.tStop)
        # Run 'End Routine' code from practice_trial_code

        G_RECORDER.stop()
        if practice_between_audio:
            practice_between_audio.stop()
        if practice_audio:
            practice_audio.stop()
        g_release_stims(practice_images, practice_arrows)
        g_release_fullscreen_image(practice_placeholder)
        g_release_fullscreen_image(practice_after_placeholder)
        practice_images = []
        practice_arrows = []
        practice_placeholder = None
        practice_after_placeholder = None

        # the Routine "PracticeTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        # mark thisPracticeLoop as finished
        if hasattr(thisPracticeLoop, 'status'):
            thisPracticeLoop.status = FINISHED
        # if awaiting a pause, pause now
        if PracticeLoop.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[globalClock],
            )
            # once done pausing, restore running status
            PracticeLoop.status = STARTED
        thisExp.nextEntry()

    # completed 1.0 repeats of 'PracticeLoop'
    PracticeLoop.status = FINISHED

    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    # --- Prepare to start Routine "PracticeEnd" ---
    # create an object to store info about Routine PracticeEnd
    PracticeEnd = data.Routine(
        name='PracticeEnd',
        components=[PracticeEnd_keep_alive],
    )
    PracticeEnd.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from practice_end_code

    win.color = "white"
    practice_done_icon = visual.ImageStim(win, image=g_path("Stimuli/sound.png"), pos=(0, 0), size=(0.22, 0.22), interpolate=True)
    practice_done_audio = g_play_audio("Audio/practice_end.wav")
    practice_done_clock = core.Clock()
    practice_done_duration = g_float(practice_done_audio.getDuration() if practice_done_audio else 0, 0.0)
    event.clearEvents()

    # store start times for PracticeEnd
    PracticeEnd.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    PracticeEnd.tStart = globalClock.getTime(format='float')
    PracticeEnd.status = STARTED
    thisExp.addData('PracticeEnd.started', PracticeEnd.tStart)
    PracticeEnd.maxDuration = None
    # keep track of which components have finished
    PracticeEndComponents = PracticeEnd.components
    for thisComponent in PracticeEnd.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "PracticeEnd" ---
    thisExp.currentRoutine = PracticeEnd
    PracticeEnd.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *PracticeEnd_keep_alive* updates

        # if PracticeEnd_keep_alive is starting this frame...
        if PracticeEnd_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            PracticeEnd_keep_alive.frameNStart = frameN  # exact frame index
            PracticeEnd_keep_alive.tStart = t  # local t and not account for scr refresh
            PracticeEnd_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(PracticeEnd_keep_alive, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'PracticeEnd_keep_alive.started')
            # update status
            PracticeEnd_keep_alive.status = STARTED
            PracticeEnd_keep_alive.setAutoDraw(True)

        # if PracticeEnd_keep_alive is active this frame...
        if PracticeEnd_keep_alive.status == STARTED:
            # update params
            pass
        # Run 'Each Frame' code from practice_end_code

        practice_done_icon.draw()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            core.quit()
        if "space" in keys and practice_done_clock.getTime() >= practice_done_duration:
            if practice_done_audio:
                practice_done_audio.stop()
            continueRoutine = False


        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[routineTimer, globalClock],
                currentRoutine=PracticeEnd,
            )
            # skip the frame we paused on
            continue

        # has a Component requested the Routine to end?
        if not continueRoutine:
            PracticeEnd.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if PracticeEnd.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in PracticeEnd.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "PracticeEnd" ---
    for thisComponent in PracticeEnd.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for PracticeEnd
    PracticeEnd.tStop = globalClock.getTime(format='float')
    PracticeEnd.tStopRefresh = tThisFlipGlobal
    thisExp.addData('PracticeEnd.stopped', PracticeEnd.tStop)
    thisExp.nextEntry()
    # the Routine "PracticeEnd" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # set up handler to look after randomisation of conditions etc
    MainBlock1 = data.TrialHandler2(
        name='MainBlock1',
        nReps=1.0,
        method='sequential',
        extraInfo=expInfo,
        originPath=-1,
        trialList=data.importConditions(g_runtime_main_block_file(1)),
        seed=None,
        isTrials=True,
    )
    thisExp.addLoop(MainBlock1)  # add the loop to the experiment
    thisMainBlock1 = MainBlock1.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisMainBlock1.rgb)
    if thisMainBlock1 != None:
        for paramName in thisMainBlock1:
            globals()[paramName] = thisMainBlock1[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    for thisMainBlock1 in MainBlock1:
        MainBlock1.status = STARTED
        if hasattr(thisMainBlock1, 'status'):
            thisMainBlock1.status = STARTED
        currentLoop = MainBlock1
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisMainBlock1.rgb)
        if thisMainBlock1 != None:
            for paramName in thisMainBlock1:
                globals()[paramName] = thisMainBlock1[paramName]

        # --- Prepare to start Routine "MainTrial" ---
        # create an object to store info about Routine MainTrial
        MainTrial = data.Routine(
            name='MainTrial',
            components=[MainTrial_keep_alive],
        )
        MainTrial.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from main_trial_code

        G_MAIN_TRIAL_INDEX += 1
        win.color = "white"
        main_between_image = g_next_between_image()
        main_placeholder = g_fullscreen_image(win, main_between_image)
        main_roles, main_paths = g_roles_and_paths()
        main_images = []
        main_arrows = []
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(main_between_image))
        thisExp.addData("audio_probe", audio_probe)
        thisExp.addData("between_audio", g_path(main_between_audio_value) if main_between_audio_value else "")
        event.clearEvents()

        # store start times for MainTrial
        MainTrial.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        MainTrial.tStart = globalClock.getTime(format='float')
        MainTrial.status = STARTED
        thisExp.addData('MainTrial.started', MainTrial.tStart)
        MainTrial.maxDuration = None
        # keep track of which components have finished
        MainTrialComponents = MainTrial.components
        for thisComponent in MainTrial.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1

        # --- Run Routine "MainTrial" ---
        thisExp.currentRoutine = MainTrial
        MainTrial.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # if trial has changed, end Routine now
            if hasattr(thisMainBlock1, 'status') and thisMainBlock1.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame

            # *MainTrial_keep_alive* updates

            # if MainTrial_keep_alive is starting this frame...
            if MainTrial_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                MainTrial_keep_alive.frameNStart = frameN  # exact frame index
                MainTrial_keep_alive.tStart = t  # local t and not account for scr refresh
                MainTrial_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(MainTrial_keep_alive, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'MainTrial_keep_alive.started')
                # update status
                MainTrial_keep_alive.status = STARTED
                MainTrial_keep_alive.setAutoDraw(True)

            # if MainTrial_keep_alive is active this frame...
            if MainTrial_keep_alive.status == STARTED:
                # update params
                pass
            # Run 'Each Frame' code from main_trial_code

            if main_phase == "between":
                main_placeholder.draw()
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and main_between_clock.getTime() >= main_audio_lock:
                    if main_between_audio:
                        main_between_audio.stop()
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys:
                    audio_file = G_RECORDER.stop()
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                        G_RECORDER.start(main_stem)
                    event.clearEvents()


            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp,
                    win=win,
                    timers=[routineTimer, globalClock],
                    currentRoutine=MainTrial,
                )
                # skip the frame we paused on
                continue

            # has a Component requested the Routine to end?
            if not continueRoutine:
                MainTrial.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if MainTrial.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in MainTrial.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished

            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()

        # --- Ending Routine "MainTrial" ---
        for thisComponent in MainTrial.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for MainTrial
        MainTrial.tStop = globalClock.getTime(format='float')
        MainTrial.tStopRefresh = tThisFlipGlobal
        thisExp.addData('MainTrial.stopped', MainTrial.tStop)
        # Run 'End Routine' code from main_trial_code

        G_RECORDER.stop()
        if main_between_audio:
            main_between_audio.stop()
        g_release_stims(main_images, main_arrows)
        g_release_fullscreen_image(main_placeholder)
        main_images = []
        main_arrows = []
        main_placeholder = None

        # the Routine "MainTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        # mark thisMainBlock1 as finished
        if hasattr(thisMainBlock1, 'status'):
            thisMainBlock1.status = FINISHED
        # if awaiting a pause, pause now
        if MainBlock1.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[globalClock],
            )
            # once done pausing, restore running status
            MainBlock1.status = STARTED
        thisExp.nextEntry()

    # completed 1.0 repeats of 'MainBlock1'
    MainBlock1.status = FINISHED

    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    # --- Prepare to start Routine "Break" ---
    # create an object to store info about Routine Break
    Break = data.Routine(
        name='Break',
        components=[Break_keep_alive],
    )
    Break.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from break_code

    win.color = "white"
    break_image = visual.ImageStim(win, image=g_path("Stimuli/break.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
    break_clock = core.Clock()
    event.clearEvents()

    # store start times for Break
    Break.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Break.tStart = globalClock.getTime(format='float')
    Break.status = STARTED
    thisExp.addData('Break.started', Break.tStart)
    Break.maxDuration = None
    # keep track of which components have finished
    BreakComponents = Break.components
    for thisComponent in Break.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "Break" ---
    thisExp.currentRoutine = Break
    Break.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *Break_keep_alive* updates

        # if Break_keep_alive is starting this frame...
        if Break_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            Break_keep_alive.frameNStart = frameN  # exact frame index
            Break_keep_alive.tStart = t  # local t and not account for scr refresh
            Break_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(Break_keep_alive, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'Break_keep_alive.started')
            # update status
            Break_keep_alive.status = STARTED
            Break_keep_alive.setAutoDraw(True)

        # if Break_keep_alive is active this frame...
        if Break_keep_alive.status == STARTED:
            # update params
            pass
        # Run 'Each Frame' code from break_code

        break_image.draw()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            core.quit()
        if "space" in keys and break_clock.getTime() >= 30:
            continueRoutine = False


        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[routineTimer, globalClock],
                currentRoutine=Break,
            )
            # skip the frame we paused on
            continue

        # has a Component requested the Routine to end?
        if not continueRoutine:
            Break.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if Break.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in Break.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "Break" ---
    for thisComponent in Break.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Break
    Break.tStop = globalClock.getTime(format='float')
    Break.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Break.stopped', Break.tStop)
    thisExp.nextEntry()
    # the Routine "Break" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # set up handler to look after randomisation of conditions etc
    MainBlock2 = data.TrialHandler2(
        name='MainBlock2',
        nReps=1.0,
        method='sequential',
        extraInfo=expInfo,
        originPath=-1,
        trialList=data.importConditions(g_runtime_main_block_file(2)),
        seed=None,
        isTrials=True,
    )
    thisExp.addLoop(MainBlock2)  # add the loop to the experiment
    thisMainBlock2 = MainBlock2.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisMainBlock2.rgb)
    if thisMainBlock2 != None:
        for paramName in thisMainBlock2:
            globals()[paramName] = thisMainBlock2[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    for thisMainBlock2 in MainBlock2:
        MainBlock2.status = STARTED
        if hasattr(thisMainBlock2, 'status'):
            thisMainBlock2.status = STARTED
        currentLoop = MainBlock2
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisMainBlock2.rgb)
        if thisMainBlock2 != None:
            for paramName in thisMainBlock2:
                globals()[paramName] = thisMainBlock2[paramName]

        # --- Prepare to start Routine "MainTrial" ---
        # create an object to store info about Routine MainTrial
        MainTrial = data.Routine(
            name='MainTrial',
            components=[MainTrial_keep_alive],
        )
        MainTrial.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from main_trial_code

        G_MAIN_TRIAL_INDEX += 1
        win.color = "white"
        main_between_image = g_next_between_image()
        main_placeholder = g_fullscreen_image(win, main_between_image)
        main_roles, main_paths = g_roles_and_paths()
        main_images = []
        main_arrows = []
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(main_between_image))
        thisExp.addData("audio_probe", audio_probe)
        thisExp.addData("between_audio", g_path(main_between_audio_value) if main_between_audio_value else "")
        event.clearEvents()

        # store start times for MainTrial
        MainTrial.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        MainTrial.tStart = globalClock.getTime(format='float')
        MainTrial.status = STARTED
        thisExp.addData('MainTrial.started', MainTrial.tStart)
        MainTrial.maxDuration = None
        # keep track of which components have finished
        MainTrialComponents = MainTrial.components
        for thisComponent in MainTrial.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1

        # --- Run Routine "MainTrial" ---
        thisExp.currentRoutine = MainTrial
        MainTrial.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # if trial has changed, end Routine now
            if hasattr(thisMainBlock2, 'status') and thisMainBlock2.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame

            # *MainTrial_keep_alive* updates

            # if MainTrial_keep_alive is starting this frame...
            if MainTrial_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                MainTrial_keep_alive.frameNStart = frameN  # exact frame index
                MainTrial_keep_alive.tStart = t  # local t and not account for scr refresh
                MainTrial_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(MainTrial_keep_alive, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'MainTrial_keep_alive.started')
                # update status
                MainTrial_keep_alive.status = STARTED
                MainTrial_keep_alive.setAutoDraw(True)

            # if MainTrial_keep_alive is active this frame...
            if MainTrial_keep_alive.status == STARTED:
                # update params
                pass
            # Run 'Each Frame' code from main_trial_code

            if main_phase == "between":
                main_placeholder.draw()
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and main_between_clock.getTime() >= main_audio_lock:
                    if main_between_audio:
                        main_between_audio.stop()
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys:
                    audio_file = G_RECORDER.stop()
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                        G_RECORDER.start(main_stem)
                    event.clearEvents()


            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp,
                    win=win,
                    timers=[routineTimer, globalClock],
                    currentRoutine=MainTrial,
                )
                # skip the frame we paused on
                continue

            # has a Component requested the Routine to end?
            if not continueRoutine:
                MainTrial.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if MainTrial.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in MainTrial.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished

            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()

        # --- Ending Routine "MainTrial" ---
        for thisComponent in MainTrial.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for MainTrial
        MainTrial.tStop = globalClock.getTime(format='float')
        MainTrial.tStopRefresh = tThisFlipGlobal
        thisExp.addData('MainTrial.stopped', MainTrial.tStop)
        # Run 'End Routine' code from main_trial_code

        G_RECORDER.stop()
        if main_between_audio:
            main_between_audio.stop()
        g_release_stims(main_images, main_arrows)
        g_release_fullscreen_image(main_placeholder)
        main_images = []
        main_arrows = []
        main_placeholder = None

        # the Routine "MainTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        # mark thisMainBlock2 as finished
        if hasattr(thisMainBlock2, 'status'):
            thisMainBlock2.status = FINISHED
        # if awaiting a pause, pause now
        if MainBlock2.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[globalClock],
            )
            # once done pausing, restore running status
            MainBlock2.status = STARTED
        thisExp.nextEntry()

    # completed 1.0 repeats of 'MainBlock2'
    MainBlock2.status = FINISHED

    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    # --- Prepare to start Routine "Break" ---
    # create an object to store info about Routine Break
    Break = data.Routine(
        name='Break',
        components=[Break_keep_alive],
    )
    Break.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from break_code

    win.color = "white"
    break_image = visual.ImageStim(win, image=g_path("Stimuli/break.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
    break_clock = core.Clock()
    event.clearEvents()

    # store start times for Break
    Break.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    Break.tStart = globalClock.getTime(format='float')
    Break.status = STARTED
    thisExp.addData('Break.started', Break.tStart)
    Break.maxDuration = None
    # keep track of which components have finished
    BreakComponents = Break.components
    for thisComponent in Break.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "Break" ---
    thisExp.currentRoutine = Break
    Break.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *Break_keep_alive* updates

        # if Break_keep_alive is starting this frame...
        if Break_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            Break_keep_alive.frameNStart = frameN  # exact frame index
            Break_keep_alive.tStart = t  # local t and not account for scr refresh
            Break_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(Break_keep_alive, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'Break_keep_alive.started')
            # update status
            Break_keep_alive.status = STARTED
            Break_keep_alive.setAutoDraw(True)

        # if Break_keep_alive is active this frame...
        if Break_keep_alive.status == STARTED:
            # update params
            pass
        # Run 'Each Frame' code from break_code

        break_image.draw()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys:
            core.quit()
        if "space" in keys and break_clock.getTime() >= 30:
            continueRoutine = False


        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[routineTimer, globalClock],
                currentRoutine=Break,
            )
            # skip the frame we paused on
            continue

        # has a Component requested the Routine to end?
        if not continueRoutine:
            Break.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if Break.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in Break.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "Break" ---
    for thisComponent in Break.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for Break
    Break.tStop = globalClock.getTime(format='float')
    Break.tStopRefresh = tThisFlipGlobal
    thisExp.addData('Break.stopped', Break.tStop)
    thisExp.nextEntry()
    # the Routine "Break" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # set up handler to look after randomisation of conditions etc
    MainBlock3 = data.TrialHandler2(
        name='MainBlock3',
        nReps=1.0,
        method='sequential',
        extraInfo=expInfo,
        originPath=-1,
        trialList=data.importConditions(g_runtime_main_block_file(3)),
        seed=None,
        isTrials=True,
    )
    thisExp.addLoop(MainBlock3)  # add the loop to the experiment
    thisMainBlock3 = MainBlock3.trialList[0]  # so we can initialise stimuli with some values
    # abbreviate parameter names if possible (e.g. rgb = thisMainBlock3.rgb)
    if thisMainBlock3 != None:
        for paramName in thisMainBlock3:
            globals()[paramName] = thisMainBlock3[paramName]
    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    for thisMainBlock3 in MainBlock3:
        MainBlock3.status = STARTED
        if hasattr(thisMainBlock3, 'status'):
            thisMainBlock3.status = STARTED
        currentLoop = MainBlock3
        thisExp.timestampOnFlip(win, 'thisRow.t', format=globalClock.format)
        if thisSession is not None:
            # if running in a Session with a Liaison client, send data up to now
            thisSession.sendExperimentData()
        # abbreviate parameter names if possible (e.g. rgb = thisMainBlock3.rgb)
        if thisMainBlock3 != None:
            for paramName in thisMainBlock3:
                globals()[paramName] = thisMainBlock3[paramName]

        # --- Prepare to start Routine "MainTrial" ---
        # create an object to store info about Routine MainTrial
        MainTrial = data.Routine(
            name='MainTrial',
            components=[MainTrial_keep_alive],
        )
        MainTrial.status = NOT_STARTED
        continueRoutine = True
        # update component parameters for each repeat
        # Run 'Begin Routine' code from main_trial_code

        G_MAIN_TRIAL_INDEX += 1
        win.color = "white"
        main_between_image = g_next_between_image()
        main_placeholder = g_fullscreen_image(win, main_between_image)
        main_roles, main_paths = g_roles_and_paths()
        main_images = []
        main_arrows = []
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(main_between_image))
        thisExp.addData("audio_probe", audio_probe)
        thisExp.addData("between_audio", g_path(main_between_audio_value) if main_between_audio_value else "")
        event.clearEvents()

        # store start times for MainTrial
        MainTrial.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
        MainTrial.tStart = globalClock.getTime(format='float')
        MainTrial.status = STARTED
        thisExp.addData('MainTrial.started', MainTrial.tStart)
        MainTrial.maxDuration = None
        # keep track of which components have finished
        MainTrialComponents = MainTrial.components
        for thisComponent in MainTrial.components:
            thisComponent.tStart = None
            thisComponent.tStop = None
            thisComponent.tStartRefresh = None
            thisComponent.tStopRefresh = None
            if hasattr(thisComponent, 'status'):
                thisComponent.status = NOT_STARTED
        # reset timers
        t = 0
        _timeToFirstFrame = win.getFutureFlipTime(clock="now")
        frameN = -1

        # --- Run Routine "MainTrial" ---
        thisExp.currentRoutine = MainTrial
        MainTrial.forceEnded = routineForceEnded = not continueRoutine
        while continueRoutine:
            # if trial has changed, end Routine now
            if hasattr(thisMainBlock3, 'status') and thisMainBlock3.status == STOPPING:
                continueRoutine = False
            # get current time
            t = routineTimer.getTime()
            tThisFlip = win.getFutureFlipTime(clock=routineTimer)
            tThisFlipGlobal = win.getFutureFlipTime(clock=None)
            frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
            # update/draw components on each frame

            # *MainTrial_keep_alive* updates

            # if MainTrial_keep_alive is starting this frame...
            if MainTrial_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
                # keep track of start time/frame for later
                MainTrial_keep_alive.frameNStart = frameN  # exact frame index
                MainTrial_keep_alive.tStart = t  # local t and not account for scr refresh
                MainTrial_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
                win.timeOnFlip(MainTrial_keep_alive, 'tStartRefresh')  # time at next scr refresh
                # add timestamp to datafile
                thisExp.timestampOnFlip(win, 'MainTrial_keep_alive.started')
                # update status
                MainTrial_keep_alive.status = STARTED
                MainTrial_keep_alive.setAutoDraw(True)

            # if MainTrial_keep_alive is active this frame...
            if MainTrial_keep_alive.status == STARTED:
                # update params
                pass
            # Run 'Each Frame' code from main_trial_code

            if main_phase == "between":
                main_placeholder.draw()
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys and main_between_clock.getTime() >= main_audio_lock:
                    if main_between_audio:
                        main_between_audio.stop()
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys:
                    audio_file = G_RECORDER.stop()
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                        G_RECORDER.start(main_stem)
                    event.clearEvents()


            # check for quit (typically the Esc key)
            if defaultKeyboard.getKeys(keyList=["escape"]):
                thisExp.status = FINISHED
            if thisExp.status == FINISHED or endExpNow:
                endExperiment(thisExp, win=win)
                return
            # pause experiment here if requested
            if thisExp.status == PAUSED:
                pauseExperiment(
                    thisExp=thisExp,
                    win=win,
                    timers=[routineTimer, globalClock],
                    currentRoutine=MainTrial,
                )
                # skip the frame we paused on
                continue

            # has a Component requested the Routine to end?
            if not continueRoutine:
                MainTrial.forceEnded = routineForceEnded = True
            # has the Routine been forcibly ended?
            if MainTrial.forceEnded or routineForceEnded:
                break
            # has every Component finished?
            continueRoutine = False
            for thisComponent in MainTrial.components:
                if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                    continueRoutine = True
                    break  # at least one component has not yet finished

            # refresh the screen
            if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
                win.flip()

        # --- Ending Routine "MainTrial" ---
        for thisComponent in MainTrial.components:
            if hasattr(thisComponent, "setAutoDraw"):
                thisComponent.setAutoDraw(False)
        # store stop times for MainTrial
        MainTrial.tStop = globalClock.getTime(format='float')
        MainTrial.tStopRefresh = tThisFlipGlobal
        thisExp.addData('MainTrial.stopped', MainTrial.tStop)
        # Run 'End Routine' code from main_trial_code

        G_RECORDER.stop()
        if main_between_audio:
            main_between_audio.stop()
        g_release_stims(main_images, main_arrows)
        g_release_fullscreen_image(main_placeholder)
        main_images = []
        main_arrows = []
        main_placeholder = None

        # the Routine "MainTrial" was not non-slip safe, so reset the non-slip timer
        routineTimer.reset()
        # mark thisMainBlock3 as finished
        if hasattr(thisMainBlock3, 'status'):
            thisMainBlock3.status = FINISHED
        # if awaiting a pause, pause now
        if MainBlock3.status == PAUSED:
            thisExp.status = PAUSED
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[globalClock],
            )
            # once done pausing, restore running status
            MainBlock3.status = STARTED
        thisExp.nextEntry()

    # completed 1.0 repeats of 'MainBlock3'
    MainBlock3.status = FINISHED

    if thisSession is not None:
        # if running in a Session with a Liaison client, send data up to now
        thisSession.sendExperimentData()

    # --- Prepare to start Routine "EndExperiment" ---
    # create an object to store info about Routine EndExperiment
    EndExperiment = data.Routine(
        name='EndExperiment',
        components=[EndExperiment_keep_alive],
    )
    EndExperiment.status = NOT_STARTED
    continueRoutine = True
    # update component parameters for each repeat
    # Run 'Begin Routine' code from end_code

    win.color = "white"
    finish_image = visual.ImageStim(win, image=g_path("Stimuli/finish.png"), pos=(0, 0), size=(0.55, 0.55), interpolate=True)
    finish_clock = core.Clock()
    event.clearEvents()

    # store start times for EndExperiment
    EndExperiment.tStartRefresh = win.getFutureFlipTime(clock=globalClock)
    EndExperiment.tStart = globalClock.getTime(format='float')
    EndExperiment.status = STARTED
    thisExp.addData('EndExperiment.started', EndExperiment.tStart)
    EndExperiment.maxDuration = None
    # keep track of which components have finished
    EndExperimentComponents = EndExperiment.components
    for thisComponent in EndExperiment.components:
        thisComponent.tStart = None
        thisComponent.tStop = None
        thisComponent.tStartRefresh = None
        thisComponent.tStopRefresh = None
        if hasattr(thisComponent, 'status'):
            thisComponent.status = NOT_STARTED
    # reset timers
    t = 0
    _timeToFirstFrame = win.getFutureFlipTime(clock="now")
    frameN = -1

    # --- Run Routine "EndExperiment" ---
    thisExp.currentRoutine = EndExperiment
    EndExperiment.forceEnded = routineForceEnded = not continueRoutine
    while continueRoutine:
        # get current time
        t = routineTimer.getTime()
        tThisFlip = win.getFutureFlipTime(clock=routineTimer)
        tThisFlipGlobal = win.getFutureFlipTime(clock=None)
        frameN = frameN + 1  # number of completed frames (so 0 is the first frame)
        # update/draw components on each frame

        # *EndExperiment_keep_alive* updates

        # if EndExperiment_keep_alive is starting this frame...
        if EndExperiment_keep_alive.status == NOT_STARTED and tThisFlip >= 0.0-frameTolerance:
            # keep track of start time/frame for later
            EndExperiment_keep_alive.frameNStart = frameN  # exact frame index
            EndExperiment_keep_alive.tStart = t  # local t and not account for scr refresh
            EndExperiment_keep_alive.tStartRefresh = tThisFlipGlobal  # on global time
            win.timeOnFlip(EndExperiment_keep_alive, 'tStartRefresh')  # time at next scr refresh
            # add timestamp to datafile
            thisExp.timestampOnFlip(win, 'EndExperiment_keep_alive.started')
            # update status
            EndExperiment_keep_alive.status = STARTED
            EndExperiment_keep_alive.setAutoDraw(True)

        # if EndExperiment_keep_alive is active this frame...
        if EndExperiment_keep_alive.status == STARTED:
            # update params
            pass
        # Run 'Each Frame' code from end_code

        finish_image.draw()
        keys = event.getKeys(keyList=["space", "escape"])
        if "escape" in keys or "space" in keys or finish_clock.getTime() >= 10:
            g_cleanup()
            continueRoutine = False


        # check for quit (typically the Esc key)
        if defaultKeyboard.getKeys(keyList=["escape"]):
            thisExp.status = FINISHED
        if thisExp.status == FINISHED or endExpNow:
            endExperiment(thisExp, win=win)
            return
        # pause experiment here if requested
        if thisExp.status == PAUSED:
            pauseExperiment(
                thisExp=thisExp,
                win=win,
                timers=[routineTimer, globalClock],
                currentRoutine=EndExperiment,
            )
            # skip the frame we paused on
            continue

        # has a Component requested the Routine to end?
        if not continueRoutine:
            EndExperiment.forceEnded = routineForceEnded = True
        # has the Routine been forcibly ended?
        if EndExperiment.forceEnded or routineForceEnded:
            break
        # has every Component finished?
        continueRoutine = False
        for thisComponent in EndExperiment.components:
            if hasattr(thisComponent, "status") and thisComponent.status != FINISHED:
                continueRoutine = True
                break  # at least one component has not yet finished

        # refresh the screen
        if continueRoutine:  # don't flip if this routine is over or we'll get a blank screen
            win.flip()

    # --- Ending Routine "EndExperiment" ---
    for thisComponent in EndExperiment.components:
        if hasattr(thisComponent, "setAutoDraw"):
            thisComponent.setAutoDraw(False)
    # store stop times for EndExperiment
    EndExperiment.tStop = globalClock.getTime(format='float')
    EndExperiment.tStopRefresh = tThisFlipGlobal
    thisExp.addData('EndExperiment.stopped', EndExperiment.tStop)
    thisExp.nextEntry()
    # the Routine "EndExperiment" was not non-slip safe, so reset the non-slip timer
    routineTimer.reset()

    # mark experiment as finished
    endExperiment(thisExp, win=win)


def saveData(thisExp):
    """
    Save data from this experiment

    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    """
    filename = thisExp.dataFileName
    # these shouldn't be strictly necessary (should auto-save)
    thisExp.saveAsWideText(filename + '.csv', delim='auto')
    thisExp.saveAsPickle(filename)


def endExperiment(thisExp, win=None):
    """
    End this experiment, performing final shut down operations.

    This function does NOT close the window or end the Python process - use `quit` for this.

    Parameters
    ==========
    thisExp : psychopy.data.ExperimentHandler
        Handler object for this experiment, contains the data to save and information about
        where to save it to.
    win : psychopy.visual.Window
        Window for this experiment.
    """
    if win is not None:
        # remove autodraw from all current components
        win.clearAutoDraw()
        # Flip one final time so any remaining win.callOnFlip()
        # and win.timeOnFlip() tasks get executed
        win.flip()
    # return console logger level to WARNING
    logging.console.setLevel(logging.WARNING)
    # mark experiment handler as finished
    thisExp.status = FINISHED
    # run any 'at exit' functions
    for fcn in runAtExit:
        fcn()
    logging.flush()


def quit(thisExp, win=None, thisSession=None):
    """
    Fully quit, closing the window and ending the Python process.

    Parameters
    ==========
    win : psychopy.visual.Window
        Window to close.
    thisSession : psychopy.session.Session or None
        Handle of the Session object this experiment is being run from, if any.
    """
    thisExp.abort()  # or data files will save again on exit
    # make sure everything is closed down
    if win is not None:
        # Flip one final time so any remaining win.callOnFlip()
        # and win.timeOnFlip() tasks get executed before quitting
        win.flip()
        win.close()
    logging.flush()
    if thisSession is not None:
        thisSession.stop()
    # terminate Python process
    core.quit()


# if running this experiment as a script...
if __name__ == '__main__':
    # call all functions in order
    expInfo = showExpInfoDlg(expInfo=expInfo)
    thisExp = setupData(expInfo=expInfo)
    logFile = setupLogging(filename=thisExp.dataFileName)
    win = setupWindow(expInfo=expInfo)
    setupDevices(expInfo=expInfo, thisExp=thisExp, win=win)
    run(
        expInfo=expInfo,
        thisExp=thisExp,
        win=win,
        globalClock='float'
    )
    saveData(thisExp=thisExp)
    quit(thisExp=thisExp, win=win)
