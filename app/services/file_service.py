import os
import logging
from fastapi import UploadFile, HTTPException
from pathlib import Path
import shutil
from datetime import datetime
from sqlalchemy.orm import Session
from app.database.models import File, User
from app.services.preview_service import PreviewService
from app.config import Config
import hashlib
from typing import List

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FileService:
    def __init__(self):
        self.config = Config()
        self.preview_service = PreviewService()
        self.base_path = Path('/media/karti/lite_driver')  # Direct path specification
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all necessary directories exist with proper permissions"""
        try:
            # Create main directories
            upload_dir = self.base_path / 'uploads'
            preview_dir = self.base_path / 'previews'

            upload_dir.mkdir(parents=True, exist_ok=True)
            preview_dir.mkdir(parents=True, exist_ok=True)

            # Set permissions
            os.chmod(str(upload_dir), 0o777)
            os.chmod(str(preview_dir), 0o777)

            logger.info(f"Directories created: {upload_dir}, {preview_dir}")
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            raise RuntimeError(f"Failed to create directories: {str(e)}")

    def _get_user_directory(self, user_email: str) -> Path:
        """Create and return user's directory based on email"""
        try:
            safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
            user_dir = self.base_path / 'uploads' / safe_email
            user_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(str(user_dir), 0o777)
            logger.info(f"User directory created: {user_dir}")
            return user_dir
        except Exception as e:
            logger.error(f"Error creating user directory: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to create user directory: {str(e)}")

    def _get_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(str(datetime.now().timestamp()).encode()).hexdigest()[:8]
        ext = Path(original_filename).suffix
        return f"{timestamp}_{file_hash}{ext}"

    async def save_file(self, file: UploadFile, user: dict, db: Session) -> File:
        """Save uploaded file with preview generation"""
        file_path = None
        try:
            logger.info(f"Starting file upload for user: {user.get('email')}")

            # Get user directory
            user_dir = self._get_user_directory(user['email'])
            logger.debug(f"User directory: {user_dir}")

            # Generate unique filename
            unique_filename = self._get_unique_filename(file.filename)
            file_path = user_dir / unique_filename
            logger.debug(f"File will be saved as: {file_path}")

            # Save file
            try:
                with open(file_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                os.chmod(str(file_path), 0o644)
                logger.info(f"File saved successfully: {file_path}")
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

            # Get file size
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # Convert to MB

            # Create preview
            try:
                preview_path = self.preview_service.create_preview(
                    file_path=file_path,
                    user_email=user['email']
                )
                logger.info(f"Preview created: {preview_path}")
            except Exception as e:
                logger.error(f"Error creating preview: {str(e)}")
                preview_path = None

            # Create database record
            try:
                db_file = File(
                    filename=unique_filename,
                    original_filename=file.filename,
                    file_path=str(file_path),
                    preview_path=str(preview_path) if preview_path else None,
                    file_type=self._get_file_type(file.filename),
                    file_size=file_size,
                    user_id=user['db_id']
                )

                db.add(db_file)
                db.commit()
                db.refresh(db_file)
                logger.info(f"Database record created for file: {file.filename}")

                return db_file

            except Exception as e:
                logger.error(f"Database error: {str(e)}")
                raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

        except Exception as e:
            logger.error(f"Error in save_file: {str(e)}")
            # Cleanup on error
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up file: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up file: {str(cleanup_error)}")
            raise HTTPException(status_code=500, detail=str(e))

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif']:
            return 'image'
        elif ext in ['.pdf', '.doc', '.docx', '.txt']:
            return 'document'
        elif ext in ['.mp4', '.avi', '.mov']:
            return 'video'
        elif ext in ['.mp3', '.wav']:
            return 'audio'
        return 'other'

    def get_user_files(self, user_id: int, db: Session) -> List[File]:
        """Get all files for a user"""
        return db.query(File).filter(File.user_id == user_id).all()

    def get_file(self, file_id: int, user_id: int, db: Session) -> File:
        """Get a specific file"""
        file = db.query(File).filter(
            File.id == file_id,
            File.user_id == user_id
        ).first()
        if not file:
            raise HTTPException(status_code=404, detail="File not found")
        return file

    def delete_file(self, file_id: int, user_id: int, db: Session) -> None:
        """Delete a file and its preview"""
        file = self.get_file(file_id, user_id, db)

        try:
            # Delete physical file
            if os.path.exists(file.file_path):
                os.remove(file.file_path)

            # Delete preview if exists
            if file.preview_path and os.path.exists(file.preview_path):
                os.remove(file.preview_path)

            # Delete database record
            db.delete(file)
            db.commit()
            logger.info(f"File deleted successfully: {file_id}")

        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting file: {str(e)}")