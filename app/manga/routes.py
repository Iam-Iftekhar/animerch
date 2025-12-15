# app/manga/routes.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.products.models import Product, Category
from app.core.security import get_current_user_from_cookie
from app.auth.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Helper to get user ---
def get_user(request: Request, db: Session):
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        return db.query(User).filter(User.email == user_payload["sub"]).first()
    return None

# 1. MANGA LANDING ROUTE
@router.get("/") # This becomes /manga/
async def manga_landing(request: Request, db: Session = Depends(get_db)):
    # Recent items specifically for the manga strip
    recent_manga = db.query(Product).join(Category).filter(Category.name == "Manga").order_by(Product.created_at.desc()).limit(10).all()
    
    return templates.TemplateResponse("manga/landing.html", {
        "request": request,
        "recent_items": recent_manga,
        "user": get_user(request, db)
    })

# 2. PHYSICAL MANGA SHOP ROUTE
@router.get("/physical") # This becomes /manga/physical
async def physical_manga(request: Request, db: Session = Depends(get_db)):
    # Fetch only Manga products for sale
    physical_manga = db.query(Product).join(Category).filter(Category.name == "Manga").all()
    
    # Recent items for strip
    recent_items = db.query(Product).order_by(Product.created_at.desc()).limit(10).all()

    return templates.TemplateResponse("manga/physical.html", {
        "request": request,
        "products": physical_manga,
        "recent_items": recent_items,
        "user": get_user(request, db)
    })

# 3. E-BOOK / API ROUTE
@router.get("/ebooks") # This becomes /manga/ebooks
async def ebooks_page(request: Request, db: Session = Depends(get_db)):
    # No DB query for products needed here, JS handles Jikan API
    return templates.TemplateResponse("manga/ebooks.html", {
        "request": request,
        "user": get_user(request, db)
    })