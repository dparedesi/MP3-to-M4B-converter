# MP3 to M4B Converter

A simple but versatile tool to convert MP3 files into M4B audiobook format, available as both a **command-line script** and a **graphical user interface (GUI)** application. Perfect for organizing podcasts, lectures, or audiobooks with chapter markers and metadata.

![GUI Screenshot](https://github.com/dparedesi/MP3-to-M4B-converter/blob/fc574e1d145cb911f4009b46a1dcf016bac9a9f8/src/resources/screenshot.png)

## Features

### Command-Line Interface (CLI)
- Batch convert MP3 files from an `inputs` folder to a single M4B file.
- Merge files into one track or split into chapters.
- Customize title, author, and metadata.

### Graphical User Interface (GUI)
- Drag-and-drop file management.
- Custom cover art support (PNG/JPG).
- Edit metadata (title, author).
- Toggle between merged output or chapter-based M4B.
- Progress bar and error handling.
- Cross-platform compatibility.

---

## Prerequisites

- **FFmpeg & FFprobe**: Required for both CLI and GUI.
  - Download from [ffmpeg.org](https://ffmpeg.org/)
  - Add to system PATH ([instructions](https://phoenixnap.com/kb/ffmpeg-windows)).
- **Python 3.9+**

---

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/MP3-to-M4B-converter.git
   cd MP3-to-M4B-converter
    ```
2. **Install dependencies for the GUI:**:
    ```bash
    pip install -r src/requirements.txt
    ```
---

## Usage

### Command-Line Tool (`mp3-to-m4b-converter.py`)
1. Place MP3 files in the `inputs` folder.
2. Edit the script's **user-configurable variables** at the top of the file:
   ```python
   INPUT_FOLDER = "inputs"    # Default input folder (no trailing slash)
   OUTPUT_FOLDER = "outputs"  # Output folder
   TITLE = "My Audiobook"     # M4B title (avoid special characters)
   AUTHOR = "John Doe"        # Author name
   MERGE = False               # True = single merged file, False = chapter markers
   ```
3. Run the script:
    ```bash
    python mp3-to-m4b-converter.py
    ```
4. Find your `.m4b` file in the `outputs` folder, named after your title.

### GUI Application (`src/main.py`)
1. Launch the app:
   ```bash
   cd src
   python main.py
   ```
*(Windows users: Double-click `main.py` if Python is associated with `.py` files)*

2. **Add Files**:
   - Click **"+ Add Media"** to select MP3 files (supports multi-select).
   - Drag-and-drop files directly into the table.
   - Reorder files using **↑ Up**/**↓ Down** buttons or delete via right-click context menu.

3. **Customize**:
   - **Title/Author**: Enter metadata in the right panel.
   - **Cover Art**: Drag-and-drop an image or click the upload area (supports PNG/JPG).
   - **Merge Mode**: Toggle the switch to combine files into one track (disables chapter names).

4. **Output**:
   - Click **"Save To…"** to choose a folder (default: system Downloads folder).
   - Click **"Convert"** to start. Progress bar will show real-time status.

5. **Result**:
   - Output file: `<Title>.m4b` in your chosen folder.
   - Chapter names (if Merge Mode is off) match original filenames (e.g., `Chapter_01.mp3` → "Chapter 01").