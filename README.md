# Ignition AI Upscaler

Ignition AI Upscaler is a professional desktop application for upscaling low-quality videos into high-quality output using **PyQt6 + FFmpeg + Real-ESRGAN**.

## Features
- Premium multi-page desktop UI (Home, Settings, Processing, Completion)
- Drag & drop and multi-file selection workflow
- Video metadata preview (resolution, duration, FPS, file size)
- AI model choices (General, Anime, Face enhancement mode)
- GPU CUDA auto-detection with CPU fallback
- Processing controls: pause/resume, cancel, progress, ETA, usage metrics, logs
- Export controls (codec, bitrate, format, overwrite, output folder, presets)
- Dark/light mode toggle
- Auto-download model weights if missing
- Settings save/load
- Temp file cleanup after processing

## Project Structure
```text
main.py
ui/
models/
processing/
utils/
assets/
```

## Installation

### 1) Install Python dependencies
```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt
```

### 2) Install FFmpeg
#### Ubuntu / Debian
```bash
sudo apt update
sudo apt install ffmpeg
```
#### macOS (Homebrew)
```bash
brew install ffmpeg
```
#### Windows (Winget)
```powershell
winget install Gyan.FFmpeg
```

### 3) CUDA / GPU setup (optional, recommended)
1. Install NVIDIA driver (latest stable).
2. Install CUDA toolkit compatible with your PyTorch version.
3. Install torch with CUDA wheel, for example:
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```
4. Verify CUDA:
```bash
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```
If CUDA is unavailable, the app automatically falls back to CPU processing.

## Run
```bash
python main.py
```

## Notes for Production
- On first run, model files are downloaded automatically into `models/weights/`.
- For AV1 encoding, ensure your FFmpeg build has `libaom-av1` support.
- Face enhancement mode can be extended by integrating GFPGAN in `processing/pipeline.py`.

## Packaging suggestion
Use PyInstaller for distribution:
```bash
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "Ignition AI Upscaler" main.py
```
