# 🌌 Echer OS Layer

[![Local AI](https://img.shields.io/badge/Local%20AI-Ollama-blueviolet?style=for-the-badge)](https://ollama.com)
[![GUI](https://img.shields.io/badge/UI-PyQt6-blue?style=for-the-badge)](https://www.riverbankcomputing.com/software/pyqt/)
[![OCR](https://img.shields.io/badge/OCR-EasyOCR-green?style=for-the-badge)](https://github.com/JaidedAI/EasyOCR)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

<video src="assets/echer_demo.mp4" width="100%" controls autoplay loop muted></video>

**Echer** is a native, premium, transparent OS overlay assistant that runs completely offline and locally on Windows. Built using PyQt6, it provides a seamless, context-aware bridge between your local LLM and what is currently happening on your screen.

With a simple keystroke, Echer sweeps under your active windows, captures your screen text, and lets you query your local AI companion about anything you are currently looking at—whether you're debugging code, analyzing system performance, reading complex documents, or browsing the web.

---

## ✨ Features

* **⚡ Instant summoning:** Summon or hide Echer instantly from any background state using a global keyboard shortcut (`Ctrl + Space`).
* **🪟 Context-Aware Perception:** Smartly captures either your primary monitor (`🖥️ Full Screen`) or just the coordinates of the application window you were working in (`🪟 Active Window`).
* **👻 100% Invisible Capture:** Uses a pre-focus caching mechanism and DWM fade-out buffers to ensure that Echer hides itself completely before snapping your screen, making it completely invisible to its own screenshot engine.
* **🧠 Offline OCR Intelligence:** Powered by a local `easyocr` (PyTorch) pipeline running on your CPU (leaving 100% of your GPU's VRAM free for the LLM). Employs pre-warming threads to parse full screenshots in under 1.5 seconds.
* **🎨 Glassmorphic "Dynamic Island" UI:** A luxurious, semi-translucent dark frosted-glass overlay featuring rounded bubble corners, neon aura drop-shadows, responsive VS Code-style Markdown rendering, and fluid height-expansion animations.
* **🔒 Purely Local & Private:** Zero cloud dependencies, zero external APIs, and zero data tracking. Your screenshots and queries never leave your PC.

---

## 🛠️ Tech Stack

* **Core & GUI:** Python 3.11, `PyQt6` (translucent frameless widgets)
* **Screen Capturing:** `mss` (high-speed primary monitor and cropped boundaries captures)
* **OCR Text Parsing:** `easyocr` (CPU-based ResNet & CRAFT neural networks)
* **Keyboard Hooks:** `pynput` (thread-safe global keyboard shortcuts routed via `pyqtSignal`)
* **Local Brain:** `Ollama` hosting `gemma2:2b` (prioritizes fastest downloaded model on startup)

---

## 🚀 Installation & Setup

### 1. Prerequisites
* **Python 3.11** (Recommended)
* **Ollama** installed on your Windows machine: [https://ollama.com](https://ollama.com)
* Download the fast and accurate Gemma 2 model in your terminal:
  ```bash
  ollama run gemma2:2b
  ```

### 2. Clone & Setup Environment
Navigate to your desired directory and clone/copy this repository, then create and activate a virtual environment:
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\Activate.ps1

# Install dependencies
pip install PyQt6 easyocr mss pynput requests pygetwindow markdown opencv-python-headless
```

### 3. Run Echer
To start Echer in interactive console mode:
```powershell
python main.py
```

---

## 📂 Project Structure

```
echer/
├── core/
│   ├── ai/
│   │   └── llm_controller.py      # Handles Ollama connectivity and model loading
│   ├── ui/
│   │   └── main_window.py          # Frosted-glass UI, keyboard hook, thread-safe slots
│   └── vision/
│       ├── ocr_parser.py           # Pre-warmed singleton EasyOCR CPU engine
│       └── screen_capture.py       # High-speed window and full screen captures
├── assets/                         # Visual resources (walkthrough video, etc.)
├── captures/                       # Temporary folder for screenshots (auto-created)
├── .gitignore                      # Excludes virtual environments and captures
├── main.py                         # App entrypoint
└── README.md                       # Documentation
```

---

## 🎮 How to Use

1. Double-click **`Start_Ollama.bat`** to start your local Ollama server in the background.
2. Double-click **`Start_Echer.bat`** (or `Start_Echer_Debug.bat` to see terminal logs) to boot Echer silently in the background.
3. Open any application (e.g. VS Code, a browser, VLC, or your desktop).
4. Press **`Ctrl + Space`**.
5. The Echer search pill will slide onto your screen. Type your question (e.g., *"What window is active?"* or *"Explain this error on my screen"*) and press **Enter**.
6. Echer will automatically slide out of the way, take a clean capture, feed it to Gemma, and stream a beautifully formatted response directly into its glassmorphic response area.
7. Click the close button (`✕`) or press **`Ctrl + Space`** again to dismiss Echer.

---

## 🔒 Privacy & Security

Echer is built from the ground up for strict local operation. 
* All screenshots are saved to a temporary folder (`captures/`) inside your local project folder and overwritten on every new query.
* No data is sent over HTTP to external servers. The local API URL points strictly to `http://localhost:11434`.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
