import pygame
import time
import os
import re
import statistics


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DHUM_PATH = os.path.join(
    BASE_DIR,
    "sounds",
    "dhum.wav"
)

TA_PATH = os.path.join(
    BASE_DIR,
    "sounds",
    "ta.wav"
)


# =========================================================
# AUDIO INITIALIZATION
# =========================================================

# Small buffer keeps latency low while remaining stable.
pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=256
)

dhum = pygame.mixer.Sound(DHUM_PATH)
ta = pygame.mixer.Sound(TA_PATH)


# =========================================================
# LIMITS
# =========================================================

MIN_BPM = 50
MAX_BPM = 220

MIN_INTERVAL_MS = 80
MAX_INTERVAL_MS = 2000


# =========================================================
# PARSE GEMINI RESPONSE
# =========================================================

def parse_ai_response(ai_response):
    """
    Expected format:

    PATTERN: DHUM TA TA | DHUM TA DHUM
    TEMPO: 120
    INTENSITY: HIGH

    Returns:
        pattern, bpm, intensity
    """

    pattern_match = re.search(
        r"PATTERN\s*:\s*(.+)",
        ai_response,
        re.IGNORECASE
    )

    tempo_match = re.search(
        r"TEMPO\s*:\s*(\d+)",
        ai_response,
        re.IGNORECASE
    )

    intensity_match = re.search(
        r"INTENSITY\s*:\s*(LOW|MEDIUM|HIGH)",
        ai_response,
        re.IGNORECASE
    )

    if not pattern_match:
        print("ERROR: AI response has no PATTERN.")
        return None, None, None

    pattern_text = pattern_match.group(1).strip()

    # Preserve phrase separators for accent detection.
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
        return None, None, None

    if tempo_match:

        bpm = int(
            tempo_match.group(1)
        )

        bpm = max(
            MIN_BPM,
            min(bpm, MAX_BPM)
        )

    else:
        bpm = 120

    if intensity_match:
        intensity = (
            intensity_match
            .group(1)
            .upper()
        )
    else:
        intensity = "MEDIUM"

    return (
        pattern,
        bpm,
        intensity,
        phrase_starts
    )


# =========================================================
# CLEAN INPUT INTERVALS
# =========================================================

def clean_intervals(input_intervals):
    """
    Clamp impossible values while preserving the
    actual rhythmic structure.
    """

    if not input_intervals:
        return []

    cleaned = []

    for value in input_intervals:

        try:
            value = float(value)
        except (TypeError, ValueError):
            continue

        value = max(
            MIN_INTERVAL_MS,
            min(value, MAX_INTERVAL_MS)
        )

        cleaned.append(value)

    return cleaned


# =========================================================
# NATURALIZE TIMING
# =========================================================

def naturalize_intervals(input_intervals):
    """
    Balance between exact input timing and musical flow.

    Strategy:

    - Major pauses remain almost unchanged.
    - Very short subdivisions remain fast.
    - Small jitter between neighboring beats is smoothed.
    - Timing is never converted into a rigid BPM grid.

    This preserves the rhythmic fingerprint while
    avoiding the "mechanically triggered sample" effect.
    """

    intervals = clean_intervals(
        input_intervals
    )

    if len(intervals) <= 2:
        return intervals

    median_interval = statistics.median(
        intervals
    )

    result = []

    for i, interval in enumerate(intervals):

        # ---------------------------------------------
        # Detect important pauses / structural gaps
        # ---------------------------------------------

        is_long = (
            interval > median_interval * 1.45
        )

        is_short = (
            interval < median_interval * 0.70
        )

        if is_long:

            # Preserve major pauses.
            smoothed = (
                interval * 0.95
                + median_interval * 0.05
            )

        elif is_short:

            # Preserve quick subdivisions.
            smoothed = (
                interval * 0.92
                + median_interval * 0.08
            )

        else:

            # Smooth only a little.
            # This removes sensor-level jitter without
            # flattening the rhythm.
            smoothed = (
                interval * 0.82
                + median_interval * 0.18
            )

        result.append(
            max(
                MIN_INTERVAL_MS,
                smoothed
            )
        )

    return result


# =========================================================
# GET VOLUME SETTINGS
# =========================================================

def get_volume_levels(intensity):

    if intensity == "LOW":

        return 0.52, 0.38

    if intensity == "HIGH":

        return 0.92, 0.72

    return 0.74, 0.56


# =========================================================
# PLAY A SINGLE HIT
# =========================================================

