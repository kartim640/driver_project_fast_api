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
from typing import List, Optional
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)


class FileService:
    def __init__(self):
        self.config = Config()
        self.preview_service = PreviewService()
        self.base_path = Path(self.config.storage.base_path)
        self._ensure_directories()

    def _ensure_directories(self):
        """Create necessary directories"""
        try:
            directories = [
                self.base_path / 'uploads',
                self.base_path / 'previews'
            ]

            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
                os.chmod(str(directory), 0o777)
                logger.info(f"Directory created/verified: {directory}")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise RuntimeError(f"Failed to create directories: {str(e)}")

    def _get_user_directory(self, user_email: str) -> Path:
        """Get or create user directory"""
        try:
            safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
            user_dir = self.base_path / 'uploads' / safe_email
            user_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(str(user_dir), 0o777)
            logger.info(f"User directory created/verified: {user_dir}")
            return user_dir
        except Exception as e:
            logger.error(f"Error creating user directory: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create user directory: {str(e)}"
            )

    def _get_unique_filename(self, original_filename: str) -> str:
        """Generate unique filename"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_hash = hashlib.md5(
            str(datetime.now().timestamp()).encode()
        ).hexdigest()[:8]
        ext = Path(original_filename).suffix
        return f"{timestamp}_{file_hash}{ext}"

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        file_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
            'document': ['.pdf', '.doc', '.docx', '.txt'],
            'spreadsheet': ['.xls', '.xlsx', '.csv'],
            'video': ['.mp4', '.avi', '.mov'],
            'audio': ['.mp3', '.wav', '.ogg'],
            'archive': ['.zip', '.rar', '.7z']
        }

        for file_type, extensions in file_types.items():
            if ext in extensions:
                return file_type
        return 'other'

    async def save_file(
            self,
            file: UploadFile,
            user: dict,
            db: Session
    ) -> File:
        """Save uploaded file with preview"""
        file_path = None
        try:
            # Get user and check storage limit
            db_user = db.query(User).filter(User.id == user['db_id']).first()
            file_size = len(await file.read()) / (1024 * 1024)  # Convert to MB
            await file.seek(0)  # Reset file pointer

            if db_user.storage_used + file_size > db_user.storage_limit:
                raise HTTPException(
                    status_code=400,
                    detail="Storage limit exceeded"
                )

            # Save file
            user_dir = self._get_user_directory(user['email'])
            unique_filename = self._get_unique_filename(file.filename)
            file_path = user_dir / unique_filename

            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            os.chmod(str(file_path), 0o644)

            # Create preview
            preview_path = await self.preview_service.create_preview(
                file_path=file_path,
                user_email=user['email']
            )

            # Create database record
            db_file = File(
                filename=unique_filename,
                original_filename=file.filename,
                file_path=str(file_path),
                preview_path=str(preview_path) if preview_path else None,
                file_type=self._get_file_type(file.filename),
                file_size=file_size,
                user_id=user['db_id']
            )

            # Update user storage
            db_user.update_storage_used(file_size)

            db.add(db_file)
            db.commit()
            db.refresh(db_file)

            logger.info(f"File saved successfully: {file_path}")
            return db_file

        except Exception as e:
            # Cleanup on error
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Cleaned up file after error: {file_path}")
                except Exception as cleanup_error:
                    logger.error(f"Error cleaning up file: {cleanup_error}")

            logger.error(f"Error saving file: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_files(self, user_id: int, db: Session) -> List[File]:
        """Get all files for a user"""
        try:
            files = db.query(File).filter(File.user_id == user_id).all()
            logger.info(f"Retrieved {len(files)} files for user {user_id}")
            return files
        except Exception as e:
            logger.error(f"Error retrieving user files: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving files"
            )

    def get_file(self, file_id: int, user_id: int, db: Session) -> File:
        """Get a specific file"""
        try:
            file = db.query(File).filter(
                File.id == file_id,
                File.user_id == user_id
            ).first()

            if not file:
                raise HTTPException(status_code=404, detail="File not found")

            return file
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving file: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error retrieving file"
            )

    def delete_file(self, file_id: int, user_id: int, db: Session) -> None:
        """Delete a file and its preview"""
        try:
            file = self.get_file(file_id, user_id, db)

            # Delete physical file
            if os.path.exists(file.file_path):
                os.remove(file.file_path)

            # Delete preview if exists
            if file.preview_path and os.path.exists(file.preview_path):
                os.remove(file.preview_path)

            # Update user storage
            user = db.query(User).filter(User.id == user_id).first()
            user.update_storage_used(-file.file_size)

            # Delete database record
            db.delete(file)
            db.commit()

            logger.info(f"File deleted successfully: {file_id}")

        except Exception as e:
            logger.error(f"Error deleting file: {e}")
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting file: {str(e)}"
            )

    def serve_file(self, file: File) -> FileResponse:
        """Serve file for download"""
        try:
            if not os.path.exists(file.file_path):
                raise HTTPException(
                    status_code=404,
                    detail="File not found on server"
                )

            return FileResponse(
                path=file.file_path,
                filename=file.original_filename,
                media_type='application/octet-stream'
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error serving file: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error serving file"
            )

    def check_file_exists(self, filename: str, user_id: int, db: Session) -> bool:
        """Check if file already exists for user"""
        return db.query(File).filter(
            File.original_filename == filename,
            File.user_id == user_id
        ).first() is not None

    def get_file_stats(self, user_id: int, db: Session) -> dict:
        """Get file statistics for user"""
        try:
            files = self.get_user_files(user_id, db)
            total_size = sum(file.file_size for file in files)
            file_types = {}

            for file in files:
                file_type = file.file_type
                if file_type in file_types:
                    file_types[file_type] += 1
                else:
                    file_types[file_type] = 1

            return {
                "total_files": len(files),
                "total_size": total_size,
                "file_types": file_types
            }
        except Exception as e:
            logger.error(f"Error getting file stats: {e}")
            raise HTTPException(
                status_code=500,
                detail="Error getting file statistics"
            )