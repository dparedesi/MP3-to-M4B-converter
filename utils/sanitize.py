from mutagen.mp4 import MP4
import os
import shutil

def sanitize_m4b_metadata(file_path, backup=False):
    try:
        # Create backup
        if backup:
            backup_path = f"{file_path}.bak"
            shutil.copyfile(file_path, backup_path)
            print(f"Backup created: {backup_path}")

        # Load file
        audio = MP4(file_path)
        
        # Tags
        tags = {'AACR', 'CDEK', 'cprt', 'CDET', 'prID', 'asin', 'AUDIBLE_ASIN'}

        tags_found = []
        for key in list(audio.tags.keys()):
            if key in tags:
                del audio.tags[key]
                tags_found.append(key)
            elif key.startswith('----'):
                tag_name = key.split(':')[-1]
                if tag_name in tags:
                    del audio.tags[key]
                    tags_found.append(tag_name)

        # Save changes
        audio.save()
        print(f"Sanitized file saved to: {file_path}")
        
        return True

    except Exception as e:
        print(f"\nError: {str(e)}")
        if backup:
            print("Restoring backup...")
            shutil.move(backup_path, file_path)
        return False

# Usage
file_path = input("Drag/drop M4B file to sanitize: ").strip('"')
sanitize_m4b_metadata(file_path)