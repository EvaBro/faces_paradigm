# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 12:10:46 2026

@author: Eva Broeders

Faces paradigm. 
Trials consist of happy and angry faces and corresponding scrambled faces which serve as control stimuli. 
Participants are instructed to press the red button if they see a bird. 

Optitrack is triggered automatically once the experiment starts, and it stops automatically when the experiment ends. 
The take name is also set automatically, with the datetime at the end so existing takes cannot be overwritten. 

Controls:
    - red button:   button press (linked to trigger)
    - space:        enter trial loop after showing instruction screen / button press during trial loop (linked to trigger)
    - Escape:       quits the experiment completely. Also works while paused
    - p:            pauses the experiment
    - r:            resumes the experiment after pause
    
Outputs: 
    - A log file will be written to a folder of your choice. The log file 
      contains the exact file names of the images that were presented, as well 
      as the number of frame drops that occurred during each trial, if any. 
      E.g. having a browser window open with some graphics playing in the 
      background will dramatically affect timing.
    - (Optional) Optitrack recording, starts and stops automatically. 
      If you want this functionality, make sure the Motive software is running and set up 
"""

import numpy as np
from enum import IntFlag
from psychopy import visual, event, core
import os
import sys
import pandas as pd
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent
sys.path.append(str(BASE_DIR.parent / 'stim_utils'))
import OptitrackUtils as opti
import ExperimentUtils as utils


#%% System-dependent parameters - change these as needed

# Do not forget to set up triggers and button box in the ExperimentUtils module

# File paths
faces_folder = BASE_DIR / 'Faces_original' 
scrambled_folder = BASE_DIR / 'Faces_scrambled' 
target_folder = BASE_DIR / 'Target_images'
instruction = BASE_DIR / 'Instructions' / 'Instruction_Faces.png'
log_folder = BASE_DIR.parent / 'OPM07 - UKRI/logs' 

framerate = 60 # Hz, System-dependent

# Triggers
class PortCodes(IntFlag):
    reset = 0           # Reset all ports
    optitrack = 2       # Trigger 2 reserved for Optitrack
    angry_face = 4      # Trigger 3 for angry face
    scrambled_face = 8  # Trigger 4 for scrambled face image
    happy_face = 16     # Trigger 5 for happy face
    target_image = 32   # Trigger 6 for target image
    button = 64         # Trigger 7 for button press
    all = 255           # Send trigger to all ports

# Screen on which video is displayed
screen_idx=0 

# Whether or not to use head motion tracking, set to False if you don't have Optitrack
optitrack = False

#%% General parameters

# Timing parameters
num_faces = 80 # number of face images
num_scrambled = 80 # same number of scrambled faces
num_targets = 30 # number of target images
stimulus_duration = 0.5 # duration of face presentation s
fixation_duration = 1.25 # average duration of fixation
max_jitter = 0.2; # jitter duration in s, effective fixation duration will be between [fixation_duration - max_jitter, fixation_duration + max_jitter]
ready_duration = 3 # duration of ready set go sequence
end_duration = 2 # duration of the final message in s

# Image width in pixels
target_size = 506
    
#%% Logistics

# Apply jitter to isi interval
num_trials = num_faces + num_scrambled + num_targets
jitters = np.random.uniform(-max_jitter, max_jitter, num_trials)
fixation_durations = fixation_duration + jitters

# Convert timings to number of frames 
num_fixation_frames = np.round(fixation_durations*framerate).astype(int)
num_image_frames = np.round(stimulus_duration*framerate).astype(int)

# Get images
face_files = utils.create_img_list(faces_folder)
scrambled_files = utils.create_img_list(scrambled_folder)
target_files = utils.create_img_list(target_folder)

#%% Set up window and hardware

# Create a window
win_size = utils.get_window_size(screen_idx) 
window = utils.create_window(win_size, screen_idx)

# Set up Optitrack
if optitrack:
    client = opti.setup()
else:
    client = None

#%% Create screens
intro_screen = visual.ImageStim(window, pos=(0,0), image=instruction, size=win_size)

ready_screen = visual.TextStim(win=window, text="Ready", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

set_screen = visual.TextStim(win=window, text="Set", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

go_screen = visual.TextStim(win=window, text="Go!", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')

fixation = utils.create_fixation_screen(window)

end_screen = visual.TextStim(win=window, text="The end.\nThank you for playing!", color='white',
                               height=70, alignText='center', anchorHoriz='center',
                               anchorVert='center')


#%% Display instructions
intro_screen.draw()
window.flip()

#%% Meanwhile, load the stimuli and randomize their order
trial_list = face_files + scrambled_files + target_files
np.random.shuffle(trial_list)

is_target = [1 if 'bird' in img.name else 0 for img in trial_list]
is_scrambled = [1 if '_scrambled' in img.name else 0 for img in trial_list]
is_happy = [1 if ('_HA_' in img.name) and ('scrambled' not in img.name) else 0 for img in trial_list]
is_angry = [1 if ('_AN_' in img.name) and ('scrambled' not in img.name) else 0 for img in trial_list]

trigger_list = np.zeros(num_trials, dtype=int)
trigger_list[np.array(is_target).astype(bool)]    = PortCodes.target_image
trigger_list[np.array(is_scrambled).astype(bool)] = PortCodes.scrambled_face
trigger_list[np.array(is_happy).astype(bool)]     = PortCodes.happy_face
trigger_list[np.array(is_angry).astype(bool)]     = PortCodes.angry_face

# Create stim objects
stim = [visual.ImageStim(window, pos=(0,0), image=i) for i in trial_list]
for s in range(num_trials):
    if is_target[s]:
        stim[s].size = target_size

#%% Logging
log_df = pd.DataFrame({'trial_image': [img.name for img in trial_list]})
log_df['trigger'] = trigger_list
log_df['is_happy'] = is_happy
log_df['is_angry'] = is_angry
log_df['is_scrambled'] = is_scrambled
log_df['is_target'] = is_target
log_df['trial_completed'] = False

def save_data(): # This is not pretty, but it works
    now = datetime.now()
    save_folder = log_folder / now.strftime("%Y%m%d")
    os.makedirs(save_folder, exist_ok=True)
    log_df.to_csv(save_folder / ('logFaces_' + now.strftime("%Y-%m-%d_%H-%M-%S") + '.csv'), index=False)

#%% Wait until ready
event.clearEvents() # Clear the keyboard events buffer to make sure previous button presses are ignored

print('Press space when ready to start.')
ready = False
while not ready:
    keys = event.getKeys()
    if 'escape' in keys:
        window.close()
        core.quit()
    if 'space' in keys:
        ready = True
        
# Start Optitrack
if optitrack: 
    opti.set_take_name(client, 'Faces')
    opti.start_recording(client)

# Present get ready screens
ready_screen.draw()
window.flip()
core.wait(ready_duration/3)

set_screen.draw()
window.flip()
core.wait(ready_duration/3)

go_screen.draw()
window.flip()
core.wait(ready_duration/3)


#%% Trial loop

# Initialize
buttonClock = core.Clock()
prev_button_state = False
prev_button_time = float('-inf')
window.setRecordFrameIntervals(True) # Enable frame timing diagnostics
drops_before = 0

for trial_idx in range(num_trials):
    
    # Present stimulus
    window.callOnFlip(utils.send_trigger, PortCodes(int(trigger_list[trial_idx])))
    for frame_idx in range(num_image_frames):
        stim[trial_idx].draw()
        window.flip()
        prev_button_state, prev_button_time = utils.check_keys(window, PortCodes, buttonClock, prev_button_state, prev_button_time, client, save_function=save_data)
    
    log_df.loc[trial_idx, 'dropped_frames_stim'] = window.nDroppedFrames - drops_before
    drops_before = window.nDroppedFrames
    
    # Present fixation
    for frame_idx in range(num_fixation_frames[trial_idx]):
        fixation.draw()
        window.flip()
        prev_button_state, prev_button_time = utils.check_keys(window, PortCodes, buttonClock, prev_button_state, prev_button_time, client, save_function=save_data)
    
    log_df.loc[trial_idx, 'trial_completed'] = True
    log_df.loc[trial_idx, 'dropped_frames_fix'] = window.nDroppedFrames - drops_before
    drops_before = window.nDroppedFrames

# Draw end screen
end_screen.draw()
window.flip()
core.wait(end_duration)

# Quit and save log
utils.print_frame_timing_diagnostics(window)
utils.quit_experiment(window,client,save_data)
