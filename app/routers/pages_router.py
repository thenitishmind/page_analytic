"""Pages management router."""

from fastapi import APIRouter, Request, Depends, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.jwt_handler import get_current_user_from_cookie
from app.services.page_service import get_user_pages, get_page, create_page, delete_page
from app.utils.helpers import format_number

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/pages", response_class=HTMLResponse)
async def pages_list(request: Request, db: Session = Depends(get_db)):
    """List all user's pages."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    pages = get_user_pages(db, user.id)
    
    return templates.TemplateResponse(
        request=request,
        name="pages.html",
        context={
            "user": user,
            "pages": pages,
            "format_number": format_number,
        },
    )


@router.post("/pages")
async def create_page_submit(
    request: Request,
    platform: str = Form(...),
    page_name: str = Form(...),
    page_url: str = Form(""),
    db: Session = Depends(get_db),
):
    """Create a new page."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    create_page(
        db=db,
        user_id=user.id,
        platform=platform,
        page_name=page_name,
        page_url=page_url or None,
    )
    
    return RedirectResponse(url="/pages", status_code=302)


@router.post("/pages/{page_id}/delete")
async def delete_page_submit(
    page_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """Delete a page."""
    try:
        user = get_current_user_from_cookie(request, db)
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
    
    delete_page(db, page_id, user.id)
    return RedirectResponse(url="/pages", status_code=302)
