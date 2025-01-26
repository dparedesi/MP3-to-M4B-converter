from mutagen.mp4 import MP4, MP4Tags
import os

def extract_all_m4b_tags(file_path, output_file="outputs/full_metadata.txt"):
    try:
        audio = MP4(file_path)
        all_tags = {}

        # Extract all existing tags (standard + custom)
        for key in audio.tags.keys():
            try:
                # Handle standard tags (4-character codes like '©ART')
                if not key.startswith('----'):
                    values = [str(v) for v in audio.tags[key]]
                    all_tags[key] = values
                
                # Handle custom tags (Audible/conversion metadata)
                else:
                    # Decode custom tag name (e.g., '----:com.apple.iTunes:ASIN')
                    decoded_key = key.split(':')[-1]
                    
                    # Decode values safely
                    decoded_values = []
                    for value in audio.tags[key]:
                        try:
                            decoded_values.append(value.decode('utf-8', errors='replace'))
                        except:
                            decoded_values.append(f"<binary_data: {value.hex()}>")
                    
                    all_tags[decoded_key] = decoded_values

            except Exception as e:
                all_tags[key] = [f"<error: {str(e)}>"]

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("=== COMPLETE M4B METADATA ===\n\n")
            for tag, values in all_tags.items():
                f.write(f"[{tag}]\n")
                f.write('\n'.join(values) + '\n\n')

        print(f"All tags saved to {os.path.abspath(output_file)}")
        return True

    except Exception as e:
        print(f"Error: {str(e)}")
        return False

# Usage
file_path = input("Drag/drop M4B file here: ").strip('"')
extract_all_m4b_tags(file_path)