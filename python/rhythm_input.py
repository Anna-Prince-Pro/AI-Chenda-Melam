import serial
import time
import statistics
import os

from dotenv import load_dotenv
from google import genai

from rhythm_player import play_rhythm


# =================================
# LOAD ENVIRONMENT VARIABLES
# =================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

load_dotenv(os.path.join(BASE_DIR, ".env"))

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY not found in .env file!"
    )


# =================================
# GEMINI CLIENT
# =================================

client = genai.Client(api_key=API_KEY)


# =================================
# ARDUINO SETTINGS
# =================================

PORT = "COM3"
BAUD_RATE = 9600


# =================================
# RHYTHM SETTINGS
# =================================

MIN_TAPS = 6

# Time without a tap before the
# rhythm phrase is considered finished
PAUSE_THRESHOLD = 1.5

# Ignore duplicate/accidental sensor hits
DEBOUNCE_TIME = 250


# =================================
# ANALYZE RHYTHM
# =================================

def analyze_rhythm(tap_times):

    if len(tap_times) < MIN_TAPS:
        print("\nNot enough taps for analysis.")
        return None

    intervals = []

    for i in range(1, len(tap_times)):

        interval = tap_times[i] - tap_times[i - 1]

        # Ignore abnormal pauses
        if interval < 2000:
            intervals.append(interval)

    if len(intervals) < 3:
        print("Not enough valid intervals.")
        return None


    # -----------------------------
    # TEMPO
    # -----------------------------

    average_interval = statistics.mean(intervals)

    bpm = 60000 / average_interval


    # -----------------------------
    # SPEED
    # -----------------------------

    if bpm < 80:
        speed = "SLOW"

    elif bpm < 120:
        speed = "MEDIUM"

    else:
        speed = "FAST"


    # -----------------------------
    # RHYTHM TREND
    # -----------------------------

    midpoint = len(intervals) // 2

    first_half = intervals[:midpoint]
    second_half = intervals[midpoint:]

    trend = "STABLE"

    if first_half and second_half:

        first_avg = statistics.mean(first_half)
        second_avg = statistics.mean(second_half)

        if second_avg < first_avg * 0.85:
            trend = "ACCELERATING"

        elif second_avg > first_avg * 1.15:
            trend = "SLOWING_DOWN"


    # -----------------------------
    # RHYTHM STRUCTURE
    # -----------------------------

    structure = []

    for interval in intervals:

        ratio = interval / average_interval

        if ratio < 0.75:
            structure.append("SHORT")

        elif ratio > 1.35:
            structure.append("LONG")

        else:
            structure.append("NORMAL")


    # -----------------------------
    # RHYTHM CONSISTENCY
    # -----------------------------

    if len(intervals) > 1:

        variation = statistics.stdev(intervals)
        variation_ratio = variation / average_interval

    else:
        variation_ratio = 0


    # -----------------------------
    # INTENSITY
    # -----------------------------

    if bpm >= 150:
        intensity = "HIGH"

    elif bpm >= 100:
        intensity = "MEDIUM"

    else:
        intensity = "LOW"


    # -----------------------------
    # DISPLAY RESULTS
    # -----------------------------

    print("\n" + "=" * 45)
    print("         RHYTHM ANALYSIS")
    print("=" * 45)

    print(f"Tap count: {len(tap_times)}")
    print(f"Average interval: {average_interval:.2f} ms")
    print(f"Tempo: {bpm:.2f} BPM")
    print(f"Speed: {speed}")
    print(f"Trend: {trend}")
    print(f"Intensity: {intensity}")
    print(f"Consistency variation: {variation_ratio:.2f}")

    print("\nIntervals:")
    print(intervals)

    print("\nRhythm structure:")
    print(" ".join(structure))

    print("=" * 45)


    return {
        "tap_count": len(tap_times),
        "intervals": intervals,
        "average_interval": average_interval,
        "bpm": bpm,
        "speed": speed,
        "trend": trend,
        "intensity": intensity,
        "structure": structure,
        "variation_ratio": variation_ratio
    }


# =================================
# GENERATE AI RHYTHM
# =================================

