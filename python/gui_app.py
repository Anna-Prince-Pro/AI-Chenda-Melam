import os
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

import serial

from rhythm_input import (
    BAUD_RATE,
    DEBOUNCE_TIME,
    MIN_TAPS,
    PAUSE_THRESHOLD,
    analyze_rhythm,
    generate_ai_rhythm,
)
from rhythm_player import play_rhythm


class ChendaMelamApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Chenda Melam - Kaelix")
        self.root.geometry("1120x700")
        self.root.minsize(1040, 640)
        self.root.configure(bg="#130f0b")

        self.serial_connection = None
        self.worker_thread = None
        self.running = False
        self.processing = False
        self.events = queue.Queue()
        self.tap_times = []
        self.tap_lock = threading.Lock()
        self.audio_lock = threading.Lock()

        self.port_var = tk.StringVar(value=os.getenv("ARDUINO_PORT", "COM3"))
        self.status_var = tk.StringVar(value="Ready")
        self.audio_var = tk.StringVar(value="Audio ready")
        self.tap_count_var = tk.StringVar(value="0")
        self.bpm_var = tk.StringVar(value="--")
        self.speed_var = tk.StringVar(value="--")
        self.intensity_var = tk.StringVar(value="--")
        self.trend_var = tk.StringVar(value="--")
        self.pattern_var = tk.StringVar(value="Waiting for your rhythm...")

        self.colors = {
            "bg": "#130f0b",
            "panel": "#211912",
            "panel_2": "#302318",
            "line": "#4b3826",
            "gold": "#f7bd45",
            "cream": "#fff0cf",
            "muted": "#c7ad86",
            "green": "#70d489",
        }

        self.setup_styles()
        self.build_layout()
        self.root.after(80, self.process_events)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "TButton",
            background=self.colors["gold"],
            foreground="#1d1308",
            borderwidth=0,
            focusthickness=0,
            padding=(14, 10),
            font=("Segoe UI", 10, "bold"),
        )
        style.map(
            "TButton",
            background=[
                ("active", "#ffd777"),
                ("disabled", "#655138"),
            ],
            foreground=[("disabled", "#b8a27e")],
        )

    def build_layout(self):
        header = tk.Frame(self.root, bg=self.colors["bg"])
        header.pack(fill="x", padx=32, pady=(26, 12))

        tk.Label(
            header,
            text="AI Chenda Melam",
            bg=self.colors["bg"],
            fg=self.colors["cream"],
            font=("Segoe UI", 32, "bold"),
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Live rhythm input, Gemini response, Chenda audio output.",
            bg=self.colors["bg"],
            fg=self.colors["muted"],
            font=("Segoe UI", 13),
        ).pack(anchor="w", pady=(2, 0))

        main = tk.Frame(self.root, bg=self.colors["bg"])
        main.pack(fill="both", expand=True, padx=32, pady=(10, 28))
        main.columnconfigure(0, weight=3)
        main.columnconfigure(1, weight=2)
        main.rowconfigure(0, weight=1)

        left = tk.Frame(main, bg=self.colors["bg"])
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 18))
        left.rowconfigure(2, weight=1)

        right = tk.Frame(main, bg=self.colors["bg"])
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)

        self.build_controls(left)
        self.build_metrics(left)
        self.build_pattern(left)
        self.build_status(right)
        self.build_audio(right)
        self.build_log(right)

    def build_controls(self, parent):
        panel = self.card(parent)
        panel.pack(fill="x", pady=(0, 16))
        panel.columnconfigure(0, weight=1)
        panel.columnconfigure(1, weight=2)

        tk.Label(
            panel,
            text="Control",
            bg=self.colors["panel"],
            fg=self.colors["cream"],
            font=("Segoe UI", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 8))

        tk.Label(
            panel,
            textvariable=self.status_var,
            bg=self.colors["panel"],
            fg=self.colors["green"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=0, column=1, sticky="e", padx=20, pady=(18, 8))

        tk.Label(
            panel,
            text="Arduino port",
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=20)

        tk.Entry(
            panel,
            textvariable=self.port_var,
            bg=self.colors["panel_2"],
            fg=self.colors["cream"],
            insertbackground=self.colors["cream"],
            relief="flat",
            font=("Segoe UI", 14, "bold"),
            width=10,
        ).grid(row=2, column=0, sticky="w", padx=20, pady=(6, 20))

        buttons = tk.Frame(panel, bg=self.colors["panel"])
        buttons.grid(row=2, column=1, sticky="e", padx=20, pady=(6, 20))

        self.start_button = ttk.Button(
            buttons,
            text="Start",
            command=self.start_listening,
        )
        self.start_button.pack(side="left", padx=(0, 8))

        self.stop_button = ttk.Button(
            buttons,
            text="Stop",
            command=self.stop_listening,
            state="disabled",
        )
        self.stop_button.pack(side="left")

    def build_metrics(self, parent):
        grid = tk.Frame(parent, bg=self.colors["bg"])
        grid.pack(fill="x", pady=(0, 16))

        self.metric(grid, "Taps", self.tap_count_var, 0, 0)
        self.metric(grid, "BPM", self.bpm_var, 0, 1)
        self.metric(grid, "Speed", self.speed_var, 1, 0)
        self.metric(grid, "Intensity", self.intensity_var, 1, 1)
        self.metric(grid, "Trend", self.trend_var, 2, 0, columnspan=2)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

    def build_pattern(self, parent):
        panel = self.card(parent)
        panel.pack(fill="both", expand=True)

        tk.Label(
            panel,
            text="Generated Pattern",
            bg=self.colors["panel"],
            fg=self.colors["cream"],
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 8))

        tk.Label(
            panel,
            textvariable=self.pattern_var,
            bg=self.colors["panel"],
            fg=self.colors["gold"],
            font=("Consolas", 22, "bold"),
            wraplength=610,
            justify="left",
        ).pack(anchor="w", fill="both", expand=True, padx=20, pady=(8, 20))

    def build_status(self, parent):
        panel = self.card(parent)
        panel.grid(row=0, column=0, sticky="ew", pady=(0, 16))

        tk.Label(
            panel,
            text="Live Status",
            bg=self.colors["panel"],
            fg=self.colors["cream"],
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 4))

        tk.Label(
            panel,
            text=(
                "Tap at least 6 beats. Pause briefly to hear the AI response."
            ),
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Segoe UI", 11),
            wraplength=400,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 18))

    def build_audio(self, parent):
        panel = self.card(parent)
        panel.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        panel.columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="Audio Output",
            bg=self.colors["panel"],
            fg=self.colors["cream"],
            font=("Segoe UI", 17, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=20, pady=(18, 4))

        tk.Label(
            panel,
            textvariable=self.audio_var,
            bg=self.colors["panel"],
            fg=self.colors["gold"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

    def build_log(self, parent):
        panel = self.card(parent)
        panel.grid(row=2, column=0, sticky="nsew")
        parent.columnconfigure(0, weight=1)

        tk.Label(
            panel,
            text="Event Log",
            bg=self.colors["panel"],
            fg=self.colors["cream"],
            font=("Segoe UI", 17, "bold"),
        ).pack(anchor="w", padx=20, pady=(18, 8))

        self.log_box = tk.Text(
            panel,
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            insertbackground=self.colors["cream"],
            relief="flat",
            font=("Consolas", 10),
            wrap="word",
            height=13,
        )
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_box.configure(state="disabled")

    def card(self, parent):
        return tk.Frame(
            parent,
            bg=self.colors["panel"],
            highlightthickness=1,
            highlightbackground=self.colors["line"],
        )

    def metric(self, parent, label, value_var, row, column, columnspan=1):
        card = tk.Frame(parent, bg=self.colors["panel_2"])
        card.grid(
            row=row,
            column=column,
            columnspan=columnspan,
            sticky="ew",
            padx=6,
            pady=6,
        )

        tk.Label(
            card,
            text=label,
            bg=self.colors["panel_2"],
            fg=self.colors["muted"],
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w", padx=16, pady=(13, 0))

        tk.Label(
            card,
            textvariable=value_var,
            bg=self.colors["panel_2"],
            fg=self.colors["cream"],
            font=("Segoe UI", 23, "bold"),
        ).pack(anchor="w", padx=16, pady=(0, 14))

    def start_listening(self):
        if self.running:
            return

        if self.worker_thread and self.worker_thread.is_alive():
            self.log("Serial listener is still closing. Try again in a second.")
            return

        self.running = True
        self.processing = False
        with self.tap_lock:
            self.tap_times = []
        self.reset_metrics()
        self.status_var.set("Connecting...")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.worker_thread = threading.Thread(
            target=self.serial_worker,
            daemon=True,
        )
        self.worker_thread.start()

    def stop_listening(self):
        with self.tap_lock:
            tap_count = len(self.tap_times)

        if tap_count >= MIN_TAPS and not self.processing:
            self.log("Stopping after generating from current taps.")
            self.generate_from_current_taps(stop_after=True)
            return

        self.running = False
        self.status_var.set("Stopping...")

    def generate_from_current_taps(self, stop_after):
        with self.tap_lock:
            taps = self.tap_times[:]
            self.tap_times = []

        self.tap_count_var.set("0")

        threading.Thread(
            target=self.process_taps,
            args=(taps, self.serial_connection, stop_after),
            daemon=True,
        ).start()

    def reset_metrics(self):
        self.tap_count_var.set("0")
        self.bpm_var.set("--")
        self.speed_var.set("--")
        self.intensity_var.set("--")
        self.trend_var.set("--")
        self.pattern_var.set("Waiting for your rhythm...")
        self.audio_var.set("Audio ready")

    def serial_worker(self):
        port = self.port_var.get().strip()
        last_tap_time = None

        try:
            self.serial_connection = serial.Serial(
                port,
                BAUD_RATE,
                timeout=0.1,
            )
            time.sleep(2)
            self.serial_connection.reset_input_buffer()
            self.events.put(("status", f"Listening on {port}"))
            self.events.put(("log", "Connected. Tap a rhythm now."))

            while self.running:
                if self.serial_connection.in_waiting > 0:
                    line = (
                        self.serial_connection.readline()
                        .decode("utf-8", errors="ignore")
                        .strip()
                    )

                    if line.startswith("TAP,"):
                        timestamp = self.parse_tap(line)

                        if timestamp is None:
                            continue

                        if (
                            self.should_accept_tap(timestamp)
                        ):
                            with self.tap_lock:
                                self.tap_times.append(timestamp)
                                tap_count = len(self.tap_times)

                            last_tap_time = time.time()
                            self.events.put(("tap", (timestamp, tap_count)))

                with self.tap_lock:
                    has_enough_taps = len(self.tap_times) >= MIN_TAPS

                if (
                    has_enough_taps
                    and last_tap_time is not None
                    and time.time() - last_tap_time >= PAUSE_THRESHOLD
                    and not self.processing
                ):
                    with self.tap_lock:
                        taps = self.tap_times[:]
                        self.tap_times = []

                    last_tap_time = None

                    threading.Thread(
                        target=self.process_taps,
                        args=(taps, self.serial_connection, False),
                        daemon=True,
                    ).start()

                time.sleep(0.01)

        except serial.SerialException as error:
            self.events.put(("error", f"Could not connect to Arduino: {error}"))

        finally:
            if self.serial_connection:
                self.serial_connection.close()
                self.serial_connection = None

            self.running = False
            self.events.put(("stopped", None))

    def process_taps(self, taps, serial_connection, stop_after=False):
        if self.processing:
            return

        self.processing = True
        self.events.put(("status", "Analyzing rhythm..."))
        self.events.put(("log", "Phrase detected. Analyzing..."))

        analysis = analyze_rhythm(taps)

        if not analysis:
            self.events.put(("log", "Not enough clean taps. Try again."))
            self.events.put(("status", "Listening"))
            self.processing = False
            return

        self.events.put(("analysis", analysis))
        self.events.put(("status", "Asking Gemini..."))

        ai_response = generate_ai_rhythm(analysis)

        if not ai_response:
            self.events.put(("log", "Gemini did not return a response."))
            self.events.put(("status", "Listening"))
            self.processing = False
            return

        self.events.put(("response", ai_response))
        self.play_response(
            ai_response,
            analysis["intervals"],
            serial_connection,
        )
        self.events.put(("status", "Listening"))
        self.events.put(("log", "Ready for the next rhythm."))
        self.processing = False

        if stop_after:
            self.running = False

    def play_response(self, ai_response, input_intervals, serial_connection):
        self.events.put(("status", "Playing response..."))
        self.events.put(("audio", "Playing DHUM / TA response"))

        with self.audio_lock:
            play_rhythm(
                ai_response,
                input_intervals,
                serial_connection,
            )

        self.events.put(("audio", "Audio ready"))
        self.events.put(("status", "Listening" if self.running else "Ready"))

    def parse_tap(self, line):
        try:
            return int(line.split(",")[1])
        except (IndexError, ValueError):
            return None

    def should_accept_tap(self, timestamp):
        with self.tap_lock:
            return (
                not self.tap_times
                or timestamp - self.tap_times[-1] >= DEBOUNCE_TIME
            )

    def process_events(self):
        while not self.events.empty():
            event_type, value = self.events.get()

            if event_type == "status":
                self.status_var.set(value)

            elif event_type == "tap":
                timestamp, tap_count = value
                self.tap_count_var.set(str(tap_count))
                self.log(f"TAP {timestamp} ms")

            elif event_type == "analysis":
                self.bpm_var.set(f"{value['bpm']:.0f}")
                self.speed_var.set(value["speed"].replace("_", " "))
                self.intensity_var.set(value["intensity"])
                self.trend_var.set(value["trend"].replace("_", " "))
                self.log(
                    "Analysis: "
                    f"{value['bpm']:.0f} BPM, "
                    f"{value['speed']}, "
                    f"{value['intensity']}"
                )

            elif event_type == "response":
                self.pattern_var.set(self.extract_pattern(value))
                self.log("Gemini response received.")

            elif event_type == "audio":
                self.audio_var.set(value)

            elif event_type == "log":
                self.log(value)

            elif event_type == "error":
                self.status_var.set("Connection failed")
                self.log(value)
                messagebox.showerror("Arduino Connection", value)

            elif event_type == "stopped":
                self.status_var.set("Ready")
                self.start_button.configure(state="normal")
                self.stop_button.configure(state="disabled")
                self.log("Stopped.")

        self.root.after(80, self.process_events)

    def extract_pattern(self, response):
        for line in response.splitlines():
            if line.upper().startswith("PATTERN:"):
                return line.split(":", 1)[1].strip()

        return response

    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"{text}\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    def close(self):
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    app = ChendaMelamApp(root)
    root.protocol("WM_DELETE_WINDOW", app.close)
    root.mainloop()


if __name__ == "__main__":
    main()
