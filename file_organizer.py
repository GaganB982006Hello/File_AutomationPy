import os
import shutil

def organize_files(files):
    import tempfile
    import zipfile
    
    if not files:
        return None, "No files uploaded."

    try:
        # Create a temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = os.path.join(temp_dir, "organized_files")
            os.makedirs(base_dir, exist_ok=True)

            dest_dirs = {
                "Images": [".jpg", ".jpeg", ".png", ".gif"],
                "Documents": [".pdf", ".docx", ".txt", ".xlsx"],
                "Archives": [".zip", ".rar", ".tar"]
            }

            organized_count = 0

            for file in files:
                filename = file.filename
                if not filename:
                    continue
                
                file_ext = os.path.splitext(filename)[1].lower()
                
                # Default folder
                target_folder_name = "Others"
                
                for folder, extensions in dest_dirs.items():
                    if file_ext in extensions:
                        target_folder_name = folder
                        break
                
                target_path = os.path.join(base_dir, target_folder_name)
                os.makedirs(target_path, exist_ok=True)
                
                # Save the file
                file.save(os.path.join(target_path, filename))
                organized_count += 1

            # Create a zip file of the organized directory
            # We need to save the zip to a persistent temp location (not the one that's about to be deleted)
            # Vercel allows writing to /tmp
            zip_filename = "organized_files.zip"
            zip_path = os.path.join("/tmp", zip_filename) if os.path.exists("/tmp") else os.path.join(tempfile.gettempdir(), zip_filename)

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(base_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, base_dir)
                        zipf.write(file_path, arcname)
            
            return zip_path, f"Successfully organized {organized_count} files."

    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == "__main__":
    pass
