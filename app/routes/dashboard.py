from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.file_service import FileService
from starlette.responses import RedirectResponse

router = APIRouter()
templates = Jinja2Templates(directory="templates")
file_service = FileService()


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = request.session.get('user')
    if not user:
        return RedirectResponse('/')

    # Get user's files from database
    files = file_service.get_user_files(user['id'], db)

    # Calculate storage usage
    storage_used = sum(file.file_size for file in files)
    storage_limit = 1024  # 1GB
    storage_percentage = (storage_used / storage_limit) * 100

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "user": user,
            "files": files,
            "storage_used": round(storage_used, 2),
            "storage_limit": storage_limit,
            "storage_percentage": min(storage_percentage, 100)
        }
    )