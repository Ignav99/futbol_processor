# ⚽ Football Match Panoramic Video Processor

Automated system for processing football matches recorded with two Wolfgang GA120 action cameras, generating panoramic videos and automatic ball-tracking footage.

> 🇪🇸 [Documentación completa en español](docs/LEEME.md)

---

## 🎯 Overview

This project processes videos from two action cameras mounted on a tripod, each pointing at one half of the football field, and automatically:
- Merges both cameras into a full panoramic view
- Synchronizes videos using audio (clap detection)
- Concatenates multiple video files (cameras record in ~18min segments)
- Generates two output videos:
  - **Tactical View**: Full field panorama
  - **Tracking View**: Automatic zoom following the ball
- Uploads videos to Google Drive

---

## ✨ Features

**Phase 1 (Current):**
- ✓ Automatic dual-camera panorama fusion
- ✓ Audio-based synchronization (clap detection)
- ✓ Multi-file automatic concatenation
- ✓ Lens distortion correction
- ✓ Ball detection and tracking
- ✓ Two output formats (tactical + tracking)
- ✓ Google Drive auto-upload

**Phase 2 (Future):**
- Event detection (goals, shots, passes)
- Automatic highlights
- Match statistics
- Player heatmaps
- Offside detection

---

## 🚀 Quick Start

### 1. Installation

```bash
cd ~
git clone https://github.com/Ignav99/futbol_processor.git
cd futbol_processor
bash setup_inicial.sh
```

### 2. Initial Setup (One-time)

```bash
source ~/futbol_processor_env/bin/activate

# Calibrate cameras
python3 scripts/calibrar_camaras.py

# Configure homography (camera alignment)
python3 scripts/configurar_homografia.py

# Setup Google Drive
python3 scripts/configurar_drive.py
```

### 3. Process a Match

Copy your videos to:
- Left camera → `~/Desktop/raw_video_left/`
- Right camera → `~/Desktop/raw_video_right/`

Then run:
```bash
# Double-click on:
PROCESAR_PARTIDO.command

# Or in terminal:
source ~/futbol_processor_env/bin/activate
python3 scripts/procesar_partido.py
```

---

## 📋 Requirements

### Hardware
- macOS
- 2x Wolfgang GA120 Action Cameras
- Tripod
- ~20GB free disk space per match

### Recording Specs
- Resolution: 2.7K
- FPS: 30
- Format: MP4/MOV
- Audio: Required for synchronization

### Software
- Python 3.8+
- ffmpeg
- OpenCV
- See `requirements.txt` for full dependencies

---

## 📁 Project Structure

```
futbol_processor/
├── scripts/
│   ├── calibrar_camaras.py        # Camera calibration
│   ├── configurar_homografia.py   # Camera alignment
│   ├── configurar_drive.py        # Google Drive setup
│   ├── procesar_partido.py        # Main processing script
│   └── verificar_instalacion.py   # Verify installation
├── docs/
│   └── LEEME.md                   # Full documentation (Spanish)
├── setup_inicial.sh               # Automated installation
├── requirements.txt               # Python dependencies
└── PROCESAR_PARTIDO.command       # macOS launcher
```

---

## 🎥 How It Works

1. **Concatenation**: Merges multiple video files from each camera chronologically
2. **Synchronization**: Uses audio cross-correlation to detect clap and sync videos
3. **Distortion Correction**: Applies camera calibration to fix lens distortion
4. **Panorama Fusion**: Warps and merges both camera views using homography
5. **Ball Detection**: Finds the ball in each frame using color detection + Hough circles
6. **Tracking View**: Creates zoom view following ball position with smoothing
7. **Upload**: Automatically uploads to Google Drive

---

## 💡 Tips

- **Recording**: Give a loud clap near both cameras at the start
- **Position**: Keep cameras in the same position as during calibration
- **Ball**: Works best with white balls in good lighting
- **Processing Time**: ~2-3x match duration

---

## 🔧 Troubleshooting

### ffmpeg not found
```bash
brew install ffmpeg
```

### Poor synchronization
- Make sure clap is loud and audible in both cameras
- Check that audio is enabled

### Ball detection issues
- Ensure white ball
- Improve field lighting
- Adjust parameters in `detectar_balon()`

### Videos don't align
- Ensure cameras are in same position as calibration
- Redo homography configuration

Full troubleshooting guide in [Spanish docs](docs/LEEME.md).

---

## 🛣️ Roadmap

- [ ] Automatic event detection
- [ ] Highlight reel generation
- [ ] Match statistics and analytics
- [ ] Player tracking
- [ ] Interactive timeline
- [ ] Web interface

---

## 👤 Author

**Ignacio Navarro**
- GitHub: [@Ignav99](https://github.com/Ignav99)

---

## 📄 License

Personal use project. Contact author for usage.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repo
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

---

**Made with ❤️ for football analysis**
