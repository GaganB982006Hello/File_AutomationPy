import os
from PIL import Image

def resize_images(files, target_width):
    import tempfile
    import zipfile
    
    # Ensure target_width is an integer
    try:
        target_width = int(target_width)
    except ValueError:
        return None, "Error: Target width must be a number."

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_folder = os.path.join(temp_dir, "optimized")
            os.makedirs(output_folder, exist_ok=True)
            
            resized_count = 0
            
            for file in files:
                filename = file.filename
                if not filename:
                    continue
                    
                if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    try:
                        # Open image directly from file object
                        with Image.open(file) as img:
                             # Convert to RGB if necessary (e.g. for PNGs with transparency if saving as JPG, though we save as original)
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            
                            # Calculate new height to maintain aspect ratio
                            aspect_ratio = img.height / img.width
                            target_height = int(target_width * aspect_ratio)
                            
                            # Resize
                            resample_method = Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS
                            img = img.resize((target_width, target_height), resample_method)
                            
                            # Save optimized version
                            save_path = os.path.join(output_folder, filename)
                            img.save(save_path, optimize=True, quality=85)
                            resized_count += 1
                    except Exception as e:
                        print(f"Skipping {filename}: {e}")
                        continue
            
            if resized_count == 0:
                 return None, "No images were resized."

            # Create zip
            zip_filename = "resized_images.zip"
            zip_path = os.path.join("/tmp", zip_filename) if os.path.exists("/tmp") else os.path.join(tempfile.gettempdir(), zip_filename)
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                 for root, dirs, files_in_dir in os.walk(output_folder):
                    for file_name in files_in_dir:
                        file_path = os.path.join(root, file_name)
                        arcname = file_name
                        zipf.write(file_path, arcname)

            return zip_path, f"Successfully resized {resized_count} images."
            
    except Exception as e:
        return None, f"Error: {str(e)}"

if __name__ == "__main__":
    pass
