# Mirror-Motion

Mirror Motion Repository.

# Prerequisites

- Python 3.11

## Installation

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## FFmpeg Setup

Install ffmpeg for your system:

**macOS** (using Homebrew):
```bash
brew install ffmpeg
```

**Windows** (using winget):
```bash
winget install -e --id Gyan.FFmpeg
```


# Running the Back End

```
cd backend
python main.py
```

# Noted Issues

The version of mediapipe was downgraded based on https://github.com/google-ai-edge/mediapipe/issues/1928

```
python -m pip uninstall mediapipe -y
python -m pip install mediapipe==0.10.9
```


# Resources
- [Low poly 3D models](https://quaternius.com/)