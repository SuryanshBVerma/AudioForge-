import base64
import os
import logging
import io
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import soundfile as sf
import torch

from neuttsair.neutts import NeuTTSAir

# --- App State Management ---
# This dictionary will hold our loaded model and cached voice references
app_state = {}

# --- FastAPI App Initialization ---
app = FastAPI(
    title="NeuTTS-Air API",
    description="A TTS server with voice cloning from reference audio.",
    version="2.0.0"
)

# --- Model Loading and Caching Logic ---
device = "cuda" if torch.cuda.is_available() else "cpu"
logging.info(f"Loading NeuTTSAir model on device: {device} ...")
app_state["tts_model"] =  NeuTTSAir(
        backbone_repo="./local_models/backbone/",  # Path to the saved backbone folder
        codec_repo="./local_models/codec.pt",       # Path to the saved codec .pt file
        backbone_device="cpu", # or "cuda"
        codec_device="cpu"     # or "cuda"
    )
logging.info("Model loaded successfully.")

# --- Pre-load and Cache Reference Voices ---
logging.info("Pre-loading and caching reference voices...")
app_state["cached_references"] = {}

voice_types = {
    "MALE": {"audio": "samples/male.wav", "text": "samples/male.txt"},
    "FEMALE": {"audio": "samples/female.wav", "text": "samples/female.txt"}
}

for name, paths in voice_types.items():
    if not os.path.exists(paths["audio"]) or not os.path.exists(paths["text"]):
        logging.warning(f"Reference files for {name} not found. Skipping.")
        continue

    ref_text = open(paths["text"], "r").read().strip()
    ref_codes = app_state["tts_model"].encode_reference(paths["audio"])
    app_state["cached_references"][name] = {"text": ref_text, "codes": ref_codes}
    logging.info(f"Successfully cached reference for voice: {name}")

# --- Pydantic Models ---
class VoiceType(str, Enum):
    MALE = "MALE"
    FEMALE = "FEMALE"

class TTSRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=500, example="Hello, world. This is a test.")
    voice_type: VoiceType = Field(..., example=VoiceType.MALE)

class TTSResponseBase64(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV audio string.")
    input_text: str
    voice_type: str

# --- Helper Function for Inference ---
def run_inference(text: str, voice_type: VoiceType):
    """A helper function to run TTS inference and return audio data as bytes."""
    tts_model = app_state.get("tts_model")
    cached_refs = app_state.get("cached_references")

    if not tts_model:
        raise HTTPException(status_code=503, detail="TTS model is not available.")
    if voice_type.name not in cached_refs:
        raise HTTPException(status_code=404, detail=f"Reference voice for '{voice_type.name}' not found or failed to load.")

    try:
        logging.info(f"Running inference for voice '{voice_type.name}'...")
        reference = cached_refs[voice_type.name]
        
        # Perform inference using the main text and the cached reference data
        wav = tts_model.infer(text, reference["codes"], reference["text"])
        
        # Write the audio data to an in-memory buffer instead of a file
        buffer = io.BytesIO()
        sf.write(buffer, wav, 24000, format='WAV')
        buffer.seek(0)
        
        logging.info("Inference successful.")
        return buffer.read()

    except Exception as e:
        logging.error(f"An error occurred during inference: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate audio due to an internal error.")

# --- API Endpoints ---
@app.post("/generate-tts-base64/", response_model=TTSResponseBase64, tags=["TTS Generation"])
async def generate_tts_base64(request: TTSRequest):
    """
    Accepts text and a voice type, returns the synthesized audio as a Base64 encoded string.
    """
    audio_bytes = run_inference(request.text, request.voice_type)
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
    
    return TTSResponseBase64(
        audio_base64=audio_base64,
        input_text=request.text,
        voice_type=request.voice_type.name
    )

@app.post("/generate-tts-file/", response_class=StreamingResponse, tags=["TTS Generation"])
async def generate_tts_file(request: TTSRequest):
    """
    Accepts text and a voice type, returns the synthesized audio as a complete .wav file.
    """
    audio_bytes = run_inference(request.text, request.voice_type)
    
    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=output.wav"}
    )

@app.get("/", tags=["General"])
def read_root():
    return {"message": "NeuTTS-Air API is running."}
