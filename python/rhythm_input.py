import os
import time

import serial
from dotenv import load_dotenv
from google import genai

from rhythm_player import play_rhythm


# =========================================================
# CONFIGURATION
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, ".env"))
load_dotenv(os.path.join(SCRIPT_DIR, ".env"))

PORT = os.getenv("ARDUINO_PORT", "COM3")
BAUD_RATE = int(os.getenv("ARDUINO_BAUD_RATE", "115200"))

PHRASE_TIMEOUT = float(os.getenv("PHRASE_TIMEOUT", "0.9"))
PAUSE_THRESHOLD = PHRASE_TIMEOUT
MIN_TAPS = int(os.getenv("MIN_TAPS", "4"))
DEBOUNCE_TIME = int(os.getenv("DEBOUNCE_TIME", "80"))

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("ERROR: GEMINI_API_KEY not found in .env")
    raise SystemExit

client = genai.Client(api_key=API_KEY)


# =========================================================
# RHYTHM ANALYSIS
# =========================================================

def analyze_rhythm(taps):
    if len(taps) < MIN_TAPS:
        print("\nNot enough taps for analysis.")
        return None

    intervals = []

    for i in range(1, len(taps)):
        intervals.append(taps[i] - taps[i - 1])

    active_intervals = [
        value
        for value in intervals
        if value < 1500
    ]

    if len(active_intervals) == 0:
        return None

    average_interval = sum(active_intervals) / len(active_intervals)
    tempo = round(60000 / average_interval)
    tempo = max(60, min(tempo, 220))

    if tempo < 90:
        speed = "SLOW"
    elif tempo < 135:
        speed = "MEDIUM"
    else:
        speed = "FAST"

    if len(active_intervals) >= 4:
        middle = len(active_intervals) // 2
        first_half = active_intervals[:middle]
        second_half = active_intervals[middle:]
        first_average = sum(first_half) / len(first_half)
        second_average = sum(second_half) / len(second_half)
        difference = second_average - first_average

        if difference < -60:
            trend = "ACCELERATING"
        elif difference > 60:
            trend = "SLOWING_DOWN"
        else:
            trend = "STABLE"
    else:
        trend = "STABLE"

    deviations = [
        abs(interval - average_interval)
        for interval in active_intervals
    ]
    average_deviation = sum(deviations) / len(deviations)
    consistency = average_deviation / average_interval

    if tempo >= 150:
        intensity = "HIGH"
    elif tempo >= 100:
        intensity = "MEDIUM"
    else:
        intensity = "LOW"

    structure = []

    for interval in active_intervals:
        ratio = interval / average_interval

        if ratio < 0.75:
            structure.append("SHORT")
        elif ratio > 1.30:
            structure.append("LONG")
        else:
            structure.append("NORMAL")

    return {
        "tap_count": len(taps),
        "intervals": active_intervals,
        "average_interval": round(average_interval, 2),
        "tempo": tempo,
        "bpm": tempo,
        "speed": speed,
        "trend": trend,
        "intensity": intensity,
        "consistency": round(consistency, 2),
        "variation_ratio": round(consistency, 2),
        "structure": structure,
    }


def print_analysis(analysis):
    print("\n=============================================")
    print("         RHYTHM ANALYSIS")
    print("=============================================")
    print("Tap count:", analysis["tap_count"])
    print("Average interval:", analysis["average_interval"], "ms")
    print("Tempo:", analysis["tempo"], "BPM")
    print("Speed:", analysis["speed"])
    print("Trend:", analysis["trend"])
    print("Intensity:", analysis["intensity"])
    print("Consistency variation:", analysis["consistency"])
    print("\nIntervals:")
    print(analysis["intervals"])
    print("\nRhythm structure:")
    print(" ".join(analysis["structure"]))
    print("=============================================\n")


# =========================================================
# GENERATE AI RHYTHM
# =========================================================

def generate_ai_rhythm(analysis):
    structure_text = " ".join(analysis["structure"])

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
2. If the rhythm is FAST or ACCELERATING, gradually build energy and use denser TA patterns.
3. If the rhythm is SLOW, use stronger DHUM strokes and more space.
4. If the rhythm is SLOWING_DOWN, create a controlled response and finish strongly.
5. Use BOTH DHUM and TA.
6. Divide the composition into 3 to 5 MUSICAL PHRASES using |.
7. Create musical development across the phrases.
8. Avoid repeating exactly the same phrase.
9. Keep the response between 12 and 24 total strokes.
10. Use only these rhythm tokens: DHUM, TA, |
11. Do not write explanations.

Return EXACTLY in this format:

PATTERN: DHUM TA TA | DHUM TA DHUM TA | DHUM DHUM TA TA | DHUM TA DHUM
TEMPO: number
INTENSITY: LOW or MEDIUM or HIGH

The output tempo should remain close to the human tempo,
within approximately plus or minus 15 BPM.
"""

    print("Sending musical analysis to Gemini...")

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt,
        )
        ai_response = response.text.strip()

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
            timeout=0.1,
        )
        time.sleep(2)
        ser.reset_input_buffer()
        print("Connected!")

    except Exception as error:
        print("\nCould not connect to Arduino.")
        print(error)
        return

    print("\nTap a rhythm on the drum.")
    print(
        f"Stop tapping for {PHRASE_TIMEOUT} seconds and "
        "the AI will respond automatically."
    )
    print("Press Ctrl + C to stop.\n")

    taps = []
    last_tap_time = None

    try:
        while True:
            while ser.in_waiting:
                raw_line = ser.readline()

                if not raw_line:
                    break

                line = raw_line.decode(
                    "utf-8",
                    errors="ignore",
                ).strip()

                if line:
                    print(f"SERIAL RECEIVED: [{line}]")

                if "TAP" in line.upper():
                    current_time = int(time.time() * 1000)

                    if (
                        last_tap_time is None
                        or current_time - last_tap_time > DEBOUNCE_TIME
                    ):
                        taps.append(current_time)
                        last_tap_time = current_time
                        print(f"TAP DETECTED: {current_time} ms")

            if last_tap_time is not None and len(taps) >= MIN_TAPS:
                current_time = int(time.time() * 1000)
                silence = (current_time - last_tap_time) / 1000

                if silence >= PHRASE_TIMEOUT:
                    print("\nRhythm phrase detected!")

                    analysis = analyze_rhythm(taps)

                    if analysis:
                        print_analysis(analysis)
                        ai_response = generate_ai_rhythm(analysis)

                        if ai_response:
                            print("\nStarting AI Chenda response...")
                            play_rhythm(
                                ai_response,
                                analysis["intervals"],
                                ser,
                            )

                    taps = []
                    last_tap_time = None
                    print("\nReady for next rhythm...\n")

            time.sleep(0.005)

    except KeyboardInterrupt:
        print("\n\nStopping AI Chenda Melam...")

    finally:
        if ser.is_open:
            ser.close()

        print("Serial connection closed.")


if __name__ == "__main__":
    main()
