import os

def remove_duplicate_mp3s(base_path):
    for root, dirs, files in os.walk(base_path):
        # Map from clean base filename to original file path of clean file
        clean_files = {}

        # First, find all clean mp3 files and map them
        for file in files:
            if file.lower().endswith('.mp3') and not file.lower().endswith('.mp3.mp3'):
                clean_files[file] = os.path.join(root, file)

        # Now find duplicates like *.Mp3.mp3 whose clean versions exist
        for file in files:
            file_lower = file.lower()
            if file_lower.endswith('.mp3.mp3'):
                # Build clean filename by removing the extra '.mp3'
                clean_name = file[:-4]  # remove last '.mp3'
                clean_name_lower = clean_name.lower()

                # Check if the clean file exists (case insensitive)
                for clean_file in clean_files:
                    if clean_file.lower() == clean_name_lower:
                        # We found a duplicate file to remove
                        dup_path = os.path.join(root, file)
                        print(f"Deleting duplicate file: {dup_path}")
                        try:
                            os.remove(dup_path)
                        except Exception as e:
                            print(f"Error deleting file {dup_path}: {e}")
                        break

if __name__ == "__main__":
    base_dir = r"C:\Users\KudikalaVamshi\AndroidStudioProjects\fun"
    remove_duplicate_mp3s(base_dir)
