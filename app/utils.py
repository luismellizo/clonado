import shutil
import os
import zipfile


def create_zip_archive(source_dir: str, output_filename: str) -> str:
    """Creates a zip archive of the source directory with proper structure."""
    try:
        # Remove .zip extension if present for make_archive
        base_name = output_filename.replace('.zip', '')
        
        # Create archive
        shutil.make_archive(base_name, 'zip', source_dir)
        
        return output_filename
    except Exception as e:
        print(f"Error creating zip: {e}")
        return None


def clean_download_folder(folder_path: str) -> bool:
    """Remove a download folder after ZIP is created."""
    try:
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
        return True
    except Exception as e:
        print(f"Error cleaning folder: {e}")
        return False
