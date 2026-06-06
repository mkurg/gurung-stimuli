#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
This experiment was created using PsychoPy3 Experiment Builder (v2026.1.3),
    on Sat Jun  6 21:10:23 2026
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
_fullScr = False
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
        originPath='/Users/matveikurzukov/gurung/psychopy_gurung_v1/gurung_120_v1_lastrun.py',
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
    if win is None:
        # if not given a window to setup, make one
        win = visual.Window(
            size=_winSize, fullscr=_fullScr, screen=-1,
            winType='pyglet', allowGUI=True, allowStencil=False,
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
    
    G_ROOT = Path(_thisDir)
    G_DATA_DIR = G_ROOT / "data"
    G_RECORDINGS_DIR = G_ROOT / "recordings"
    G_DATA_DIR.mkdir(exist_ok=True)
    G_RECORDINGS_DIR.mkdir(exist_ok=True)
    G_IMAGE_SIZE = (0.22, 0.35)
    G_ARROW_SIZE = (0.035, 0.035)
    G_STEP = 0.27
    G_MAIN_TRIAL_INDEX = 0
    G_PRACTICE_TRIAL_INDEX = 0
    G_SPEAKER = None
    
    try:
        event.globalKeys.add(key="escape", func=core.quit, name="gurung_escape_quit")
    except Exception as _gurung_global_key_error:
        print("Global escape key was not registered:", _gurung_global_key_error)
    
    
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
    
    
    def g_fullscreen_size(win):
        try:
            return (float(win.size[0]) / float(win.size[1]), 1.0)
        except Exception:
            return (1.5, 1.0)
    
    
    def g_fullscreen_image(win, image_value):
        return visual.ImageStim(
            win,
            image=g_path(image_value),
            pos=(0, 0),
            size=g_fullscreen_size(win),
            interpolate=True,
        )
    
    
    def g_choose_speaker():
        if SpeakerDevice is None:
            return None
        try:
            devices = SpeakerDevice.getAvailableDevices()
        except Exception as err:
            print("Could not list speaker devices:", err)
            return None
        names = [g_text(device.get("deviceName") or device.get("name")) for device in devices]
        print("Available speaker devices:", names)
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
                print("Using speaker device:", speaker.name)
                return speaker
            except Exception as err:
                print(f"Could not open speaker {name!r}:", err)
        print("No usable speaker found; PsychoPy will use its default audio device.")
        return None
    
    
    G_SPEAKER = g_choose_speaker()
    
    
    def g_safe(value):
        text = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))
        while "__" in text:
            text = text.replace("__", "_")
        return text.strip("._") or "item"
    
    
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
    
    
    def g_positions_for_roles(roles):
        target_index = None
        for target_role in ("tr_target", "it_target"):
            if target_role in roles:
                target_index = roles.index(target_role)
                break
        if target_index is None:
            target_index = (len(roles) - 1) / 2
        return [((idx - target_index) * G_STEP, 0) for idx in range(len(roles))]
    
    
    def g_make_sequence(win, roles, paths):
        positions = g_positions_for_roles(roles)
        images = []
        for path, pos in zip(paths, positions):
            images.append(visual.ImageStim(win, image=path, pos=pos, size=G_IMAGE_SIZE, interpolate=True))
        arrows = []
        arrow_path = g_path("Stimuli/arrow.png")
        for left, right in zip(positions, positions[1:]):
            arrows.append(
                visual.ImageStim(
                    win,
                    image=arrow_path,
                    pos=((left[0] + right[0]) / 2, 0),
                    size=G_ARROW_SIZE,
                    interpolate=True,
                )
            )
        return images, arrows
    
    
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
            self.frames = []
            self.path = None
    
        def start(self, stem):
            self.stop()
            if not G_RECORDING_AVAILABLE:
                return ""
            self.frames = []
            self.path = self.root / f"{g_safe(stem)}.wav"
    
            def callback(indata, frames, time_info, status):
                if status:
                    print(status)
                self.frames.append(indata.copy())
    
            self.stream = _gurung_sd.InputStream(
                samplerate=48000,
                channels=1,
                dtype="float32",
                callback=callback,
            )
            self.stream.start()
            return str(self.path)
    
        def stop(self):
            if self.stream is None:
                return ""
            try:
                self.stream.stop()
            except Exception as err:
                print("Recorder stop failed; aborting stream:", err)
                try:
                    self.stream.abort()
                except Exception:
                    pass
            try:
                self.stream.close()
            except Exception as err:
                print("Recorder close failed:", err)
            self.stream = None
            if self.path and self.frames:
                audio = _gurung_np.concatenate(self.frames, axis=0)
                _gurung_sf.write(str(self.path), audio, 48000)
                return str(self.path)
            return ""
    
        def abort(self):
            if self.stream is not None:
                self.stream.abort()
                self.stream.close()
                self.stream = None
    
    
    def g_cleanup():
        try:
            G_RECORDER.abort()
        except Exception as err:
            print("Recorder cleanup failed:", err)
        try:
            if G_SPEAKER is not None:
                G_SPEAKER.close()
        except Exception as err:
            print("Speaker cleanup failed:", err)
    
    
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
        practice_roles, practice_paths = g_roles_and_paths()
        practice_images, practice_arrows = g_make_sequence(win, practice_roles, practice_paths)
        practice_segment = 0
        practice_phase = "between"
        practice_placeholder = g_fullscreen_image(win, between_image)
        practice_between_clock = core.Clock()
        practice_audio = None
        practice_audio_clock = core.Clock()
        practice_audio_duration = 0
        thisExp.addData("practice_trial_index", G_PRACTICE_TRIAL_INDEX)
        thisExp.addData("practice_between_image", g_path(between_image))
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
                if "space" in keys:
                    thisExp.addData("practice_between_rt", practice_between_clock.getTime())
                    practice_phase = "segment"
                    practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                    G_RECORDER.start(practice_stem)
                    event.clearEvents()
            elif practice_phase == "segment":
                g_draw_sequence(practice_images, practice_arrows, practice_segment + 1)
                keys = event.getKeys(keyList=["space", "escape"])
                if "escape" in keys:
                    G_RECORDER.abort()
                    core.quit()
                if "space" in keys:
                    audio_file = G_RECORDER.stop()
                    seg = practice_segment + 1
                    thisExp.addData(f"practice_seg{seg}_role", practice_roles[practice_segment])
                    thisExp.addData(f"practice_seg{seg}_audio", audio_file)
                    if practice_segment >= len(practice_images) - 1:
                        continueRoutine = False
                    else:
                        practice_segment += 1
                        if practice_segment == 2:
                            practice_phase = "practice_audio"
                            practice_audio = g_play_audio("Audio/tsakyali.wav")
                            practice_audio_clock.reset()
                            practice_audio_duration = practice_audio.getDuration() if practice_audio else 0
                        else:
                            practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                            G_RECORDER.start(practice_stem)
                    event.clearEvents()
            elif practice_phase == "practice_audio":
                g_draw_sequence(practice_images, practice_arrows, 2)
                if practice_audio_clock.getTime() >= practice_audio_duration:
                    practice_phase = "segment"
                    practice_stem = f"{expInfo['participant']}_practice_{G_PRACTICE_TRIAL_INDEX:02d}_pic{practice_segment + 1:02d}_{practice_roles[practice_segment]}"
                    G_RECORDER.start(practice_stem)
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
        if practice_audio:
            practice_audio.stop()
        
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
        trialList=data.importConditions('Conds/main_block1.csv'), 
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
        main_roles, main_paths = g_roles_and_paths()
        main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_placeholder = g_fullscreen_image(win, between_image)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(between_image))
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
        trialList=data.importConditions('Conds/main_block2.csv'), 
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
        main_roles, main_paths = g_roles_and_paths()
        main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_placeholder = g_fullscreen_image(win, between_image)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(between_image))
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
        trialList=data.importConditions('Conds/main_block3.csv'), 
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
        main_roles, main_paths = g_roles_and_paths()
        main_images, main_arrows = g_make_sequence(win, main_roles, main_paths)
        main_segment = 0
        main_phase = "between"
        main_between_clock = core.Clock()
        main_between_audio = None
        main_between_audio_value = g_text(globals().get("between_audio", ""))
        main_audio_lock = g_float(globals().get("between_audio_lock_sec", 0), 0.0)
        main_placeholder = g_fullscreen_image(win, between_image)
        main_dataset_number = g_int(globals().get("dataset_number", 0), 0)
        main_condition_id = g_text(globals().get("condition_id", "unknown_condition"))
        if main_between_audio_value:
            main_between_audio = g_play_audio(main_between_audio_value)
        main_between_clock.reset()
        thisExp.addData("main_trial_index", G_MAIN_TRIAL_INDEX)
        thisExp.addData("between_image", g_path(between_image))
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
