# app/services/preview_service.py
import os
from PIL import Image
from pathlib import Path
import logging
from app.config import Config

logger = logging.getLogger(__name__)


class PreviewService:
    def __init__(self):
        self.config = Config()
        self.base_path = Path('/media/karti/lite_driver')
        self.preview_base = self.base_path / 'previews'
        self.static_path = Path('static')

        # File type definitions
        self.file_types = {
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'],
            'document': ['.doc', '.docx', '.txt', '.rtf', '.odt'],
            'pdf': ['.pdf'],
            'spreadsheet': ['.xls', '.xlsx', '.csv'],
            'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.mkv'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.flac'],
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz'],
            'code': ['.py', '.js', '.html', '.css', '.java', '.php']
        }

        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure all necessary directories exist"""
        try:
            # Create preview directory
            self.preview_base.mkdir(parents=True, exist_ok=True)
            os.chmod(str(self.preview_base), 0o777)

            # Create static/previews directory for public access
            preview_static = self.static_path / 'previews'
            preview_static.mkdir(parents=True, exist_ok=True)
            os.chmod(str(preview_static), 0o777)

            logger.info("Directories created successfully")
        except Exception as e:
            logger.error(f"Error creating directories: {str(e)}")
            raise

    def get_file_type(self, filename: str) -> str:
        """Determine file type from extension"""
        ext = Path(filename).suffix.lower()
        for file_type, extensions in self.file_types.items():
            if ext in extensions:
                return file_type
        return 'file'  # Default type

    def create_preview(self, file_path: Path, user_email: str) -> str:
        """Create preview and return public URL path"""
        try:
            file_type = self.get_file_type(str(file_path))

            if file_type == 'image':
                return self._create_image_preview(file_path, user_email)

            # Return default icon path for non-image files
            return f"/static/icons/{file_type}.png"

        except Exception as e:
            logger.error(f"Error creating preview: {str(e)}")
            return "/static/icons/file.png"

    def _create_image_preview(self, file_path: Path, user_email: str) -> str:
        """Create image thumbnail and return public URL path"""
        try:
            # Create user-specific preview directory
            safe_email = user_email.replace('@', '_at_').replace('.', '_dot_')
            preview_dir = self.static_path / 'previews' / safe_email
            preview_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(str(preview_dir), 0o777)

            # Generate preview filename
            preview_filename = f"{file_path.stem}_thumb.webp"
            preview_path = preview_dir / preview_filename
            public_path = f"/static/previews/{safe_email}/{preview_filename}"

            # Create thumbnail
            with Image.open(file_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')

                # Create thumbnail
                img.thumbnail((200, 200))  # Set thumbnail size
                img.save(preview_path, 'WEBP', quality=85)
                os.chmod(str(preview_path), 0o644)

            logger.info(f"Created preview at: {preview_path}")
            return public_path

        except Exception as e:
            logger.error(f"Error creating image preview: {str(e)}")
            return "/static/icons/image.png"