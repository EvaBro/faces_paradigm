# -*- coding: utf-8 -*-
"""
Created on Mon Apr 13 11:17:25 2026

@author: Claude AI supervised by Eva Broeders
"""

import os
import random
from PIL import Image, ImageFilter

os.chdir(os.path.dirname(os.path.abspath(__file__))) 


# --- Parameters ---
input_folder = r'C:\Experiments\TaylorLab\FacesNormalAndScrambled\Faces_original'
output_folder = r'C:\Experiments\TaylorLab\FacesNormalAndScrambled\Faces_scrambled'

GRID_SIZE = 8          # 8x8 grid
MOSAIC_CELL_SIZE = 15  # pixels
BLUR_RADIUS = 5       # pixels

os.makedirs(output_folder, exist_ok=True)

def apply_mosaic(img, cell_size):
    """Pixelate image by downscaling then upscaling with nearest-neighbor."""
    w, h = img.size
    small = img.resize((w // cell_size, h // cell_size), Image.BOX)
    return small.resize((w, h), Image.NEAREST)

def scramble_face(img):
    w, h = img.size
    cell_w = w // GRID_SIZE
    cell_h = h // GRID_SIZE

    # Crop into 8x8 grid of cells
    cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            left   = col * cell_w
            upper  = row * cell_h
            right  = left + cell_w
            lower  = upper + cell_h
            cells.append(img.crop((left, upper, right, lower)))

    # Shuffle cells randomly
    random.shuffle(cells)

    # Reassemble into new image
    scrambled = Image.new(img.mode, (cell_w * GRID_SIZE, cell_h * GRID_SIZE))
    for i, cell in enumerate(cells):
        row = i // GRID_SIZE
        col = i % GRID_SIZE
        scrambled.paste(cell, (col * cell_w, row * cell_h))

    # Apply mosaic
    scrambled = apply_mosaic(scrambled, MOSAIC_CELL_SIZE)

    # Apply Gaussian blur
    scrambled = scrambled.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

    return scrambled

# --- Process all images ---
valid_extensions = ('.bmp', '.jpg', '.jpeg', '.png', '.tif', '.tiff')

for img_file in os.listdir(input_folder):
    if img_file.lower().endswith(valid_extensions) and 'Copy' not in img_file:
        input_path = os.path.join(input_folder, img_file)
        output_path = os.path.join(output_folder, img_file.split(sep='.')[0] + '_scrambled.bmp')
        print('INPUT: ' + input_path)
        print('OUTPUT: ' + output_path)
    
    
        img = Image.open(input_path).convert('RGB')
        scrambled = scramble_face(img)
        scrambled.save(output_path)
        print(f'Processed: {img_file}')

