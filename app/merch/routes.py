# app/merch/routes.py
from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.products.models import Product, Category 
from app.core.security import get_current_user_from_cookie
from app.auth.models import User

router = APIRouter()
templates = Jinja2Templates(directory="templates")

@router.get("/")  # This becomes /merch/
async def merch_page(request: Request, db: Session = Depends(get_db)):
    # 1. Fetch User (for navbar logic)
    user = None
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        user = db.query(User).filter(User.email == user_payload["sub"]).first()

    # 2. Fetch Merchandise Products
    # Filter by category name "Merchandise"
    merch_products = db.query(Product).join(Category).filter(Category.name == "Merchandise").all()
    
    # 3. Fetch Recent items for the Gliding Strip (Last 10 items)
    recent_items = db.query(Product).order_by(Product.created_at.desc()).limit(10).all()

    return templates.TemplateResponse("merch.html", {
        "request": request, 
        "products": merch_products,
        "recent_items": recent_items,
        "user": user
    })