import serial
import time
import os

from dotenv import load_dotenv
from google import genai

from rhythm_player import play_rhythm


# =========================================================
# CONFIGURATION
# =========================================================

PORT = "COM3"
BAUD_RATE = 115200

# Time to wait after the last tap before considering
# the user's rhythm phrase complete
PHRASE_TIMEOUT = 1.5

# Minimum taps required to analyze a rhythm
MIN_TAPS = 4


# =========================================================
# LOAD GEMINI API KEY
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

env_path = os.path.join(
    BASE_DIR,
    ".env"
)

load_dotenv(env_path)

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env")
    raise SystemExit


# =========================================================
# INITIALIZE GEMINI
# =========================================================

client = genai.Client(
    api_key=API_KEY
)


# =========================================================
# RHYTHM ANALYSIS
# =========================================================

def analyze_rhythm(taps):

    if len(taps) < MIN_TAPS:
        return None

    # -----------------------------------------------------
    # CALCULATE INTERVALS
    # -----------------------------------------------------

    intervals = []

    for i in range(1, len(taps)):

        interval = taps[i] - taps[i - 1]

        intervals.append(interval)


    # Remove extremely long gaps
    active_intervals = [
        value
        for value in intervals
        if value < 1500
    ]

    if len(active_intervals) == 0:
        return None


    # -----------------------------------------------------
    # AVERAGE INTERVAL
    # -----------------------------------------------------

    average_interval = (
        sum(active_intervals)
        / len(active_intervals)
    )


    # -----------------------------------------------------
    # TEMPO
    # -----------------------------------------------------

    tempo = (
        60000
        / average_interval
    )

    tempo = max(
        60,
        min(
            round(tempo),
            220
        )
    )


    # -----------------------------------------------------
    # SPEED
    # -----------------------------------------------------

    if tempo < 90:
        speed = "SLOW"

    elif tempo < 135:
        speed = "MEDIUM"

    else:
        speed = "FAST"


    # -----------------------------------------------------
    # RHYTHM TREND
    # -----------------------------------------------------

    if len(active_intervals) >= 4:

        middle = len(active_intervals) // 2

        first_half = active_intervals[:middle]
        second_half = active_intervals[middle:]

        first_average = (
            sum(first_half)
            / len(first_half)
        )

        second_average = (
            sum(second_half)
            / len(second_half)
        )

        difference = (
            second_average
            - first_average
        )

        if difference < -60:
            trend = "ACCELERATING"

        elif difference > 60:
            trend = "SLOWING_DOWN"

        else:
            trend = "STABLE"

    else:
        trend = "STABLE"


    # -----------------------------------------------------
    # CONSISTENCY
    # -----------------------------------------------------

    deviations = []

    for interval in active_intervals:

        deviation = abs(
            interval
            - average_interval
        )

        deviations.append(deviation)

    average_deviation = (
        sum(deviations)
        / len(deviations)
    )

    consistency_variation = (
        average_deviation
        / average_interval
    )


    # -----------------------------------------------------
    # INTENSITY
    # -----------------------------------------------------

    if tempo >= 150:
        intensity = "HIGH"

    elif tempo >= 100:
        intensity = "MEDIUM"

    else:
        intensity = "LOW"


    # -----------------------------------------------------
    # RHYTHM STRUCTURE
    # -----------------------------------------------------

    structure = []

    for interval in active_intervals:

        ratio = (
            interval
            / average_interval
        )

        if ratio < 0.75:

            structure.append(
                "SHORT"
            )

        elif ratio > 1.30:

            structure.append(
                "LONG"
            )

        else:

            structure.append(
                "NORMAL"
            )


    # -----------------------------------------------------
    # CREATE RESULT
    # -----------------------------------------------------

    result = {

        "tap_count": len(taps),

        "intervals": active_intervals,

        "average_interval": round(
            average_interval,
            2
        ),

        "tempo": tempo,

        "speed": speed,

        "trend": trend,

        "intensity": intensity,

        "consistency": round(
            consistency_variation,
            2
        ),

        "structure": structure
    }

    return result


# =========================================================
# PRINT RHYTHM ANALYSIS
# =========================================================

def print_analysis(analysis):

    print("\n=============================================")
    print("         RHYTHM ANALYSIS")
    print("=============================================")

    print(
        "Tap count:",
        analysis["tap_count"]
    )

    print(
        "Average interval:",
        analysis["average_interval"],
        "ms"
    )

    print(
        "Tempo:",
        analysis["tempo"],
        "BPM"
    )

    print(
        "Speed:",
        analysis["speed"]
    )

    print(
        "Trend:",
        analysis["trend"]
    )

    print(
        "Intensity:",
        analysis["intensity"]
    )

    print(
        "Consistency variation:",
        analysis["consistency"]
    )

    print("\nIntervals:")

    print(
        analysis["intervals"]
    )

    print("\nRhythm structure:")

    print(
        " ".join(
            analysis["structure"]
        )
    )

    print("=============================================\n")


# =========================================================
# GENERATE AI RHYTHM
# =========================================================

