import os
import re
import statistics
import time

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DHUM_PATH = os.path.join(BASE_DIR, "sounds", "dhum.wav")
TA_PATH = os.path.join(BASE_DIR, "sounds", "ta.wav")


# =========================================================
# AUDIO INITIALIZATION
# =========================================================

pygame.mixer.pre_init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=128,
)

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=128,
)

dhum = pygame.mixer.Sound(DHUM_PATH)
ta = pygame.mixer.Sound(TA_PATH)

dhum_channel = pygame.mixer.Channel(0)
ta_channel = pygame.mixer.Channel(1)


# =========================================================
# LIMITS
# =========================================================

MIN_BPM = 50
MAX_BPM = 220
MIN_INTERVAL_MS = 80
MAX_INTERVAL_MS = 2000


# =========================================================
# SERIAL LED SYNC
# =========================================================

def send_led_beat(serial_connection, sound_name):
    if serial_connection is None:
        return

    try:
        serial_connection.write(
            f"LED,{sound_name}\n".encode("utf-8")
        )
    except Exception as error:
        print("LED sync error:", error)


# =========================================================
# PARSE GEMINI RESPONSE
# =========================================================

def parse_ai_response(ai_response):
    pattern_match = re.search(
        r"PATTERN\s*:\s*(.+)",
        ai_response,
        re.IGNORECASE,
    )

    tempo_match = re.search(
        r"TEMPO\s*:\s*(\d+)",
        ai_response,
        re.IGNORECASE,
    )

    intensity_match = re.search(
        r"INTENSITY\s*:\s*(LOW|MEDIUM|HIGH)",
        ai_response,
        re.IGNORECASE,
    )

    if not pattern_match:
        print("ERROR: AI response has no PATTERN.")
        return None

    pattern_text = pattern_match.group(1).strip()
    tokens = pattern_text.split()

    pattern = []
    phrase_starts = set()
    next_phrase = True

    for token in tokens:
        token = token.strip().upper()

        if token == "|":
            next_phrase = True
            continue

        if token not in ("DHUM", "TA"):
            continue

        if next_phrase:
            phrase_starts.add(len(pattern))
            next_phrase = False

        pattern.append(token)

    if not pattern:
        print("ERROR: AI returned an empty pattern.")
        return None

    if tempo_match:
        bpm = int(tempo_match.group(1))
        bpm = max(MIN_BPM, min(bpm, MAX_BPM))
    else:
        bpm = 120

    if intensity_match:
        intensity = intensity_match.group(1).upper()
    else:
        intensity = "MEDIUM"

    return pattern, bpm, intensity, phrase_starts


# =========================================================
# TIMING HELPERS
# =========================================================

def clean_intervals(input_intervals):
    if not input_intervals:
        return []

    cleaned = []

    for value in input_intervals:
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        value = max(MIN_INTERVAL_MS, min(value, MAX_INTERVAL_MS))
        cleaned.append(value)

    return cleaned


def naturalize_intervals(input_intervals):
    intervals = clean_intervals(input_intervals)

    if len(intervals) <= 2:
        return intervals

    median_interval = statistics.median(intervals)
    result = []

    for interval in intervals:
        is_long = interval > median_interval * 1.45
        is_short = interval < median_interval * 0.70

        if is_long:
            smoothed = interval * 0.95 + median_interval * 0.05
        elif is_short:
            smoothed = interval * 0.92 + median_interval * 0.08
        else:
            smoothed = interval * 0.82 + median_interval * 0.18

        result.append(max(MIN_INTERVAL_MS, smoothed))

    return result


def wait_until(target_time):
    while True:
        remaining = target_time - time.perf_counter()

        if remaining <= 0:
            return

        if remaining > 0.004:
            time.sleep(remaining - 0.002)


# =========================================================
# AUDIO HELPERS
# =========================================================

def get_volume_levels(intensity):
    if intensity == "LOW":
        return 0.52, 0.38

    if intensity == "HIGH":
        return 0.92, 0.72

    return 0.74, 0.56


def play_hit(beat, volume):
    if beat == "DHUM":
        dhum.set_volume(volume)
        dhum_channel.fadeout(12)
        dhum_channel.play(dhum, fade_ms=4)

    elif beat == "TA":
        ta.set_volume(volume)
        ta_channel.fadeout(8)
        ta_channel.play(ta, fade_ms=2)


# =========================================================
# PLAY RHYTHM
# =========================================================

def play_rhythm(
    ai_response,
    input_intervals=None,
    serial_connection=None,
):
    print("\n==============================================")
    print("          AI CHENDA AUDIO ENGINE")
    print("==============================================")

    print("\nAI response:")
    print(ai_response)

    parsed = parse_ai_response(ai_response)

    if not parsed:
        return

    pattern, bpm, intensity, phrase_starts = parsed

    print("\nGenerated pattern:")
    print(" ".join(pattern))
    print(f"AI tempo: {bpm} BPM")
    print(f"Intensity: {intensity}")

    input_intervals = clean_intervals(input_intervals)

    if input_intervals and len(pattern) == len(input_intervals) + 1:
        playback_intervals = naturalize_intervals(input_intervals)
        timing_mode = "INPUT RHYTHM + MUSICAL SMOOTHING"
    else:
        beat_duration = 60.0 / bpm
        playback_intervals = [
            beat_duration * 1000
            for _ in range(max(0, len(pattern) - 1))
        ]
        timing_mode = "AI TEMPO"

    print("Timing mode:", timing_mode)

    dhum_base, ta_base = get_volume_levels(intensity)
    next_event = time.perf_counter()

    print("\nPlaying Chenda response...")

    for index, beat in enumerate(pattern):
        wait_until(next_event)

        if beat == "DHUM":
            volume = dhum_base
        else:
            volume = ta_base

        if index in phrase_starts:
            volume *= 1.12

        if index == 0:
            volume *= 1.10

        if index == len(pattern) - 1:
            volume *= 1.08

        volume = max(0.05, min(volume, 1.0))

        send_led_beat(serial_connection, beat)
        play_hit(beat, volume)

        print(f"{index + 1:02d}. {beat}")

        if index < len(pattern) - 1:
            next_event += playback_intervals[index] / 1000.0

    time.sleep(0.35)
    print("\nAI Chenda response finished!")
