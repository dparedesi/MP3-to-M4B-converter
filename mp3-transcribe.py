# pip install openai-whisper pydub
import whisper
import sys

# Configuration
MP3_PATH = "inputs/file-3.mp3"
OUTPUT_TXT = "transcript.txt"
MODEL_SIZE = "large-v3"

def transcribe_audio(audio_path, model_size):
    """
    Loads a Whisper model and transcribes the given audio file.
    Returns the plain text transcription.
    """
    print("Loading Whisper model...")
    model = whisper.load_model(model_size)
    
    print("Transcribing audio...")
    result = model.transcribe(
        audio_path,
        verbose=True,
        no_speech_threshold=0.45,
        compression_ratio_threshold=2.4,
        fp16=False  # Disable if using CPU
    )
    return result["text"]

def main():
    try:
        # Transcribe and get the raw text
        transcript_text = transcribe_audio(MP3_PATH, MODEL_SIZE)
        
        # Save to .txt file
        with open(OUTPUT_TXT, "w", encoding="utf-8") as txt_file:
            txt_file.write(transcript_text)
        
        print(f"Transcription saved to {OUTPUT_TXT}")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
