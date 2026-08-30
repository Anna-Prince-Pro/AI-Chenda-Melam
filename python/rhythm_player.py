import pygame
import time
import os
import re


# =========================================================
# PROJECT PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

dhum_path = os.path.join(BASE_DIR, "sounds", "dhum.wav")
ta_path = os.path.join(BASE_DIR, "sounds", "ta.wav")


# =========================================================
# INITIALIZE AUDIO
# =========================================================

pygame.mixer.init(
    frequency=44100,
    size=-16,
    channels=2,
    buffer=256
)

dhum = pygame.mixer.Sound(dhum_path)
ta = pygame.mixer.Sound(ta_path)


# =========================================================
# PLAY A SINGLE SOUND
# =========================================================

def play_sound(sound_name, volume=1.0):

    sound_name = sound_name.upper()

    if sound_name == "DHUM":
        dhum.set_volume(volume)
        dhum.play()

    elif sound_name == "TA":
        ta.set_volume(volume)
        ta.play()


# =========================================================
# PARSE AI RESPONSE
# =========================================================

def parse_response(ai_response):

    pattern_match = re.search(
        r"PATTERN:\s*(.+)",
        ai_response
    )

    tempo_match = re.search(
        r"TEMPO:\s*(\d+)",
        ai_response
    )

    intensity_match = re.search(
        r"INTENSITY:\s*(\w+)",
        ai_response
    )

    if not pattern_match or not tempo_match:

        print("Invalid AI response format!")
        return None, None, None

    pattern_text = pattern_match.group(1).strip()

    bpm = int(tempo_match.group(1))

    if intensity_match:
        intensity = intensity_match.group(1).upper()
    else:
        intensity = "MEDIUM"

    # Safety limits
    bpm = max(60, min(bpm, 220))

    return pattern_text, bpm, intensity


# =========================================================
# INTENSITY SETTINGS
# =========================================================

def get_volume(intensity):

    intensity = intensity.upper()

    if intensity == "LOW":
        return 0.55

    elif intensity == "MEDIUM":
        return 0.75

    elif intensity == "HIGH":
        return 1.0

    return 0.75


# =========================================================
# PLAY AI RHYTHM
# =========================================================

def play_rhythm(ai_response):

    print("\n=============================================")
    print("           AI CHENDA RESPONSE")
    print("=============================================")
    print(ai_response)
    print("=============================================")

    pattern_text, bpm, intensity = parse_response(
        ai_response
    )

    if pattern_text is None:
        return


    # -----------------------------------------------------
    # PATTERN FORMAT
    #
    # Example:
    #
    # DHUM TA TA | DHUM TA TA | DHUM DHUM TA TA | DHUM
    #
    # "|" separates musical phrases
    # -----------------------------------------------------

    phrases = [
        phrase.strip()
        for phrase in pattern_text.split("|")
        if phrase.strip()
    ]


    base_volume = get_volume(intensity)

    beat_duration = 60 / bpm


    print("\nTempo:", bpm, "BPM")
    print("Intensity:", intensity)
    print("Phrases:")

    for phrase in phrases:
        print("  ", phrase)


    print("\nPlaying AI-generated Chenda response...\n")


    total_phrases = len(phrases)


    # =====================================================
    # PLAY EACH PHRASE
    # =====================================================

    for phrase_index, phrase in enumerate(phrases):

        beats = phrase.split()

        if not beats:
            continue


        print(
            f"Phrase {phrase_index + 1}/{total_phrases}:",
            phrase
        )


        # -------------------------------------------------
        # PHRASE DYNAMICS
        #
        # Beginning  -> controlled
        # Middle     -> stronger
        # Ending     -> climax
        # -------------------------------------------------

        if phrase_index == 0:

            phrase_volume = base_volume * 0.85

        elif phrase_index == total_phrases - 1:

            phrase_volume = min(
                1.0,
                base_volume * 1.10
            )

        else:

            phrase_volume = base_volume


        # -------------------------------------------------
        # PLAY BEATS
        # -------------------------------------------------

        beat_count = len(beats)

        i = 0

        while i < beat_count:

            current = beats[i].upper()


            # ---------------------------------------------
            # ACCENT FIRST DHUM OF EACH PHRASE
            # ---------------------------------------------

            if i == 0 and current == "DHUM":

                volume = min(
                    1.0,
                    phrase_volume * 1.15
                )

            else:

                volume = phrase_volume


            # ---------------------------------------------
            # PLAY SOUND
            # ---------------------------------------------

            if current in ["DHUM", "TA"]:

                play_sound(
                    current,
                    volume
                )


            # ---------------------------------------------
            # RHYTHMIC SUBDIVISION
            #
            # TA TA gets played faster.
            #
            # Example:
            #
            # DHUM TA TA
            #
            # DHUM = one beat
            # TA TA = two quicker strokes
            # ---------------------------------------------

            if (
                current == "TA"
                and i + 1 < beat_count
                and beats[i + 1].upper() == "TA"
            ):

                time.sleep(
                    beat_duration * 0.50
                )

            else:

                time.sleep(
                    beat_duration
                )


            i += 1


        # -------------------------------------------------
        # SMALL PHRASE BREATH
        # -------------------------------------------------

        if phrase_index < total_phrases - 1:

            time.sleep(
                beat_duration * 0.25
            )


    # =====================================================
    # FINISH
    # =====================================================

    time.sleep(0.5)

    print("\nAI Chenda rhythm finished!")