# utils.py

import pygame
import os

def load_image(path):
    img = pygame.image.load(path).convert_alpha()
    return img