def generate_ai_rhythm(analysis):

    print("\nSending rhythm to Gemini...")

    intervals_text = ", ".join(
        str(interval)
        for interval in analysis["intervals"]
    )

    structure_text = " ".join(
        analysis["structure"]
    )


    prompt = f"""
You are the rhythm intelligence module of an interactive
AI Chenda Melam system.

A human performer has tapped a physical rhythm.

Generate a creative CALL-AND-RESPONSE Chenda-style rhythm
based specifically on the input characteristics.

INPUT:

Tempo: {analysis["bpm"]:.0f} BPM
Speed: {analysis["speed"]}
Trend: {analysis["trend"]}
Intensity: {analysis["intensity"]}

Tap intervals in milliseconds:
{intervals_text}

Rhythm structure:
{structure_text}

INSTRUCTIONS:

- Do NOT return a generic repeating pattern.
- Create a variation inspired by the input rhythm.
- Preserve approximately the same tempo.
- Keep the response energetic if the input is FAST.
- Use DHUM for strong accents and longer beats.
- Use TA for faster subdivisions.
- Make the rhythm sound like a response to the performer.
- Use between 8 and 20 beats.
- Use ONLY the tokens DHUM and TA.

Return ONLY this exact format:

PATTERN: DHUM TA TA DHUM TA DHUM TA TA
TEMPO: 169
INTENSITY: HIGH
"""

    try:

        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:

        print("\nGemini Error:")
        print(e)

        return None


# =================================
# MAIN PROGRAM
# =================================

def main():

    print("Connecting to Arduino...")

    try:

        ser = serial.Serial(
            PORT,
            BAUD_RATE,
            timeout=0.1
        )

    except serial.SerialException as e:

        print("\nCould not connect to Arduino!")
        print(e)

        return


    time.sleep(2)

    # Clear old data from Arduino
    ser.reset_input_buffer()


    print("Connected!")

    print("\nTap a rhythm on the drum.")
    print(
        f"Stop tapping for {PAUSE_THRESHOLD} seconds "
        "and the AI will respond automatically."
    )
    print("Press Ctrl + C to stop.\n")


    tap_times = []
    last_tap_time = None


    try:

        while True:

            # =========================
            # CHECK FOR SERIAL DATA
            # =========================

            if ser.in_waiting > 0:

                line = (
                    ser.readline()
                    .decode(
                        "utf-8",
                        errors="ignore"
                    )
                    .strip()
                )


                # =====================
                # RECEIVE TAP
                # =====================

                if line.startswith("TAP,"):

                    try:

                        timestamp = int(
                            line.split(",")[1]
                        )

                    except ValueError:

                        continue


                    # =================
                    # DEBOUNCE FILTER
                    # =================

                    if (
                        not tap_times
                        or timestamp
                        - tap_times[-1]
                        >= DEBOUNCE_TIME
                    ):

                        tap_times.append(timestamp)

                        last_tap_time = time.time()

                        print(
                            f"TAP: {timestamp} ms"
                        )


            # =========================
            # DETECT END OF PHRASE
            # =========================

            if (
                tap_times
                and last_tap_time is not None
                and len(tap_times) >= MIN_TAPS
            ):

                pause_duration = (
                    time.time()
                    - last_tap_time
                )


                if pause_duration >= PAUSE_THRESHOLD:

                    print("\nRhythm phrase detected!")

                    # Analyze physical rhythm
                    analysis = analyze_rhythm(
                        tap_times
                    )


                    # Generate AI response
                    if analysis:

                        ai_response = (
                            generate_ai_rhythm(
                                analysis
                            )
                        )


                        # Play AI response
                        if ai_response:

                            print(
                                "\n--- GEMINI RESPONSE ---"
                            )

                            print(ai_response)

                            play_rhythm(
                                ai_response
                            )


                    # =================
                    # RESET FOR NEXT
                    # =================

                    print(
                        "\nReady for next rhythm...\n"
                    )

                    tap_times = []
                    last_tap_time = None


            # Prevent unnecessary CPU usage
            time.sleep(0.01)


    except KeyboardInterrupt:

        print(
            "\nStopping AI Chenda Melam..."
        )


    finally:

        ser.close()

        print(
            "Serial connection closed."
        )


# =================================
# START PROGRAM
# =================================

if __name__ == "__main__":
    main()