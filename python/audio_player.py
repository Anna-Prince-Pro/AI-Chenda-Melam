import pygame
import time
import os

# Initialize audio
pygame.mixer.init()

# Get path to the Chenda audio file
audio_path = os.path.join(
    os.path.dirname(__file__),
    "..",
    "sounds",
    "chenda.ogg"
)

print("Loading Chenda audio...")

# Load the same recording as a Sound object
chenda_sound = pygame.mixer.Sound(audio_path)

print("Audio engine ready!")
print("\nTesting rhythm...")
print("DHUM TA TA DHUM TA TA")

# Temporary test rhythm
pattern = [
    "DHUM", "TA", "TA",
    "DHUM", "TA", "TA"
]

# Temporary BPM
bpm = 108

# Time between beats
beat_duration = 60 / bpm

for beat in pattern:

    print(beat)

    # For now, play the Chenda sound
    chenda_sound.play()

    time.sleep(beat_duration)

print("\nFinished!")
time.sleep(2)

pygame.mixer.quit()