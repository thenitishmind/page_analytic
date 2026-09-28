"""Authentication router for login, register, and logout."""

from fastapi import APIRouter, Request, Depends, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.auth_service import register_user, authenticate_user
from app.auth.jwt_handler import get_current_user_optional

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, db: Session = Depends(get_db)):
    """Render login page. Redirect to dashboard if already authenticated."""
    user = get_current_user_optional(request, db)
    if user:
        return RedirectResponse(url="/dashboard", status_code=302)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "mode": "login",
        },
    )


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    """Render registration page."""
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": None,
            "mode": "register",
        },
    )


@router.post("/login")
async def login_submit(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process login form submission."""
    try:
        token = authenticate_user(db, email, password)
        redirect = RedirectResponse(url="/dashboard", status_code=302)
        redirect.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=86400,
            samesite="lax",
        )
        return redirect
    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": str(e),
                "mode": "login",
            },
        )


@router.post("/register")
async def register_submit(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """Process registration form submission."""
    try:
        user = register_user(db, name, email, password)
        token = authenticate_user(db, email, password)
        redirect = RedirectResponse(url="/dashboard", status_code=302)
        redirect.set_cookie(
            key="access_token",
            value=f"Bearer {token}",
            httponly=True,
            max_age=86400,
            samesite="lax",
        )
        return redirect
    except ValueError as e:
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "error": str(e),
                "mode": "register",
            },
        )


@router.get("/logout")
async def logout():
    """Log out the user by clearing the auth cookie."""
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie("access_token")
    return response
