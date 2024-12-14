from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.utils.decorators import require_admin
from typing import List

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")


class AdminController:
    def __init__(self):
        self.templates = templates

    @staticmethod
    def get_all_users(db: Session) -> List[User]:
        return db.query(User).all()

    @staticmethod
    def update_user(db: Session, user_id: int, data: dict) -> User:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for key, value in data.items():
            setattr(user, key, value)

        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def delete_user(db: Session, user_id: int):
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(user)
        db.commit()


admin_controller = AdminController()


@router.get("/dashboard")
@require_admin
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    users = admin_controller.get_all_users(db)
    return templates.TemplateResponse(
        "admin/dashboard.html",
        {"request": request, "users": users}
    )


@router.post("/users/{user_id}")
@require_admin
async def update_user(user_id: int, data: dict, db: Session = Depends(get_db)):
    updated_user = admin_controller.update_user(db, user_id, data)
    return {"message": "User updated", "user": updated_user}


@router.delete("/users/{user_id}")
@require_admin
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    admin_controller.delete_user(db, user_id)
    return {"message": "User deleted"}