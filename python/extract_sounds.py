import os

# --------------------------------------------------
# FFmpeg configuration
# --------------------------------------------------

FFMPEG_BIN = (
    r"C:\Users\ANNA\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg.Shared_Microsoft.Winget.Source_8wekyb3d8bbwe"
    r"\ffmpeg-9.0.1-full_build-shared\bin"
)

# Add FFmpeg folder to PATH for this Python program
os.environ["PATH"] = FFMPEG_BIN + os.pathsep + os.environ["PATH"]

# Import pydub AFTER setting PATH
from pydub import AudioSegment
from pydub import utils

# Explicitly tell pydub where FFmpeg is
AudioSegment.converter = os.path.join(FFMPEG_BIN, "ffmpeg.exe")
AudioSegment.ffprobe = os.path.join(FFMPEG_BIN, "ffprobe.exe")

# Override pydub's internal FFmpeg detection
utils.get_prober_name = lambda: os.path.join(
    FFMPEG_BIN,
    "ffprobe.exe"
)

utils.get_encoder_name = lambda: os.path.join(
    FFMPEG_BIN,
    "ffmpeg.exe"
)


# --------------------------------------------------
# PROJECT PATHS
# --------------------------------------------------

# AI-Chenda-Melam project folder
BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

# Original Chenda audio
input_path = os.path.join(
    BASE_DIR,
    "sounds",
    "chenda.ogg"
)

# Output folder
output_folder = os.path.join(
    BASE_DIR,
    "sounds"
)


# --------------------------------------------------
# LOAD AUDIO
# --------------------------------------------------

print("Loading Chenda audio...")

audio = AudioSegment.from_file(
    input_path,
    format="ogg"
)

print(
    f"Audio duration: {len(audio) / 1000:.2f} seconds"
)


# --------------------------------------------------
# EXTRACT TEMPORARY SOUND SAMPLES
# --------------------------------------------------

# DHUM = deeper drum sound
dhum = audio[1000:1400]

# TA = sharper drum sound
ta = audio[3000:3300]


# --------------------------------------------------
# OUTPUT PATHS
# --------------------------------------------------

dhum_path = os.path.join(
    output_folder,
    "dhum.wav"
)

ta_path = os.path.join(
    output_folder,
    "ta.wav"
)


# --------------------------------------------------
# EXPORT SOUND FILES
# --------------------------------------------------

print("Creating DHUM sample...")

dhum.export(
    dhum_path,
    format="wav"
)

print("Creating TA sample...")

ta.export(
    ta_path,
    format="wav"
)


# --------------------------------------------------
# FINISHED
# --------------------------------------------------

print("\nDone!")
print("Created:")
print(" - sounds/dhum.wav")
print(" - sounds/ta.wav")