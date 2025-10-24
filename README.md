# Audio Forge (TTS in your own voice)


This project provides a local Text-to-Speech (TTS) service that can clone a voice from an audio sample and then generate speech in that same voice. It is designed to be a self-contained service that you can run locally.

## Try it out for free

You can try out the `neutts-air` model live on [Hugging Face Spaces](https://huggingface.co/spaces/neuphonic/neutts-air)

## How it Works

The service uses the `NeuTTS-Air` model for voice cloning and speech synthesis. When the service starts, it pre-loads and caches voice references from the audio samples provided in the `app/samples` directory.

The core logic is exposed via a FastAPI server, which provides API endpoints to generate speech from text using one of the pre-cached voices. The entire application is containerized using Docker for easy setup and deployment.

## Features

*   **Voice Cloning:** Clone any voice by providing a high-quality audio sample.
*   **Text-to-Speech:** Generate natural-sounding speech from text in the cloned voice.
*   **FastAPI Service:** Exposes the TTS functionality through a simple and clean REST API.
*   **Dockerized:** Easy to run and deploy using Docker.
*   **Pre-cached Voices:** Comes with pre-cached male and female voices for immediate use.

## Tech Stack

*   **Model:** `NeuTTS-Air`
*   **Framework:** `FastAPI`
*   **Audio Processing:** `librosa`, `soundfile`
*   **Phonemization:** `phonemizer`
*   **Containerization:** `Docker`

## Setup Instructions

> **Performance Considerations :** For optimal performance, it is recommended to run this service in a Linux environment where Docker is installed natively. When running on Windows or macOS via Docker Desktop, the service may experience significantly slower performance due to the overhead of the underlying virtual machine.


### 1. Download the Models

Before building the Docker image, you need to download the pre-trained models. The `save_models.py` script will download and save the necessary model files into the `app/neuttsair/local_models` directory.

Navigate to the `app/neuttsair` directory and run the script:

```bash
cd app/neuttsair
python save_models.py
```

### 2. Build the Docker Image

Once the models are downloaded, you can build the Docker image. Navigate back to the root of the project and run the following command:

```bash
docker build -t tts-service .
```

This will build a Docker image with the tag `tts-service`.

### 3. Run the Docker Container

After the image is built, you can run it as a container. The following command will start the container and map the service's port (8000) to the same port on your host machine.

```bash
docker run -p 8000:8000 tts-service
```

The TTS service will now be running and accessible at `http://localhost:8000`.

## Using Your Own Voice

You can configure the service to use your own voice by following these steps:

### Step 1: Record Your Voice Sample

Record a sample of your voice, keeping the following guidelines in mind for the best results:

*   **Format:** Mono channel, 16-44 kHz sample rate, saved as a `.wav` file.
*   **Length:** Between 3 and 15 seconds.
*   **Quality:** The audio should be clean, with minimal to no background noise.
*   **Content:** Use natural, continuous speech, like a monologue or conversation with few pauses. This helps the model capture the tone of your voice effectively.

### Step 2: Add the Audio and Transcript

1.  Place your recorded `.wav` file in the `app/samples` directory. For example, name it `my_voice.wav`.
2.  Create a text file (`.txt`) containing the exact transcript of your recording. The name of the text file should match the name of your `.wav` file. For example, if your audio file is `my_voice.wav`, the transcript file should be `my_voice.txt`.
3.  Place the transcript file in the same `app/samples` directory.

### Step 3: Use Your Voice in an API Call

The service will automatically detect and load new voices from the `samples` directory.

To use your voice, simply make an API call and set the `voice_type` parameter to the name of your audio file (without the `.wav` extension).

For example, if you added `my_voice.wav` and `my_voice.txt` to the `app/samples` directory, you would use `"my_voice"` as the `voice_type`:

**Request Body:**
```json
{
  "text": "This is a test of my own voice.",
  "voice_type": "my_voice"
}
```

The service will find your audio sample, encode it, cache it for future requests, and use it to generate the speech.


## API Endpoints

The service exposes the following endpoints:

### 1. Generate TTS (Base64)

*   **Endpoint:** `POST /generate-tts-base64/`
*   **Description:** Accepts text and a voice type, and returns the synthesized audio as a Base64 encoded WAV string. This is useful for applications that need to handle the audio data directly without saving it to a file.
*   **Request Body:**
    ```json
    {
      "text": "Hello, world. This is a test.",
      "voice_type": "MALE"
    }
    ```
    *   `text` (string, required): The text to be converted to speech. Must be between 3 and 500 characters.
    *   `voice_type` (string, required): The voice to use for the synthesis. Can be either `"MALE"` or `"FEMALE"`.
*   **Response Body:**
    ```json
    {
      "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAAABkYXRhIAAAAA...",
      "input_text": "Hello, world. This is a test.",
      "voice_type": "MALE"
    }
    ```
    *   `audio_base64` (string): The Base64 encoded WAV audio data.
    *   `input_text` (string): The input text that was synthesized.
    *   `voice_type` (string): The voice type used for the synthesis.

### 2. Generate TTS (File)

*   **Endpoint:** `POST /generate-tts-file/`
*   **Description:** Accepts text and a voice type, and returns the synthesized audio as a `.wav` file. This is useful for directly downloading the audio file.
*   **Request Body:**
    ```json
    {
      "text": "Hello, world. This is a test.",
      "voice_type": "FEMALE"
    }
    ```
    *   `text` (string, required): The text to be converted to speech. Must be between 3 and 500 characters.
    *   `voice_type` (string, required): The voice to use for the synthesis. Can be either `"MALE"` or `"FEMALE"`.
*   **Response:**
    *   The response is a `.wav` audio file with the `Content-Disposition` header set to `attachment; filename=output.wav`.

### 3. Health

*   **Endpoint:** `GET /`
*   **Description:** A simple health check endpoint to confirm that the service is running.
*   **Response:**
    ```json
    {
      "message": "NeuTTS-Air API is running."
    }
    ```

## Credits

This project uses the open-source `neutts-air` model from neuphonic. You can find the original repository here: [Neutts-Air](https://github.com/neuphonic/neutts-air/tree/main)
