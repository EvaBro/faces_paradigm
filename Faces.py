# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 12:10:46 2026

@author: Eva Broeders

Faces paradigm. 
Trials consist of happy and angry faces and corresponding scrambled faces which serve as control stimuli. 
Participants are instructed to press the red button if they see ... ? 

Controls:
    - red button:   button press (linked to trigger)
    - space:        enter trial loop after showing instruction screen / button press during trial loop (linked to trigger)
    - Escape:       quits the experiment completely. Also works while paused
    - p:            pauses the experiment
    - r:            resumes the experiment after pause

"""

import FacesUtils as utils
import numpy as np
from enum import IntFlag
from ParallelButtonBox import ButtonBox
from psychopy import visual, event, core
import os

os.chdir(os.path.dirname(os.path.abspath(__file__))) 

#%% Parameters

# Timing parameters
num_faces = 80 # number of face images
num_scrambled = 80 # same number of scrambled faces
num_targets = 30 # number of target images
stimulus_duration = 0.5 # duration of face presentation s
fixation_duration = 1.25 # average duration of fixation
max_jitter = 0.2; # jitter duration in s, effective fixation duration will be between [fixation_duration - max_jitter, fixation_duration + max_jitter]
framerate = 60; # Hz, System-dependent
ready_duration = 3 # duration of ready set go sequence
end_duration = 2 # duration of the final message in s


# File paths
faces_folder = "./Faces_original/"
scrambled_folder = './Faces_scrambled/'
target_image = './Target_images/astronaut.png'
instruction = './Instructions/Instruction_black.png'

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
screen_idx=0 # Should be 0 for stim PC

# Target proportion and settings
init_nontargets = 3 # How many nontarget trials come at the start

# Image sizes

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
target_files = [target_image]*num_targets

#%% Set up window and button box

# Create buttonbox    
btn_box = ButtonBox(address=0xdff8)

# Create a window
win_size = utils.get_window_size(screen_idx) 
window = utils.create_window(win_size, screen_idx)


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

is_target = [1 if img == target_image else 0 for img in trial_list]
is_scrambled = [1 if '_scrambled' in img else 0 for img in trial_list]
is_happy = [1 if ('_HA_' in img) and ('scrambled' not in img) else 0 for img in trial_list]
is_angry = [1 if ('_AN_' in img) and ('scrambled' not in img) else 0 for img in trial_list]

# Create empty stim object - will fill it up during the loop
stim = [visual.ImageStim(window, pos=(0,0), image=i) for i in trial_list]


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

for trial_idx in range(num_trials):
    
    # Present stimulus
    if is_target[trial_idx]:
        window.callOnFlip(utils.send_trigger, PortCodes.target_image)
    elif is_scrambled[trial_idx]:
        window.callOnFlip(utils.send_trigger, PortCodes.scrambled_face)
    elif is_happy[trial_idx]:
        window.callOnFlip(utils.send_trigger, PortCodes.happy_face)
    elif is_angry[trial_idx]: 
        window.callOnFlip(utils.send_trigger, PortCodes.angry_face)

    for frame_idx in range(num_image_frames):
        stim[trial_idx].draw()
        window.flip()
        prev_button_state, prev_button_time = utils.check_keys(window, PortCodes, buttonClock, prev_button_state, prev_button_time)

        
    # Present fixation
    for frame_idx in range(num_fixation_frames[trial_idx]):
        fixation.draw()
        window.flip()
        prev_button_state, prev_button_time = utils.check_keys(window, PortCodes, buttonClock, prev_button_state, prev_button_time)
    
    
# Draw end screen
end_screen.draw()
window.flip()
core.wait(end_duration)

window.close()
core.quit()