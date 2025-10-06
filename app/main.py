import base64
import os
import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from neutts import TTS

# --- Basic Setup ---
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="NeuTTS-Air API",
    description="A simple API to generate audio from text using the NeuTTS-Air model.",
    version="1.0.0"
)

# --- Model Loading ---
# Load the TTS model once when the application starts.
# Using device="cpu" is recommended for broader compatibility in Docker containers
# without GPU access.
logger.info("Loading NeuTTS-Air model...")
try:
    tts_model = TTS(device="cpu")
    logger.info("Model loaded successfully.")
except Exception as e:
    logger.error(f"Failed to load TTS model: {e}")
    tts_model = None

# --- Request & Response Models ---
class TTSRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=500,
        example="Hello, this is a test of the text to speech model."
    )

class TTSResponse(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV audio string.")
    input_text: str

# --- API Endpoint ---
@app.post("/generate-tts/", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Accepts text input and returns the synthesized audio as a base64 encoded string.
    """
    if tts_model is None:
        return {"error": "TTS model is not available."}, 500

    temp_filename = "temp_output.wav"
    
    try:
        # Synthesize audio from the input text
        logger.info(f"Synthesizing audio for text: '{request.text[:30]}...'")
        tts_model.synthesize(request.text, temp_filename)
        
        # Read the generated audio file in binary mode
        with open(temp_filename, "rb") as audio_file:
            audio_bytes = audio_file.read()
        
        # Encode the binary audio data to base64
        audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
        
        logger.info("Successfully generated and encoded audio.")
        
        return TTSResponse(audio_base64=audio_base64, input_text=request.text)

    except Exception as e:
        logger.error(f"An error occurred during TTS synthesis: {e}")
        return {"error": "Failed to generate audio."}, 500
    
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

@app.get("/")
def read_root():
    return {"message": "NeuTTS-Air API is running. POST to /generate-tts/ to synthesize audio."}