def generate_ai_rhythm(analysis):

    structure_text = " ".join(
        analysis["structure"]
    )

    prompt = f"""
You are the musical intelligence of an interactive AI Chenda Melam system.

A human has performed a rhythm on a drum sensor.

Your task is to analyze the rhythm characteristics and compose a SHORT,
energetic, Chenda-inspired rhythmic RESPONSE.

INPUT RHYTHM ANALYSIS:

Tempo: {analysis["tempo"]} BPM
Speed: {analysis["speed"]}
Trend: {analysis["trend"]}
Intensity: {analysis["intensity"]}
Tap count: {analysis["tap_count"]}
Consistency variation: {analysis["consistency"]}

Rhythm structure:
{structure_text}

COMPOSITION RULES:

1. Respond to the CHARACTER of the human rhythm.

2. If the rhythm is FAST or ACCELERATING:
   gradually build energy and use denser TA patterns.

3. If the rhythm is SLOW:
   use stronger DHUM strokes and more space.

4. If the rhythm is SLOWING_DOWN:
   create a controlled response and finish strongly.

5. Use BOTH DHUM and TA.

6. Divide the composition into 3 to 5 MUSICAL PHRASES using |.

7. Create musical development:
   - Phrase 1 responds to the input
   - Middle phrases develop or intensify
   - Final phrase creates a climax or resolution

8. Avoid repeating exactly the same phrase.

9. Keep the response between 12 and 24 total strokes.

10. Use only these rhythm tokens:
    DHUM
    TA
    |

11. Do not write explanations.

Return EXACTLY in this format:

PATTERN: DHUM TA TA | DHUM TA DHUM TA | DHUM DHUM TA TA | DHUM TA DHUM
TEMPO: number
INTENSITY: LOW or MEDIUM or HIGH

The output tempo should remain close to the human tempo,
within approximately plus or minus 15 BPM.
"""

    print(
        "Sending musical analysis to Gemini..."
    )

    try:

        response = client.models.generate_content(

            model="gemini-3.6-flash",

            contents=prompt
        )

        ai_response = (
            response.text.strip()
        )

        print("\n--- AI COMPOSITION ---")
        print(ai_response)

        return ai_response


    except Exception as error:

        print("\nGemini Error:")
        print(error)

        return None


# =========================================================
# MAIN PROGRAM
# =========================================================

def main():

    print("Connecting to Arduino...")

    try:

        ser = serial.Serial(
            PORT,
            BAUD_RATE,
            timeout=0.1
        )

        # Arduino may reset when serial connection opens
        time.sleep(2)

        # Remove old startup data from the serial buffer
        ser.reset_input_buffer()

        print("Connected!")

    except Exception as error:

        print("\nCould not connect to Arduino.")
        print(error)

        return


    print("\nTap a rhythm on the drum.")
    print(
        "Stop tapping for 1.5 seconds and "
        "the AI will respond automatically."
    )
    print("Press Ctrl + C to stop.\n")


    taps = []
    last_tap_time = None


    try:

        while True:

            # =================================================
            # READ ALL AVAILABLE ARDUINO DATA
            # =================================================

            while ser.in_waiting:

                raw_line = ser.readline()

                if not raw_line:
                    break

                line = raw_line.decode(
                    "utf-8",
                    errors="ignore"
                ).strip()

                # DEBUG:
                # Shows exactly what Python receives
                if line:
                    print(
                        f"SERIAL RECEIVED: [{line}]"
                    )


                # =============================================
                # DETECT TAP
                # =============================================

                if "TAP" in line.upper():

                    current_time = int(
                        time.time() * 1000
                    )


                    # Prevent duplicate sensor triggers
                    # occurring extremely close together
                    if (

                        last_tap_time is None

                        or current_time
                        - last_tap_time > 80

                    ):

                        taps.append(
                            current_time
                        )

                        last_tap_time = (
                            current_time
                        )

                        print(
                            f"✓ TAP DETECTED: "
                            f"{current_time} ms"
                        )


            # =================================================
            # CHECK WHETHER RHYTHM PHRASE HAS ENDED
            # =================================================

            if (

                last_tap_time is not None

                and len(taps) >= MIN_TAPS

            ):

                current_time = int(
                    time.time() * 1000
                )

                silence = (

                    current_time
                    - last_tap_time

                ) / 1000


                if silence >= PHRASE_TIMEOUT:

                    print(
                        "\nRhythm phrase detected!"
                    )


                    analysis = analyze_rhythm(
                        taps
                    )


                    if analysis:

                        print_analysis(
                            analysis
                        )


                        ai_response = (
                            generate_ai_rhythm(
                                analysis
                            )
                        )


                        if ai_response:

                            print(
                                "\nStarting AI "
                                "Chenda response..."
                            )

                            play_rhythm(
    ai_response,
    analysis["intervals"]
)


                    # =========================================
                    # RESET FOR NEXT RHYTHM
                    # =========================================

                    taps = []

                    last_tap_time = None


                    print(
                        "\nReady for next rhythm...\n"
                    )


            # Very short delay to avoid unnecessary CPU usage
            time.sleep(0.005)


    except KeyboardInterrupt:

        print(
            "\n\nStopping AI Chenda Melam..."
        )


    finally:

        if ser.is_open:
            ser.close()

        print(
            "Serial connection closed."
        )


# =========================================================
# START PROGRAM
# =========================================================

if __name__ == "__main__":
    main()