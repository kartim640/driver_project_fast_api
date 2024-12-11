import os

from fastapi import APIRouter, Request, Depends, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.services.file_service import FileService
from starlette.responses import JSONResponse, RedirectResponse, FileResponse
from typing import Dict, Any
import logging


logger = logging.getLogger(__name__)
router = APIRouter()
templates = Jinja2Templates(directory="templates")
file_service = FileService()


# Helper function to get user data
def get_user_data(request: Request) -> Dict[str, Any]:
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return user


@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_user_data(request)
        user_id = user.get('db_id')

        if not user_id:
            return RedirectResponse('/')

        # Get user's files and calculate storage
        files = file_service.get_user_files(user_id, db)
        storage_used = sum(file.file_size for file in files)
        storage_limit = 1024  # 1GB
        storage_percentage = min((storage_used / storage_limit) * 100, 100)

        return templates.TemplateResponse(
            "dashboard.html",
            {
                "request": request,
                "user": user,
                "files": files,
                "storage_used": round(storage_used, 2),
                "storage_limit": storage_limit,
                "storage_percentage": storage_percentage
            }
        )
    except HTTPException:
        return RedirectResponse('/')
    except Exception as e:
        return templates.TemplateResponse(
            "error.html",
            {"request": request, "error": str(e)}
        )


@router.post("/upload")
async def upload_file(
        request: Request,
        file: UploadFile = File(...),
        db: Session = Depends(get_db)
):
    try:
        logger.info(f"File upload request received: {file.filename}")
        user = request.session.get('user')

        if not user:
            logger.error("User not authenticated")
            raise HTTPException(status_code=401, detail="Not authenticated")

        saved_file = await file_service.save_file(file, user, db)
        logger.info(f"File uploaded successfully: {saved_file.filename}")

        return JSONResponse(
            content={
                "message": "File uploaded successfully",
                "filename": saved_file.original_filename,
                "size": saved_file.file_size
            }
        )
    except HTTPException as he:
        logger.error(f"HTTP error during upload: {str(he)}")
        raise he
    except Exception as e:
        logger.error(f"Unexpected error during upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/download/{file_id}")
async def download_file(
        request: Request,
        file_id: int,
        db: Session = Depends(get_db)
):
    try:
        user = get_user_data(request)
        file = file_service.get_file(file_id, user['db_id'], db)
        return file_service.serve_file(file)
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={"message": he.detail}
        )


@router.delete("/file/{file_id}")
async def delete_file(
        request: Request,
        file_id: int,
        db: Session = Depends(get_db)
):
    try:
        user = get_user_data(request)
        file_service.delete_file(file_id, user['db_id'], db)
        return JSONResponse(content={"message": "File deleted successfully"})
    except HTTPException as he:
        return JSONResponse(
            status_code=he.status_code,
            content={"message": he.detail}
        )


@router.get("/preview/{file_id}")
async def get_preview(file_id: int, db: Session = Depends(get_db)):
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    if file.preview_path and os.path.exists(file.preview_path):
        return FileResponse(file.preview_path)

    # Return default icon if preview doesn't exist
    return FileResponse(f"static/icons/{file.file_type}.png")