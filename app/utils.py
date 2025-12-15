# app/utils.py
import shutil
import os
from fastapi import UploadFile
from uuid import uuid4

# Define where to save images
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_upload_file(upload_file: UploadFile) -> str:
    """
    Saves an uploaded file to disk and returns the URL path.
    """
    if not upload_file.filename:
        return ""
    
    # Generate a unique filename to prevent overwrites (e.g., "my-pic.jpg" -> "uuid-my-pic.jpg")
    file_extension = os.path.splitext(upload_file.filename)[1]
    unique_filename = f"{uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Write the file to disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    # Return the URL accessible by the browser
    return f"/static/uploads/{unique_filename}"