import serial
import time
import statistics
import os

from dotenv import load_dotenv
from google import genai


# ==========================================
# GEMINI SETUP
# ==========================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found!")
    exit()

client = genai.Client(api_key=api_key)


# ==========================================
# ARDUINO SETUP
# ==========================================

PORT = "COM3"
BAUD_RATE = 9600

print("Connecting to Arduino...")

ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

time.sleep(2)

print("Connected!")
print("Start tapping...")
print("Press Ctrl + C to analyze the rhythm.\n")


# ==========================================
# RHYTHM INPUT
# ==========================================

tap_times = []

try:
    while True:

        line = ser.readline().decode(
            "utf-8",
            errors="ignore"
        ).strip()

        if line.startswith("TAP,"):

            timestamp = int(line.split(",")[1])

            # Filter duplicate sensor detections
            if len(tap_times) == 0 or timestamp - tap_times[-1] >= 250:

                tap_times.append(timestamp)

                print(f"TAP RECEIVED: {timestamp} ms")


# ==========================================
# STOP AND ANALYZE
# ==========================================

except KeyboardInterrupt:

    print("\nStopping...")

    if len(tap_times) > 1:

        intervals = []

        for i in range(1, len(tap_times)):

            interval = tap_times[i] - tap_times[i - 1]

            # Ignore very long pauses
            if interval < 2000:
                intervals.append(interval)


        # ==========================================
        # RHYTHM ANALYSIS
        # ==========================================

        print("\n--- RHYTHM ANALYSIS ---")

        print("Tap count:", len(tap_times))
        print("Intervals used:", intervals)

        if intervals:

            average_interval = statistics.mean(intervals)
            bpm = 60000 / average_interval

            print(
                f"\nAverage active interval: "
                f"{average_interval:.2f} ms"
            )

            print(
                f"Estimated active tempo: "
                f"{bpm:.2f} BPM"
            )


            # ==========================================
            # SPEED CLASSIFICATION
            # ==========================================

            if bpm < 80:
                speed = "SLOW"

            elif bpm < 120:
                speed = "MEDIUM"

            else:
                speed = "FAST"

            print(f"Rhythm speed: {speed}")


            # ==========================================
            # TREND DETECTION
            # ==========================================

            first_half = intervals[:len(intervals) // 2]
            second_half = intervals[len(intervals) // 2:]

            trend = "STABLE"

            if first_half and second_half:

                first_avg = statistics.mean(first_half)
                second_avg = statistics.mean(second_half)

                if second_avg < first_avg * 0.85:
                    trend = "ACCELERATING"

                elif second_avg > first_avg * 1.15:
                    trend = "SLOWING DOWN"

                else:
                    trend = "STABLE"

            print(f"Rhythm trend: {trend}")


            # ==========================================
            # SEND RHYTHM TO GEMINI
            # ==========================================

            print("\nSending rhythm analysis to Gemini...")

            prompt = f"""
You are the AI decision-making system of a robotic percussionist
inspired by Kerala Chenda Melam.

A human has tapped a rhythm with these characteristics:

Tap count: {len(tap_times)}
Tempo: {bpm:.2f} BPM
Speed: {speed}
Trend: {trend}

Your task is to create a complementary rhythmic response.

Return ONLY in exactly this format:

PATTERN: <a short rhythm using DHUM and TA>
TEMPO: <number between 60 and 160>
INTENSITY: <LOW, MEDIUM, or HIGH>

Do not include explanations.
Do not use markdown.
"""

            try:

                interaction = client.interactions.create(
                    model="gemini-3.6-flash",
                    input=prompt
                )

                print("\n--- GEMINI RHYTHM RESPONSE ---")
                print(interaction.output_text)

            except Exception as e:

                print("\nGemini connection error:")
                print(e)

        else:

            print(
                "Not enough valid rhythm intervals "
                "to analyze."
            )


# ==========================================
# CLEANUP
# ==========================================

finally:

    ser.close()

    print("\nSerial connection closed.")