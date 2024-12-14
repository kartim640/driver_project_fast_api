# app/services/preview_service.py
import os
from PIL import Image
from pathlib import Path
import logging
from typing import Optional
import asyncio
from app.config import Config

logger = logging.getLogger(__name__)


class PreviewService:
    def __init__(self):
        self.config = Config()
        self.base_path = Path(self.config.storage.base_path)
        self.preview_size = (200, 200)
        self.supported_formats = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
            'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf'],
            'video': ['.mp4', '.avi', '.mov', '.wmv'],
            'audio': ['.mp3', '.wav', '.ogg'],
            'archive': ['.zip', '.rar', '.7z']
        }
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Ensure all necessary directories exist"""
        try:
            preview_dir = self.base_path / 'previews'
            preview_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(str(preview_dir), 0o777)

            # Ensure static directories exist
            static_dir = Path('static')
            icons_dir = static_dir / 'icons'
            icons_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Preview directory created/verified: {preview_dir}")
        except Exception as e:
            logger.error(f"Error creating directories: {e}")
            raise RuntimeError(f"Failed to create directories: {str(e)}")

    def _get_file_type(self, file_path: Path) -> str:
        """Determine file type from extension"""
        ext = file_path.suffix.lower()
        for file_type, extensions in self.supported_formats.items():
            if ext in extensions:
                return file_type
        return 'file'

    async def create_preview(self, file_path: Path, user_email: str) -> Optional[Path]:
        """Create preview based on file type"""
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            file_type = self._get_file_type(file_path)
            preview_path = self._get_preview_path(file_path, user_email)

            if file_type == 'image':
                await self._create_image_preview(file_path, preview_path)
            else:
                await self._create_default_preview(file_type, preview_path)

            return preview_path

        except Exception as e:
            logger.error(f"Error creating preview: {e}")
            return None

    def _get_preview_path(self, file_path: Path, user_email: str) -> Path:
        """Generate preview path"""
        safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
        preview_dir = self.base_path / 'previews' / safe_email
        preview_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(str(preview_dir), 0o777)
        return preview_dir / f"{file_path.stem}_preview.webp"

    async def _create_image_preview(self, file_path: Path, preview_path: Path) -> None:
        """Create preview for image files"""
        try:
            def process_image():
                with Image.open(file_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'P'):
                        img = img.convert('RGB')

                    # Create thumbnail
                    img.thumbnail(self.preview_size)
                    img.save(preview_path, 'WEBP', quality=85)
                    os.chmod(str(preview_path), 0o644)

            await asyncio.get_event_loop().run_in_executor(None, process_image)
            logger.info(f"Created image preview: {preview_path}")

        except Exception as e:
            logger.error(f"Error creating image preview: {e}")
            raise

    async def _create_default_preview(self, file_type: str, preview_path: Path) -> None:
        """Create default preview based on file type"""
        try:
            # Use default icon based on file type
            icon_path = Path('static/icons') / f"{file_type}.png"

            if not icon_path.exists():
                icon_path = Path('static/icons/file.png')  # fallback to generic icon

            if icon_path.exists():
                def process_icon():
                    with Image.open(icon_path) as img:
                        img.thumbnail(self.preview_size)
                        img.save(preview_path, 'WEBP', quality=85)
                        os.chmod(str(preview_path), 0o644)

                await asyncio.get_event_loop().run_in_executor(None, process_icon)
                logger.info(f"Created default preview: {preview_path}")
            else:
                logger.warning(f"No icon found for file type: {file_type}")

        except Exception as e:
            logger.error(f"Error creating default preview: {e}")
            raise

    def delete_preview(self, preview_path: Path) -> None:
        """Delete preview file"""
        try:
            if preview_path.exists():
                os.remove(preview_path)
                logger.info(f"Preview deleted: {preview_path}")
        except Exception as e:
            logger.error(f"Error deleting preview: {e}")
            raise