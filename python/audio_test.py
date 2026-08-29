import pygame
import time
import os

pygame.mixer.init()

audio_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "sounds",
    "chenda.ogg"
)

print("Loading Chenda audio...")
pygame.mixer.music.load(audio_path)

print("Playing Chenda Melam! 🥁")
pygame.mixer.music.play()

while pygame.mixer.music.get_busy():
    time.sleep(0.1)

print("Finished playing.")
pygame.mixer.quit()