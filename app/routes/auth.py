from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from starlette.responses import RedirectResponse
from authlib.integrations.base_client import OAuthError
from typing import Callable
from app.config import Config

router = APIRouter()
templates = Jinja2Templates(directory="templates")
config = Config()


def get_oauth():
    return config.oauth


@router.get("/")
async def index(request: Request):
    user = request.session.get('user')
    if user:
        return RedirectResponse('/dashboard')
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/login")
async def login(request: Request, oauth=Depends(get_oauth)):
    user = request.session.get('user')
    if user:
        return RedirectResponse('/dashboard')
    url = request.url_for('auth')
    return await oauth.google.authorize_redirect(request, url)


@router.get('/auth')
async def auth(
        request: Request,
        db: Session = Depends(get_db),
        oauth=Depends(get_oauth)
):
    try:
        token = await oauth.google.authorize_access_token(request)
        user = token.get('userinfo')

        if user:
            # Check if user exists in database
            db_user = db.query(User).filter(User.email == user['email']).first()
            if not db_user:
                db_user = User(
                    email=user['email'],
                    name=user['name'],
                    profile_picture=user['picture'],
                    storage_limit=1024.0  # 1GB default limit
                )
                db.add(db_user)
                db.commit()
                db.refresh(db_user)

            # Update session with user info and database ID
            user_data = dict(user)
            user_data['db_id'] = db_user.id
            request.session['user'] = user_data

            return RedirectResponse('/dashboard')

    except OAuthError as e:
        return templates.TemplateResponse(
            'error.html',
            {'request': request, 'error': str(e)}
        )


@router.get('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse('/')

@router.get("/test-page")
async def test_page(request: Request):
    return templates.TemplateResponse("test.html", {"request": request})