import serial
import time
import statistics

PORT = "COM3"
BAUD_RATE = 9600

print("Connecting to Arduino...")

ser = serial.Serial(PORT, BAUD_RATE, timeout=1)

time.sleep(2)

print("Connected!")
print("Start tapping...")
print("Press Ctrl + C to analyze the rhythm.\n")

tap_times = []

try:
    while True:
        line = ser.readline().decode("utf-8", errors="ignore").strip()

        if line.startswith("TAP,"):
            timestamp = int(line.split(",")[1])

            # Filter duplicate sensor detections
            if len(tap_times) == 0 or timestamp - tap_times[-1] >= 250:
                tap_times.append(timestamp)
                print(f"TAP RECEIVED: {timestamp} ms")

except KeyboardInterrupt:

    print("\nStopping...")

    if len(tap_times) > 1:

        intervals = []

        for i in range(1, len(tap_times)):
            interval = tap_times[i] - tap_times[i - 1]

            # Ignore very long pauses from tempo calculation
            if interval < 2000:
                intervals.append(interval)

        print("\n--- RHYTHM ANALYSIS ---")
        print("Tap count:", len(tap_times))
        print("Intervals used:", intervals)

        if intervals:
            average_interval = statistics.mean(intervals)
            bpm = 60000 / average_interval

            print(f"\nAverage active interval: {average_interval:.2f} ms")
            print(f"Estimated active tempo: {bpm:.2f} BPM")

            # Classify speed
            if bpm < 80:
                speed = "SLOW"
            elif bpm < 120:
                speed = "MEDIUM"
            else:
                speed = "FAST"

            print(f"Rhythm speed: {speed}")

            # Detect acceleration
            first_half = intervals[:len(intervals)//2]
            second_half = intervals[len(intervals)//2:]

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

finally:
    ser.close()
    print("\nSerial connection closed.")