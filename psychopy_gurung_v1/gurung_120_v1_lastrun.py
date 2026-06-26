#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2026.1.3),
    on June 25, 2026, at 15:52
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
psychopyVersion = '2026.1.3'
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
    # store pilot mode in data file
    thisExp.addData('piloting', PILOTING, priority=priority.LOW)
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
    import atexit
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
    G_SEQUENCE_JITTER_SLOTS = (
        (-0.30, -0.018),
        (-0.22, 0.018),
        (-0.18, -0.018),
        (-0.06, 0.018),
        (0.06, -0.018),
        (0.18, 0.018),
        (0.22, -0.018),
        (0.30, 0.018),
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
    G_RECORDING_STOP_GRACE_SEC = 0.5
    G_LISTENER_RESPONSE_MIN_SEC = 10.0
    G_LISTENER_RESPONSE_DIRNAME = "listener responses"
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
    G_LAST_MAIN_TRIAL_INFO = {}
    
    
    def g_log(message):
        text = f"{core.getTime():.3f} {message}"
        print(text)
        try:
            with G_DEBUG_LOG.open("a", encoding="utf-8") as handle:
                handle.write(text + "\n")
        except Exception:
            pass
    
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
    
    
    def g_key_names(keys):
        names = []
        for key in keys:
            try:
                names.append(key[0])
            except Exception:
                names.append(key)
        return names
    
    
    def g_key_time(keys, key_name, default=None):
        if default is None:
            default = core.getTime()
        for key in keys:
            try:
                if key[0] == key_name:
                    return g_float(key[-1], default)
            except Exception:
                if key == key_name:
                    return default
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
        g_log("Using PsychoPy default speaker device.")
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
        (folder / G_LISTENER_RESPONSE_DIRNAME).mkdir(parents=True, exist_ok=True)
        expInfo["recordings_dir"] = str(folder)
        g_log(f"recordings_dir {folder}")
        return folder
    
    
    def g_listener_practice_stem(trial_index):
        participant = g_safe(expInfo.get("participant", "participant"))
        return f"{participant}_listener_practice_trial{int(trial_index):02d}"
    
    
    def g_listener_main_stem(trial_info):
        participant = g_safe(expInfo.get("participant", "participant"))
        trial_index = g_int((trial_info or {}).get("trial_index", 0), 0)
        dataset_number = g_int((trial_info or {}).get("dataset_number", 0), 0)
        condition_id = g_safe(g_text((trial_info or {}).get("condition_id", "unknown_condition")))
        return f"{participant}_listener_main_trial{trial_index:03d}_imageset{dataset_number:02d}_condition_{condition_id}"
    
    
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
            bag = list(G_SEQUENCE_JITTER_SLOTS)
            _gurung_random.shuffle(bag)
            G_SEQUENCE_JITTER_STATE["bag"] = bag
        return bag.pop()
    
    
    def g_sequence_layout(win, roles):
        sequence_count = max(1, len(roles))
        size_count = max(G_SEQUENCE_SIZE_COUNT, sequence_count)
        jitter_x_width_max = max(abs(pos[0]) for pos in G_SEQUENCE_JITTER_SLOTS)
        jitter_y_max = max(abs(pos[1]) for pos in G_SEQUENCE_JITTER_SLOTS)
        horizontal_room = max(0.1, g_window_aspect(win) - (2 * G_SEQUENCE_X_MARGIN))
        vertical_room = max(0.1, 1.0 - (2 * (G_SEQUENCE_Y_MARGIN + jitter_y_max)))
        width_from_horizontal = horizontal_room / (
            size_count
            + ((size_count - 1) * G_SEQUENCE_GAP_RATIO)
            + (2 * jitter_x_width_max)
        )
        image_height = min(vertical_room, width_from_horizontal / G_IMAGE_ASPECT)
        image_width = image_height * G_IMAGE_ASPECT
        gap = image_width * G_SEQUENCE_GAP_RATIO
        step = image_width + gap
        row_center = (len(roles) - 1) / 2.0
        jitter_x_factor, jitter_y = g_next_sequence_jitter()
        jitter_x = jitter_x_factor * image_width
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
        audio = sound.Sound(path)
        audio.play()
        return audio
    
    
    class GRecorder:
        sample_rate = 48000
    
        def __init__(self, root):
            self.root = Path(root)
            self.root.mkdir(exist_ok=True)
            self.full_path = self.root / "full_session.wav"
            self.events_path = self.root / "recording_events.csv"
            self.segments_path = self.root / "recording_segments.csv"
            self.stream = None
            self.full_writer = None
            self.segments = []
            self.current_segment = None
            self.lock = threading.Lock()
            self.log_lock = threading.Lock()
            self.write_queue = queue.Queue()
            self.close_event = threading.Event()
            self.event_index = 0
            self.segment_index = 0
            self.total_frames = 0
            self.last_callback_core_time = None
            self.last_callback_end_sample = 0
            self.finalized = False
            self.full_blocks_since_flush = 0
            self.event_handle = None
            self.event_writer = None
            self.writer_error = None
            self._open_event_log()
            self.writer = threading.Thread(target=self._writer_loop, daemon=True)
            self.writer.start()
            self.closer = threading.Thread(target=self._closer_loop, daemon=True)
            self.closer.start()
            if G_RECORDING_AVAILABLE:
                self._ensure_stream()
            else:
                self._log_event("recording_unavailable", details="sounddevice/soundfile import failed")
    
        def start(self, stem, subdir=None):
            self.stop()
            if not G_RECORDING_AVAILABLE:
                return ""
            self._ensure_stream()
            if self.stream is None:
                return ""
            now = core.getTime()
            sample = self._sample_index_now(event_core_time=now)
            target_dir = self.root
            if subdir:
                target_dir = self.root / str(subdir)
                target_dir.mkdir(parents=True, exist_ok=True)
            path = target_dir / f"{g_safe(stem)}.wav"
            with self.lock:
                self.segment_index += 1
                segment = {
                    "id": self.segment_index,
                    "stem": g_safe(stem),
                    "path": path,
                    "full_session_path": self.full_path,
                    "requested_core_time": now,
                    "requested_stream_time": self._stream_time_unlocked(),
                    "requested_sample": sample,
                    "onset_scheduled": False,
                    "onset_core_time": None,
                    "onset_stream_time": None,
                    "onset_sample": None,
                    "stop_core_time": None,
                    "stop_stream_time": None,
                    "stop_sample": None,
                    "post_pad_sec": None,
                    "end_sample": None,
                    "clip_start_sample": None,
                    "clip_end_sample": None,
                    "written": False,
                    "written_core_time": None,
                    "n_frames": 0,
                    "status": "waiting_for_picture_onset",
                    "notes": "",
                }
                self.segments.append(segment)
                self.current_segment = segment
            self._log_event("segment_start_requested", segment, sample, details=str(path))
            self._write_segments_log()
            return str(path)
    
        def mark_onset_on_flip(self):
            with self.lock:
                segment = self.current_segment
                if segment is None:
                    return
                if segment.get("onset_scheduled") or segment.get("onset_sample") is not None:
                    return
                segment["onset_scheduled"] = True
                segment_id = segment["id"]
            try:
                win.callOnFlip(self._mark_segment_onset, segment_id)
            except Exception as err:
                self._mark_segment_onset(segment_id, note=f"callOnFlip_failed:{err}")
    
        def _mark_segment_onset(self, segment_id, note=""):
            now = core.getTime()
            stream_time = self._stream_time()
            sample = self._sample_index_now(stream_time=stream_time, event_core_time=now)
            with self.lock:
                segment = self._find_segment_unlocked(segment_id)
                if segment is None or segment.get("onset_sample") is not None:
                    return
                segment["onset_core_time"] = now
                segment["onset_stream_time"] = stream_time
                segment["onset_sample"] = sample
                segment["status"] = "recording"
                if note:
                    segment["notes"] = note
            self._log_event("picture_onset", segment, sample, stream_time=stream_time, details=note)
            self._write_segments_log()
    
        def _ensure_stream(self):
            if self.stream is not None:
                return
            if not G_RECORDING_AVAILABLE:
                return
    
            def callback(indata, frames, time_info, status):
                if status:
                    g_log(f"rec_callback_status {status}")
                block = indata.copy()
                callback_core_time = core.getTime()
                with self.lock:
                    block_start = self.total_frames
                    block_end = block_start + int(frames)
                    self.total_frames = block_end
                    self.last_callback_core_time = callback_core_time
                    self.last_callback_end_sample = block_end
                self.write_queue.put(("full", block))
    
            g_log("rec_stream_open_start")
            try:
                self.full_writer = _gurung_sf.SoundFile(
                    str(self.full_path),
                    mode="w",
                    samplerate=self.sample_rate,
                    channels=1,
                )
                self.stream = _gurung_sd.InputStream(
                    samplerate=self.sample_rate,
                    channels=1,
                    dtype="float32",
                    callback=callback,
                )
                self.stream.start()
                self._log_event("full_session_start", sample_index=0, details=str(self.full_path))
                g_log("rec_stream_open_done")
            except Exception as err:
                g_log(f"rec_stream_open_failed {err}")
                self._log_event("recording_open_failed", details=str(err))
                self.stream = None
                try:
                    if self.full_writer is not None:
                        self.full_writer.close()
                except Exception:
                    pass
                self.full_writer = None
    
        def stop(self, grace_sec=None, event_core_time=None):
            if grace_sec is None:
                grace_sec = G_RECORDING_STOP_GRACE_SEC
            now = core.getTime()
            if event_core_time is None:
                event_core_time = now
            stream_time = self._stream_time()
            sample = self._sample_index_now(stream_time=stream_time, event_core_time=event_core_time)
            end_sample = sample + int(round(max(0.0, grace_sec) * self.sample_rate))
            with self.lock:
                segment = self.current_segment
                self.current_segment = None
                if segment is not None:
                    if segment.get("onset_sample") is None:
                        segment["onset_sample"] = segment.get("requested_sample", sample)
                        segment["onset_core_time"] = segment.get("requested_core_time", event_core_time)
                        segment["onset_stream_time"] = segment.get("requested_stream_time", stream_time)
                        segment["notes"] = "forced_onset_from_start_request"
                    segment["stop_core_time"] = event_core_time
                    segment["stop_stream_time"] = stream_time
                    segment["stop_sample"] = sample
                    segment["post_pad_sec"] = max(0.0, grace_sec)
                    segment["end_sample"] = max(int(segment["onset_sample"]), int(end_sample))
                    segment["status"] = "stopped_waiting_for_tail"
            if segment is None:
                return ""
            path = segment["path"]
            self._log_event(
                "segment_stop_requested",
                segment,
                sample,
                stream_time=stream_time,
                details=f"grace={grace_sec:.3f};event_core_time={event_core_time:.6f}",
            )
            self._write_segments_log()
            return str(path)
    
        def _closer_loop(self):
            while True:
                self.close_event.wait(0.02)
                self.close_event.clear()
                self._flush_ready_segments()
    
        def _flush_ready_segments(self, force=False):
            return
    
        def _writer_loop(self):
            while True:
                item = self.write_queue.get()
                try:
                    if item is None:
                        self._close_full_writer()
                        return
                    kind = item[0]
                    if kind == "full":
                        self._write_full_block(item[1])
                except Exception as err:
                    self.writer_error = err
                    g_log(f"rec_writer_loop_error {err}")
                finally:
                    self.write_queue.task_done()
    
        def _write_full_block(self, block):
            if self.full_writer is None:
                return
            self.full_writer.write(block)
            self.full_blocks_since_flush += 1
            if self.full_blocks_since_flush >= 10:
                self.full_writer.flush()
                self.full_blocks_since_flush = 0
    
        def _write_segment_clips(self):
            if not G_RECORDING_AVAILABLE:
                return
            if not self.full_path.exists():
                self._log_event("segment_clip_failed", details=f"missing_full_session={self.full_path}")
                return
            try:
                with _gurung_sf.SoundFile(str(self.full_path), mode="r") as full_audio:
                    available_frames = len(full_audio)
                    for segment in list(self.segments):
                        if segment.get("onset_sample") is None:
                            continue
                        start_sample = max(0, int(segment.get("onset_sample") or 0))
                        requested_end_sample = int(segment.get("end_sample") or available_frames)
                        requested_end_sample = max(start_sample, requested_end_sample)
                        clip_start = min(start_sample, available_frames)
                        clip_end = min(requested_end_sample, available_frames)
                        full_audio.seek(clip_start)
                        audio = full_audio.read(clip_end - clip_start, dtype="float32", always_2d=True)
                        _gurung_sf.write(str(segment["path"]), audio, full_audio.samplerate)
                        status = "written"
                        notes = g_text(segment.get("notes", ""))
                        if requested_end_sample > available_frames:
                            status = "written_truncated_at_experiment_stop"
                            suffix = f"truncated_end_sample={requested_end_sample};available_frames={available_frames}"
                            notes = f"{notes} {suffix}".strip()
                        with self.lock:
                            segment["clip_start_sample"] = clip_start
                            segment["clip_end_sample"] = clip_end
                            segment["written"] = True
                            segment["written_core_time"] = core.getTime()
                            segment["n_frames"] = int(audio.shape[0])
                            segment["status"] = status
                            segment["notes"] = notes
                        self._log_event(
                            "segment_written",
                            segment,
                            sample_index=clip_start,
                            details=f"frames={int(audio.shape[0])} clip={clip_start}:{clip_end}",
                        )
            except Exception as err:
                with self.lock:
                    for segment in self.segments:
                        if not segment.get("written"):
                            segment["status"] = "clip_failed"
                            segment["notes"] = f"{segment.get('notes', '')} clip_failed:{err}".strip()
                self._log_event("segment_clip_failed", details=str(err))
            self._write_segments_log()
    
        def _close_full_writer(self):
            writer = self.full_writer
            self.full_writer = None
            if writer is None:
                return
            try:
                writer.flush()
            except Exception:
                pass
            try:
                writer.close()
                self._log_event("full_session_closed", sample_index=self._total_frames(), details=str(self.full_path))
            except Exception as err:
                g_log(f"rec_full_writer_close_failed {err}")
    
        def _time_field(self, time_info, name):
            try:
                value = getattr(time_info, name)
            except Exception:
                try:
                    value = time_info[name]
                except Exception:
                    return None
            try:
                return float(value)
            except Exception:
                return None
    
        def _stream_time(self):
            with self.lock:
                return self._stream_time_unlocked()
    
        def _stream_time_unlocked(self):
            try:
                if self.stream is not None:
                    return float(self.stream.time)
            except Exception:
                pass
            return None
    
        def _sample_index_now(self, stream_time=None, event_core_time=None):
            with self.lock:
                total_frames = self.total_frames
                last_callback_core_time = self.last_callback_core_time
                last_callback_end_sample = self.last_callback_end_sample
                can_estimate = self.stream is not None and not self.finalized
            if can_estimate and last_callback_core_time is not None:
                if event_core_time is None:
                    event_core_time = core.getTime()
                estimate = int(round(last_callback_end_sample + ((event_core_time - last_callback_core_time) * self.sample_rate)))
                return max(0, estimate)
            return int(total_frames)
    
        def _total_frames(self):
            with self.lock:
                return int(self.total_frames)
    
        def _find_segment_unlocked(self, segment_id):
            for segment in self.segments:
                if segment.get("id") == segment_id:
                    return segment
            return None
    
        def _open_event_log(self):
            self.event_fields = (
                "event_index",
                "event_type",
                "segment_id",
                "stem",
                "path",
                "core_time",
                "stream_time",
                "sample_index",
                "details",
            )
            self.segment_fields = (
                "segment_id",
                "stem",
                "path",
                "full_session_path",
                "status",
                "requested_core_time",
                "requested_stream_time",
                "requested_sample",
                "onset_core_time",
                "onset_stream_time",
                "onset_sample",
                "stop_core_time",
                "stop_stream_time",
                "stop_sample",
                "post_pad_sec",
                "end_sample",
                "clip_start_sample",
                "clip_end_sample",
                "written_core_time",
                "n_frames",
                "notes",
            )
            try:
                self.event_handle = self.events_path.open("w", encoding="utf-8", newline="")
                self.event_writer = csv.DictWriter(self.event_handle, fieldnames=self.event_fields, lineterminator="\n")
                self.event_writer.writeheader()
                self.event_handle.flush()
            except Exception as err:
                g_log(f"recording_event_log_open_failed {err}")
                self.event_handle = None
                self.event_writer = None
            self._write_segments_log()
    
        def _format_value(self, value):
            if value is None:
                return ""
            if isinstance(value, float):
                return f"{value:.6f}"
            return str(value)
    
        def _log_event(self, event_type, segment=None, sample_index=None, stream_time=None, details=""):
            core_time = core.getTime()
            if stream_time is None:
                stream_time = self._stream_time()
            if sample_index is None:
                sample_index = self._sample_index_now(stream_time=stream_time, event_core_time=core_time)
            segment_id = ""
            stem = ""
            path = ""
            if segment is not None:
                segment_id = segment.get("id", "")
                stem = segment.get("stem", "")
                path = segment.get("path", "")
            with self.log_lock:
                self.event_index += 1
                row = {
                    "event_index": self.event_index,
                    "event_type": event_type,
                    "segment_id": segment_id,
                    "stem": stem,
                    "path": path,
                    "core_time": self._format_value(core_time),
                    "stream_time": self._format_value(stream_time),
                    "sample_index": self._format_value(sample_index),
                    "details": details,
                }
                try:
                    if self.event_writer is not None:
                        self.event_writer.writerow(row)
                        self.event_handle.flush()
                except Exception as err:
                    g_log(f"recording_event_log_write_failed {err}")
            g_log(f"recording_event {event_type} segment={segment_id} sample={row['sample_index']} {details}")
    
        def _segment_row(self, segment):
            row = {}
            for field in self.segment_fields:
                if field == "segment_id":
                    value = segment.get("id")
                else:
                    value = segment.get(field)
                row[field] = self._format_value(value)
            return row
    
        def _write_segments_log(self):
            try:
                with self.log_lock:
                    with self.segments_path.open("w", encoding="utf-8", newline="") as handle:
                        writer = csv.DictWriter(handle, fieldnames=self.segment_fields, lineterminator="\n")
                        writer.writeheader()
                        with self.lock:
                            rows = [self._segment_row(segment) for segment in self.segments]
                        writer.writerows(rows)
            except Exception as err:
                g_log(f"recording_segments_log_write_failed {err}")
    
        def _wait_for_pending_tail(self):
            deadline = core.getTime() + G_RECORDING_STOP_GRACE_SEC + 0.2
            while core.getTime() < deadline:
                with self.lock:
                    pending = [
                        int(segment["end_sample"])
                        for segment in self.segments
                        if segment.get("end_sample") is not None and not segment.get("written")
                    ]
                    total_frames = self.total_frames
                if not pending or max(pending) <= total_frames:
                    return
                core.wait(0.02)
    
        def _force_close_open_segments(self):
            now = core.getTime()
            sample = self._sample_index_now(event_core_time=now)
            with self.lock:
                for segment in self.segments:
                    if segment.get("written"):
                        continue
                    if segment.get("onset_sample") is None:
                        segment["onset_sample"] = segment.get("requested_sample", sample)
                        segment["onset_core_time"] = segment.get("requested_core_time", now)
                        segment["onset_stream_time"] = segment.get("requested_stream_time")
                        segment["notes"] = "forced_onset_during_cleanup"
                    if segment.get("end_sample") is None:
                        segment["stop_core_time"] = now
                        segment["stop_stream_time"] = self._stream_time_unlocked()
                        segment["stop_sample"] = sample
                        segment["post_pad_sec"] = 0.0
                        segment["end_sample"] = max(int(segment["onset_sample"]), int(sample))
                        segment["status"] = "forced_stop_during_cleanup"
    
        def finalize(self, wait_for_post_pad=True):
            with self.lock:
                if self.finalized:
                    return
                self.finalized = True
            self._log_event("recording_finalize_start", details=f"wait_for_post_pad={wait_for_post_pad}")
            if self.current_segment is not None:
                self.stop(grace_sec=0.0)
            if wait_for_post_pad:
                self._wait_for_pending_tail()
            stream = self.stream
            self.stream = None
            if stream is not None:
                try:
                    g_log("rec_stream_stop_start")
                    stream.stop()
                    g_log("rec_stream_stop_done")
                except Exception as err:
                    g_log(f"rec_stream_stop_failed {err}")
                try:
                    stream.close()
                    g_log("rec_stream_close_done")
                except Exception as err:
                    g_log(f"rec_stream_close_failed {err}")
            self._force_close_open_segments()
            try:
                self.write_queue.join()
            except Exception as err:
                g_log(f"rec_write_queue_join_failed {err}")
            self.write_queue.put(None)
            try:
                self.write_queue.join()
            except Exception:
                pass
            try:
                self.writer.join(timeout=2.0)
            except Exception:
                pass
            self._write_segment_clips()
            self._write_segments_log()
            self._log_event("recording_finalize_done", details=f"writer_error={self.writer_error}")
            try:
                if self.event_handle is not None:
                    self.event_handle.flush()
                    self.event_handle.close()
            except Exception:
                pass
    
        def abort(self):
            self.finalize(wait_for_post_pad=False)
    
    
    def g_cleanup(wait_for_post_pad=True):
        try:
            G_RECORDER.finalize(wait_for_post_pad=wait_for_post_pad)
        except Exception as err:
            g_log(f"Recorder cleanup failed: {err}")
    
    
    G_RECORDINGS_DIR = g_session_recordings_dir()
    G_RECORDER = GRecorder(G_RECORDINGS_DIR)
    
    
    def g_abort_and_quit():
        g_cleanup(wait_for_post_pad=True)
        core.quit()
    
    
    try:
        event.globalKeys.add(key="escape", func=g_abort_and_quit, name="gurung_escape_quit")
    except Exception as _gurung_global_key_error:
        g_log(f"Global escape key was not registered: {_gurung_global_key_error}")
    
    
    try:
        runAtExit.append(g_cleanup)
    except Exception as _gurung_run_at_exit_error:
        g_log(f"Could not register recorder runAtExit cleanup: {_gurung_run_at_exit_error}")
    
    
    try:
        atexit.register(g_cleanup)
    except Exception as _gurung_atexit_error:
        g_log(f"Could not register recorder atexit cleanup: {_gurung_atexit_error}")
    
    
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
    instruction_audio = None
    instruction_started = False
    instruction_clock = core.Clock()
    instruction_duration = 0.0
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
            g_abort_and_quit()
        if "return" in keys:
            if instruction_audio:
                instruction_audio.stop()
            instruction_audio = g_play_audio("Audio/sequence_instr.wav")
            instruction_started = True
            instruction_clock.reset()
            instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
            event.clearEvents()
        elif "space" in keys:
            if not instruction_started:
                instruction_audio = g_play_audio("Audio/sequence_instr.wav")
                instruction_started = True
                instruction_clock.reset()
                instruction_duration = g_float(instruction_audio.getDuration() if instruction_audio else 0, 0.0)
                event.clearEvents()
            else:
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
        practice_between_audio_duration = 0.0
        practice_between_is_question = bool(practice_between_audio_value and not practice_between_uses_speaker)
        practice_between_audio_done = not practice_between_is_question
        practice_listener_clock = core.Clock()
        practice_listener_audio_file = ""
        practice_listener_stem = ""
        practice_after_placeholder = None
        practice_after_between_image = ""
        practice_after_between_clock = core.Clock()
        practice_after_between_lock = 0.0
        practice_after_between_audio_duration = 0.0
        practice_after_question_audio_done = True
        practice_after_listener_clock = core.Clock()
        practice_after_listener_audio_file = ""
        practice_audio = None
        practice_audio_value = ""
        practice_audio_clock = core.Clock()
        practice_audio_duration = 0
        practice_segment_audio_value = ""
        practice_segment_audio_started = False
        practice_segment_audio_lock = 0.0
        if practice_between_audio_value:
            practice_between_audio = g_play_audio(practice_between_audio_value)
            practice_between_audio_duration = g_float(practice_between_audio.getDuration() if practice_between_audio else 0, 0.0)
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
                if practice_between_is_question and not practice_between_audio_done and practice_between_clock.getTime() >= practice_between_audio_duration:
                    if practice_between_audio:
                        practice_between_audio.stop()
                    practice_between_audio = None
                    practice_listener_stem = g_listener_practice_stem(practice_previous_trial_index)
                    practice_listener_audio_file = G_RECORDER.start(practice_listener_stem, subdir=G_LISTENER_RESPONSE_DIRNAME)
                    practice_listener_clock.reset()
                    practice_between_audio_done = True
                    event.clearEvents()
                keys = event.getKeys(keyList=["space", "return", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if practice_between_uses_speaker and "return" in key_names:
                    if practice_between_audio:
                        practice_between_audio.stop()
                    practice_between_audio = g_play_audio(practice_between_audio_value)
                    practice_between_audio_duration = g_float(practice_between_audio.getDuration() if practice_between_audio else 0, 0.0)
                    practice_between_clock.reset()
                    event.clearEvents()
                if practice_between_uses_speaker:
                    practice_between_can_continue = "space" in key_names
                elif practice_between_is_question:
                    practice_between_can_continue = (
                        practice_between_audio_done
                        and "space" in key_names
                        and practice_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
                    )
                else:
                    practice_between_can_continue = "space" in key_names
                if practice_between_can_continue:
                    if practice_between_is_question:
                        stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                        if stopped_listener_file:
                            practice_listener_audio_file = stopped_listener_file
                        thisExp.addData("practice_listener_reference_trial", practice_previous_trial_index)
                        thisExp.addData("practice_listener_response_audio", practice_listener_audio_file)
                        thisExp.addData("practice_listener_response_rt", practice_listener_clock.getTime())
                    if practice_between_audio:
                        practice_between_audio.stop()
                    practice_between_audio = None
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
                G_RECORDER.mark_onset_on_flip()
                if practice_segment_audio_value and not practice_segment_audio_started:
                    practice_audio_value = practice_segment_audio_value
                    practice_audio = g_play_audio(practice_audio_value)
                    practice_audio_clock.reset()
                    practice_segment_audio_lock = g_float(practice_audio.getDuration(), 0) if practice_audio else 0
                    practice_segment_audio_started = True
                    thisExp.addData(f"practice_seg{practice_segment + 1}_onset_audio", g_path(practice_audio_value))
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if "space" in key_names and practice_audio_clock.getTime() >= practice_segment_audio_lock:
                    if practice_audio:
                        practice_audio.stop()
                    practice_audio = None
                    audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
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
                            practice_after_between_audio_duration = g_float(practice_audio.getDuration() if practice_audio else 0, 0.0)
                            practice_after_between_clock.reset()
                            practice_after_question_audio_done = False
                            practice_after_listener_audio_file = ""
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
                if not practice_after_question_audio_done and practice_audio_clock.getTime() >= practice_after_between_audio_duration:
                    if practice_audio:
                        practice_audio.stop()
                    practice_audio = None
                    practice_after_listener_audio_file = G_RECORDER.start(
                        g_listener_practice_stem(G_PRACTICE_TRIAL_INDEX),
                        subdir=G_LISTENER_RESPONSE_DIRNAME,
                    )
                    practice_after_listener_clock.reset()
                    practice_after_question_audio_done = True
                    event.clearEvents()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if (
                    "space" in key_names
                    and practice_after_question_audio_done
                    and practice_after_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
                ):
                    stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                    if stopped_listener_file:
                        practice_after_listener_audio_file = stopped_listener_file
                    thisExp.addData("practice_listener_reference_trial", G_PRACTICE_TRIAL_INDEX)
                    thisExp.addData("practice_listener_response_audio", practice_after_listener_audio_file)
                    thisExp.addData("practice_listener_response_rt", practice_after_listener_clock.getTime())
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
        keys = event.getKeys(keyList=["space", "return", "escape"])
        if "escape" in keys:
            g_abort_and_quit()
        if "return" in keys:
            if practice_done_audio:
                practice_done_audio.stop()
            practice_done_audio = g_play_audio("Audio/practice_end.wav")
            practice_done_clock.reset()
            practice_done_duration = g_float(practice_done_audio.getDuration() if practice_done_audio else 0, 0.0)
            event.clearEvents()
        if "space" in keys:
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
        main_listener_reference = dict(G_LAST_MAIN_TRIAL_INFO) if G_LAST_MAIN_TRIAL_INFO else {}
        main_between_audio_duration = 0.0
        main_between_audio_done = not bool(main_between_audio_value)
        main_listener_clock = core.Clock()
        main_listener_audio_file = ""
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
            main_between_audio_duration = g_float(main_between_audio.getDuration() if main_between_audio else 0, 0.0)
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
                if main_between_audio_value and not main_between_audio_done and main_between_clock.getTime() >= main_between_audio_duration:
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    main_listener_audio_file = G_RECORDER.start(
                        g_listener_main_stem(main_listener_reference),
                        subdir=G_LISTENER_RESPONSE_DIRNAME,
                    )
                    main_listener_clock.reset()
                    main_between_audio_done = True
                    event.clearEvents()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if main_between_audio_value:
                    main_between_can_continue = (
                        main_between_audio_done
                        and "space" in key_names
                        and main_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
                    )
                else:
                    main_between_can_continue = "space" in key_names and main_between_clock.getTime() >= main_audio_lock
                if main_between_can_continue:
                    if main_between_audio_value:
                        stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                        if stopped_listener_file:
                            main_listener_audio_file = stopped_listener_file
                        thisExp.addData("listener_reference_main_trial_index", g_int(main_listener_reference.get("trial_index", 0), 0))
                        thisExp.addData("listener_reference_dataset_number", g_int(main_listener_reference.get("dataset_number", 0), 0))
                        thisExp.addData("listener_reference_condition_id", g_text(main_listener_reference.get("condition_id", "")))
                        thisExp.addData("listener_response_audio", main_listener_audio_file)
                        thisExp.addData("listener_response_rt", main_listener_clock.getTime())
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                G_RECORDER.mark_onset_on_flip()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if "space" in key_names:
                    audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
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
        G_LAST_MAIN_TRIAL_INFO = {
            "trial_index": G_MAIN_TRIAL_INDEX,
            "dataset_number": main_dataset_number,
            "condition_id": main_condition_id,
        }
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
            g_abort_and_quit()
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
        main_listener_reference = dict(G_LAST_MAIN_TRIAL_INFO) if G_LAST_MAIN_TRIAL_INFO else {}
        main_between_audio_duration = 0.0
        main_between_audio_done = not bool(main_between_audio_value)
        main_listener_clock = core.Clock()
        main_listener_audio_file = ""
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
            main_between_audio_duration = g_float(main_between_audio.getDuration() if main_between_audio else 0, 0.0)
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
                if main_between_audio_value and not main_between_audio_done and main_between_clock.getTime() >= main_between_audio_duration:
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    main_listener_audio_file = G_RECORDER.start(
                        g_listener_main_stem(main_listener_reference),
                        subdir=G_LISTENER_RESPONSE_DIRNAME,
                    )
                    main_listener_clock.reset()
                    main_between_audio_done = True
                    event.clearEvents()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if main_between_audio_value:
                    main_between_can_continue = (
                        main_between_audio_done
                        and "space" in key_names
                        and main_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
                    )
                else:
                    main_between_can_continue = "space" in key_names and main_between_clock.getTime() >= main_audio_lock
                if main_between_can_continue:
                    if main_between_audio_value:
                        stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                        if stopped_listener_file:
                            main_listener_audio_file = stopped_listener_file
                        thisExp.addData("listener_reference_main_trial_index", g_int(main_listener_reference.get("trial_index", 0), 0))
                        thisExp.addData("listener_reference_dataset_number", g_int(main_listener_reference.get("dataset_number", 0), 0))
                        thisExp.addData("listener_reference_condition_id", g_text(main_listener_reference.get("condition_id", "")))
                        thisExp.addData("listener_response_audio", main_listener_audio_file)
                        thisExp.addData("listener_response_rt", main_listener_clock.getTime())
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                G_RECORDER.mark_onset_on_flip()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if "space" in key_names:
                    audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
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
        G_LAST_MAIN_TRIAL_INFO = {
            "trial_index": G_MAIN_TRIAL_INDEX,
            "dataset_number": main_dataset_number,
            "condition_id": main_condition_id,
        }
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
            g_abort_and_quit()
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
        main_listener_reference = dict(G_LAST_MAIN_TRIAL_INFO) if G_LAST_MAIN_TRIAL_INFO else {}
        main_between_audio_duration = 0.0
        main_between_audio_done = not bool(main_between_audio_value)
        main_listener_clock = core.Clock()
        main_listener_audio_file = ""
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
            main_between_audio_duration = g_float(main_between_audio.getDuration() if main_between_audio else 0, 0.0)
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
                if main_between_audio_value and not main_between_audio_done and main_between_clock.getTime() >= main_between_audio_duration:
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    main_listener_audio_file = G_RECORDER.start(
                        g_listener_main_stem(main_listener_reference),
                        subdir=G_LISTENER_RESPONSE_DIRNAME,
                    )
                    main_listener_clock.reset()
                    main_between_audio_done = True
                    event.clearEvents()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if main_between_audio_value:
                    main_between_can_continue = (
                        main_between_audio_done
                        and "space" in key_names
                        and main_listener_clock.getTime() >= G_LISTENER_RESPONSE_MIN_SEC
                    )
                else:
                    main_between_can_continue = "space" in key_names and main_between_clock.getTime() >= main_audio_lock
                if main_between_can_continue:
                    if main_between_audio_value:
                        stopped_listener_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                        if stopped_listener_file:
                            main_listener_audio_file = stopped_listener_file
                        thisExp.addData("listener_reference_main_trial_index", g_int(main_listener_reference.get("trial_index", 0), 0))
                        thisExp.addData("listener_reference_dataset_number", g_int(main_listener_reference.get("dataset_number", 0), 0))
                        thisExp.addData("listener_reference_condition_id", g_text(main_listener_reference.get("condition_id", "")))
                        thisExp.addData("listener_response_audio", main_listener_audio_file)
                        thisExp.addData("listener_response_rt", main_listener_clock.getTime())
                    if main_between_audio:
                        main_between_audio.stop()
                    main_between_audio = None
                    thisExp.addData("between_rt", main_between_clock.getTime())
                    g_release_fullscreen_image(main_placeholder)
                    main_placeholder = None
                    main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
                    main_phase = "segment"
                    main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
                    G_RECORDER.start(main_stem)
                    event.clearEvents()
            elif main_phase == "segment":
                g_draw_sequence(main_images, main_arrows, main_segment + 1)
                G_RECORDER.mark_onset_on_flip()
                keys = event.getKeys(keyList=["space", "escape"], timeStamped=core.monotonicClock)
                key_names = g_key_names(keys)
                if "escape" in key_names:
                    g_abort_and_quit()
                if "space" in key_names:
                    audio_file = G_RECORDER.stop(event_core_time=g_key_time(keys, "space"))
                    seg = main_segment + 1
                    thisExp.addData(f"seg{seg}_role", main_roles[main_segment])
                    thisExp.addData(f"seg{seg}_audio", audio_file)
                    if main_segment >= len(main_images) - 1:
                        continueRoutine = False
                    else:
                        main_segment += 1
                        main_stem = f"{expInfo['participant']}_main_trial{G_MAIN_TRIAL_INDEX:03d}_imageset{main_dataset_number:02d}_condition_{main_condition_id}_pic{main_segment + 1:02d}_{main_roles[main_segment]}"
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
        G_LAST_MAIN_TRIAL_INFO = {
            "trial_index": G_MAIN_TRIAL_INDEX,
            "dataset_number": main_dataset_number,
            "condition_id": main_condition_id,
        }
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
    finish_image = visual.ImageStim(win, image=g_path("Stimuli/finish.png"), pos=(0, 0), size=(0.55, 0.275), interpolate=True)
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
    # stop any playback components
    if thisExp.currentRoutine is not None:
        for comp in thisExp.currentRoutine.getPlaybackComponents():
            comp.stop()
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
