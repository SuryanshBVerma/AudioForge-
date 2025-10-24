import base64
import os
import logging
import io

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

# Normalize local model paths to absolute paths so transformers/huggingface_hub treats them as local folders
backbone_local = os.path.abspath("neuttsair/local_models/backbone")
codec_local = os.path.abspath("neuttsair/local_models/codec.pt")

app_state["tts_model"] = NeuTTSAir(
    backbone_repo=backbone_local,
    codec_repo=codec_local,
    backbone_device=device,
    codec_device=device,
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
class TTSRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=500, example="Hello, world. This is a test.")
    # voice_type may be any voice name (e.g. "MALE", "dave"); server will look for samples/<name>.wav and samples/<name>.txt
    voice_type: str = Field(..., example="MALE")


class TTSResponseBase64(BaseModel):
    audio_base64: str = Field(..., description="Base64 encoded WAV audio string.")
    input_text: str
    voice_type: str
    # Optional warning when requested voice not found and fallback used
    warning: str | None = None

# --- Helper Function for Inference ---
def run_inference(text: str, voice_name: str):
    """A helper function to run TTS inference and return audio data as bytes.

    Behavior:
    - If `voice_name` matches a cached reference (case-insensitive), use it.
    - Else, check for `samples/{voice_name}.wav` and `samples/{voice_name}.txt`.
      - If found, encode and cache that reference and use it.
      - If not found, fall back to 'MALE' cached reference (if present) and return a warning.
    Returns (audio_bytes, warning_str_or_None)
    """
    tts_model = app_state.get("tts_model")
    cached_refs = app_state.get("cached_references")

    if not tts_model:
        raise HTTPException(status_code=503, detail="TTS model is not available.")

    requested = voice_name.upper()
    warning = None

    # Direct cached hit
    if requested in cached_refs:
        reference = cached_refs[requested]
    else:
        # Look for samples/<name>.wav and .txt (case-sensitive on Linux)
        audio_path = os.path.join("samples", f"{voice_name}.wav")
        text_path = os.path.join("samples", f"{voice_name}.txt")

        if os.path.exists(audio_path) and os.path.exists(text_path):
            try:
                ref_text = open(text_path, "r").read().strip()
                ref_codes = tts_model.encode_reference(audio_path)
                # Cache under upper-case key
                cached_refs[requested] = {"text": ref_text, "codes": ref_codes}
                reference = cached_refs[requested]
            except Exception as e:
                logging.error(f"Failed to encode dynamic reference '{voice_name}': {e}")
                reference = None
        else:
            reference = None

    # If still no reference, fall back to MALE
    if reference is None:
        if "MALE" in cached_refs:
            warning = f"Requested voice '{voice_name}' not found in samples/. Falling back to MALE."
            reference = cached_refs["MALE"]
        else:
            raise HTTPException(status_code=404, detail=f"Reference voice for '{voice_name}' not found and no MALE fallback available.")

    try:
        logging.info(f"Running inference for voice '{voice_name}' (using cached key)")
        wav = tts_model.infer(text, reference["codes"], reference["text"])

        buffer = io.BytesIO()
        sf.write(buffer, wav, 24000, format='WAV')
        buffer.seek(0)

        logging.info("Inference successful.")
        return buffer.read(), warning

    except Exception as e:
        logging.error(f"An error occurred during inference: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate audio due to an internal error.")

# --- API Endpoints ---
@app.post("/generate-tts-base64/", response_model=TTSResponseBase64, tags=["TTS Generation"])
async def generate_tts_base64(request: TTSRequest):
    """
    Accepts text and a voice type, returns the synthesized audio as a Base64 encoded string.
    """
    audio_bytes, warning = run_inference(request.text, request.voice_type)
    audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")

    return TTSResponseBase64(
        audio_base64=audio_base64,
        input_text=request.text,
        voice_type=request.voice_type,
        warning=warning,
    )

@app.post("/generate-tts-file/", response_class=StreamingResponse, tags=["TTS Generation"])
async def generate_tts_file(request: TTSRequest):
    """
    Accepts text and a voice type, returns the synthesized audio as a complete .wav file.
    """
    audio_bytes, warning = run_inference(request.text, request.voice_type)

    return StreamingResponse(
        io.BytesIO(audio_bytes),
        media_type="audio/wav",
        headers={"Content-Disposition": "attachment; filename=output.wav"}
    )

@app.get("/", tags=["General"])
def read_root():
    return {"message": "NeuTTS-Air API is running."}
