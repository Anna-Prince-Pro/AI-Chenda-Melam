import pygame
import time
import os
import re


# ---------------------------------
# PROJECT PATHS
# ---------------------------------

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

dhum_path = os.path.join(BASE_DIR, "sounds", "dhum.wav")
ta_path = os.path.join(BASE_DIR, "sounds", "ta.wav")


# ---------------------------------
# INITIALIZE AUDIO
# ---------------------------------

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=256
)

dhum = pygame.mixer.Sound(dhum_path)
ta = pygame.mixer.Sound(ta_path)


# ---------------------------------
# PLAY RHYTHM FUNCTION
# ---------------------------------

def play_rhythm(gemini_response):

    print("\n--- AI RHYTHM RESPONSE ---")
    print(gemini_response)

    # Extract pattern
    pattern_match = re.search(
        r"PATTERN:\s*(.+)",
        gemini_response
    )

    # Extract tempo
    tempo_match = re.search(
        r"TEMPO:\s*(\d+)",
        gemini_response
    )

    if not pattern_match or not tempo_match:
        print("Invalid Gemini response format!")
        return

    pattern_text = pattern_match.group(1).strip()
    bpm = int(tempo_match.group(1))

    # Safety limits
    bpm = max(60, min(bpm, 220))

    pattern = pattern_text.split()

    print("\nPattern:", pattern)
    print("Tempo:", bpm, "BPM")

    beat_duration = 60 / bpm

    print("\nPlaying AI-generated Chenda response...\n")

    for i, sound_name in enumerate(pattern):

        sound_name = sound_name.upper()

        if sound_name == "DHUM":
            dhum.play()

        elif sound_name == "TA":
            ta.play()

        else:
            continue

        # Check whether the next beat is TA
        if (
            sound_name == "TA"
            and i + 1 < len(pattern)
            and pattern[i + 1].upper() == "TA"
        ):
            time.sleep(beat_duration * 0.5)

        else:
            time.sleep(beat_duration)

    time.sleep(0.5)

    print("AI rhythm finished!")