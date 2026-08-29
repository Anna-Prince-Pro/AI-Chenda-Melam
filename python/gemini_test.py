import os
from dotenv import load_dotenv
from google import genai

# Load API key from .env
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("ERROR: GEMINI_API_KEY not found!")
    exit()

# Create Gemini client
client = genai.Client(api_key=api_key)

print("Connecting to Gemini...")

interaction = client.interactions.create(
    model="gemini-3.6-flash",
    input=(
        "You are the AI brain of a robotic Chenda percussionist. "
        "Say hello in one short sentence."
    )
)

print("\n--- GEMINI RESPONSE ---")
print(interaction.output_text)