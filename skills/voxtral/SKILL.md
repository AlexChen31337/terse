---
metadata.openclaw:
  always: true
  reason: "Auto-classified as always-load (no specific rule for 'voxtral')"
---

# Voxtral Voice Conversation Skill

## Overview

**Voxtral** provides end-to-end voice conversation capabilities for EvoClaw, combining:

- **Voice Recognition**: Faster-Whisper (CUDA-accelerated on RTX 3090)
- **LLM Integration**: Seamless connection to EvoClaw agent
- **Voice Synthesis**: Google Text-to-Speech (gTTS)
- **Video Animation**: SadTalker talking head generation

## Features

### Core Pipeline

1. **Microphone Input** → Real-time audio capture
2. **Transcription** → Whisper model (base/small/medium/large)
3. **LLM Processing** → Send to EvoClaw agent for response
4. **Text-to-Speech** → gTTS audio generation
5. **Video Animation** → SadTalker creates talking head video

### Supported Tools

#### `voice_conversation`
Start a complete voice conversation loop with:
- Multi-turn dialogue
- Real-time transcription
- LLM response generation
- Optional video output with talking head

```bash
evoclaw voice_conversation --turns 3 --record_duration 5
```

#### `transcribe_audio`
Transcribe audio files using CUDA-accelerated Whisper:

```python
result = transcribe_audio(audio_path="recording.wav", language="en")
```

#### `text_to_speech`
Convert text to speech audio:

```python
text_to_speech(
    text="Hello world",
    output_path="output.mp3",
    language="en"
)
```

#### `generate_talking_head`
Generate animated talking head video:

```python
generate_talking_head(
    audio_path="response.mp3",
    avatar_image="avatar.png",
    output_path="video.mp4"
)
```

## Requirements

### Hardware
- **GPU**: NVIDIA RTX 3090 or better (CUDA 12.0+)
- **RAM**: 16GB+ recommended
- **Storage**: 10GB+ for models

### Software
- Python 3.11+
- CUDA Toolkit 12.0+
- ffmpeg
- PortAudio (for sounddevice)

## Installation

### 1. Install Dependencies

```bash
# Create conda environment
conda create -n voxtral python=3.11 -y
conda activate voxtral

# Install Python packages
pip install faster-whisper gtts sounddevice soundfile pydub numpy
```

### 2. Setup Whisper Model

Models auto-download on first use:

- `tiny` ~ 40MB - Fastest, lowest accuracy
- `base` ~ 150MB - Good balance (default)
- `small` ~ 460MB - Better accuracy
- `medium` ~ 1.5GB - High accuracy
- `large-v3` ~ 3GB - Best accuracy

### 3. Verify SadTalker

```bash
cd /data/ai-stack/sadtalker
python inference.py --help
```

## Configuration

Edit `skill.toml`:

```toml
[config]
whisper_model = "base"      # Model size
device = "cuda"              # cuda or cpu
compute_type = "float16"     # float16 or int8
sadtalker_path = "/data/ai-stack/sadtalker"
output_dir = "/tmp/voxtral_output"
```

## Usage

### Basic Voice Conversation

```python
from voxtral import VoxtralLoop

loop = VoxtralLoop(
    whisper_model="base",
    device="cuda",
    avatar_image="path/to/avatar.png"
)

# Run 3-turn conversation
loop.run_conversation_loop(num_turns=3, record_duration=5)
```

### Custom LLM Endpoint

```python
loop = VoxtralLoop(
    llm_endpoint="http://localhost:8000/chat"
)
```

## Troubleshooting

### CUDA Out of Memory
- Use smaller model: `--whisper-model tiny`
- Reduce `compute_type` to `int8`

### Microphone Not Found
- Check permissions: `arecord -L`
- Install PortAudio: `sudo apt install libportaudio2`

### SadTalker Errors
- Verify models are downloaded
- Check avatar image path exists
- Ensure ffmpeg is installed

## Performance

| Model | RTF (Real-Time Factor) | VRAM Usage |
|-------|-------------------------|-------------|
| tiny  | 0.05x (20x realtime) | 1GB |
| base  | 0.1x (10x realtime)  | 2GB |
| small | 0.15x (7x realtime)   | 3GB |
| medium | 0.3x (3x realtime)    | 5GB |

**Latency**: ~200ms per phrase on RTX 3090 (base model)

## Integration

### Desktop Tools (Microphone Access)

The skill integrates with `desktop-tools` for microphone access:

```bash
evoclash desktop-tools --mode microphone --listen
```

### EvoClaw Agent Integration

Send transcribed text to agent:

```python
def get_llm_response(self, text):
    # Integration with EvoClaw agent
    response = requests.post(
        "http://localhost:8000/agent/chat",
        json={"message": text}
    )
    return response.json()["reply"]
```

## Error Handling

The skill includes graceful fallbacks:

1. **CUDA unavailable** → Falls back to CPU
2. **Mic not detected** → File input mode
3. **SadTalker fails** → Audio-only response
4. **Network error** → Local echo response

## License

MIT License - See LICENSE file

## Credits

- **Whisper**: OpenAI (faster-whisper by guillaumekln)
- **gTTS**: Google Text-to-Speech
- **SadTalker**: Talking head generation
