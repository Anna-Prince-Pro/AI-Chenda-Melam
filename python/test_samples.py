import pygame
import time
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

dhum_path = os.path.join(BASE_DIR, "sounds", "dhum.wav")
ta_path = os.path.join(BASE_DIR, "sounds", "ta.wav")

# ---------------------------------
# RHYTHM SETTINGS
# ---------------------------------

BPM = 108

# Duration of one beat in seconds
BEAT = 60 / BPM

print("Initializing audio...")

pygame.mixer.init()

dhum = pygame.mixer.Sound(dhum_path)
ta = pygame.mixer.Sound(ta_path)

# ---------------------------------
# TEST PATTERN
# ---------------------------------

pattern = [
    ("DHUM", 1.0),
    ("TA", 0.5),
    ("TA", 0.5),
    ("DHUM", 1.0),
    ("TA", 0.5),
    ("TA", 0.5),
]

print(f"Playing at {BPM} BPM...")
print("Pattern:", " ".join([beat[0] for beat in pattern]))

# ---------------------------------
# PLAY RHYTHM
# ---------------------------------

start_time = time.perf_counter()

for sound_name, beat_length in pattern:

    # Play the correct sound
    if sound_name == "DHUM":
        dhum.play()
    elif sound_name == "TA":
        ta.play()

    # Wait according to BPM
    time.sleep(BEAT * beat_length)

# Wait for final sound
time.sleep(1)

pygame.mixer.quit()

print("Done!")