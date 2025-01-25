import os
import subprocess
import sys
import json

# User-configurable variables
INPUT_FOLDER = "inputs"
OUTPUT_FOLDER = "outputs"
TITLE = "Write the title"
AUTHOR = "Write the name of the author"
MERGE = True  # Set to True for simple merge without chapters

def get_duration(file_path):
    """Get audio duration in seconds using ffprobe."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    return float(data['format']['duration'])

def create_chapter_metadata(mp3_files, metadata_path):
    """Create FFmpeg metadata file with chapter information."""
    start_time = 0.0
    
    with open(metadata_path, 'w') as f:
        f.write(";FFMETADATA1\n")
        for mp3 in mp3_files:
            file_path = os.path.join(INPUT_FOLDER, mp3)
            duration = get_duration(file_path)
            chapter_title = os.path.splitext(mp3)[0].replace("_", " ")
            
            f.write("[CHAPTER]\n")
            f.write("TIMEBASE=1/1000\n")
            f.write(f"START={int(start_time * 1000)}\n")
            f.write(f"END={int((start_time + duration) * 1000)}\n")
            f.write(f"title={chapter_title}\n\n")
            
            start_time += duration

def merge_mp3s(mp3_files, output_path):
    """Merge multiple MP3 files into one, preserving original streams."""
    filelist_path = os.path.join(OUTPUT_FOLDER, "merge_list.txt")
    
    with open(filelist_path, 'w') as f:
        for mp3 in mp3_files:
            input_path = os.path.abspath(os.path.join(INPUT_FOLDER, mp3))
            f.write(f"file '{input_path}'\n")
    
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", filelist_path,
        "-c", "copy",
        output_path
    ]
    
    try:
        print("Merging MP3 files...")
        subprocess.run(cmd, check=True)
    finally:
        if os.path.exists(filelist_path):
            os.remove(filelist_path)

def main():
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    
    input_folder = INPUT_FOLDER
    
    mp3_files = sorted([f for f in os.listdir(input_folder) if f.lower().endswith('.mp3')])
    if not mp3_files:
        print("Error: No MP3 files found in input folder")
        sys.exit(1)

    final_mp3 = os.path.join(OUTPUT_FOLDER, "merged_temp.mp3") if MERGE else None
    filelist_path = os.path.join(OUTPUT_FOLDER, "filelist.txt")
    metadata_path = os.path.join(OUTPUT_FOLDER, "metadata.txt")

    if MERGE:
        merge_mp3s(mp3_files, final_mp3)
        mp3_files = ["merged_temp.mp3"]
        input_folder = OUTPUT_FOLDER

    with open(filelist_path, 'w') as f:
        for mp3 in mp3_files:
            input_path = os.path.abspath(os.path.join(input_folder, mp3))
            f.write(f"file '{input_path}'\n")

    if not MERGE:
        create_chapter_metadata(mp3_files, metadata_path)
    else:
        with open(metadata_path, 'w') as f:
            f.write(";FFMETADATA1\n")

    output_filename = f"{TITLE}.m4b".replace(" ", "_")
    output_path = os.path.join(OUTPUT_FOLDER, output_filename)

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", filelist_path,
        "-i", metadata_path,
        "-map", "0:a",
        "-map_metadata", "1",
        "-c:a", "aac",
        "-b:a", "128k",
        "-metadata", f"title={TITLE}",
        "-metadata", f"artist={AUTHOR}",
        "-movflags", "+faststart",
        output_path
    ]

    try:
        print("Starting conversion...")
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("\nConversion failed. Check FFmpeg output above for details.")
        sys.exit(1)
    finally:
        cleanup_files = [filelist_path, metadata_path]
        if MERGE:
            cleanup_files.append(final_mp3)
            
        for f in cleanup_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except Exception as e:
                print(f"Error cleaning up file {f}: {e}")

    print(f"\nSuccessfully created audiobook: {output_path}")

if __name__ == "__main__":
    main()