def play_hit(
    beat,
    volume
):

    if beat == "DHUM":

        dhum.set_volume(volume)
        dhum.play()

    elif beat == "TA":

        ta.set_volume(volume)
        ta.play()


# =========================================================
# PLAY RHYTHM
# =========================================================

def play_rhythm(
    ai_response,
    input_intervals=None
):
    """
    Play the AI-generated Chenda response while preserving
    the timing fingerprint of the user's original rhythm.

    input_intervals:
        Time between the user's detected taps in milliseconds.
    """

    print("\n==============================================")
    print("          AI CHENDA AUDIO ENGINE")
    print("==============================================")

    print("\nAI response:")
    print(ai_response)

    parsed = parse_ai_response(
        ai_response
    )

    if not parsed:
        return

    (
        pattern,
        bpm,
        intensity,
        phrase_starts
    ) = parsed

    print("\nGenerated pattern:")
    print(
        " ".join(pattern)
    )

    print(
        f"AI tempo: {bpm} BPM"
    )

    print(
        f"Intensity: {intensity}"
    )

    # =====================================================
    # DETERMINE TIMING
    # =====================================================

    input_intervals = clean_intervals(
        input_intervals
    )

    if input_intervals:

        # Ideally:
        # number of output beats = input taps
        if len(pattern) == len(input_intervals) + 1:

            playback_intervals = naturalize_intervals(
                input_intervals
            )

            timing_mode = (
                "INPUT RHYTHM + MUSICAL SMOOTHING"
            )

        else:

            print(
                "\nWarning: AI pattern length does not "
                "match input rhythm length."
            )

            # Fallback to tempo timing.
            beat_duration = (
                60.0 / bpm
            )

            playback_intervals = [
                beat_duration * 1000
                for _ in range(
                    max(0, len(pattern) - 1)
                )
            ]

            timing_mode = (
                "AI TEMPO FALLBACK"
            )

    else:

        beat_duration = (
            60.0 / bpm
        )

        playback_intervals = [
            beat_duration * 1000
            for _ in range(
                max(0, len(pattern) - 1)
            )
        ]

        timing_mode = (
            "AI TEMPO"
        )


    print(
        "Timing mode:",
        timing_mode
    )


    if input_intervals:

        print(
            "Original intervals:"
        )

        print(
            [
                round(x, 1)
                for x in input_intervals
            ]
        )

        print(
            "Smoothed playback intervals:"
        )

        print(
            [
                round(x, 1)
                for x in playback_intervals
            ]
        )


    # =====================================================
    # VOLUME
    # =====================================================

    dhum_base, ta_base = (
        get_volume_levels(
            intensity
        )
    )


    # =====================================================
    # PLAYBACK CLOCK
    # =====================================================

    next_event = (
        time.perf_counter()
    )


    print(
        "\nPlaying Chenda response..."
    )


    # =====================================================
    # PLAY BEATS
    # =====================================================

    for index, beat in enumerate(pattern):


        # -------------------------------------------------
        # Wait until exact scheduled time
        # -------------------------------------------------

        now = time.perf_counter()

        wait_time = (
            next_event - now
        )

        if wait_time > 0:

            time.sleep(
                wait_time
            )


        # -------------------------------------------------
        # DETERMINE DYNAMIC LEVEL
        # -------------------------------------------------

        if beat == "DHUM":

            volume = dhum_base

        else:

            volume = ta_base


        # -------------------------------------------------
        # PHRASE ACCENTS
        # -------------------------------------------------

        if index in phrase_starts:

            volume *= 1.12


        # First beat of entire response
        # gets a stronger attack.

        if index == 0:

            volume *= 1.10


        # Final beat gets a controlled resolution.

        if index == len(pattern) - 1:

            volume *= 1.08


        # Keep volume in safe range.

        volume = max(
            0.05,
            min(volume, 1.0)
        )


        # -------------------------------------------------
        # PLAY HIT
        # -------------------------------------------------

        play_hit(
            beat,
            volume
        )


        print(
            f"{index + 1:02d}. {beat}"
        )


        # -------------------------------------------------
        # SCHEDULE NEXT HIT
        # -------------------------------------------------

        if index < len(pattern) - 1:

            interval = (
                playback_intervals[index]
            )

            next_event += (
                interval / 1000.0
            )


    # =====================================================
    # FINAL AUDIO TAIL
    # =====================================================

    time.sleep(0.35)

    print(
        "\nAI Chenda response finished!"
    )