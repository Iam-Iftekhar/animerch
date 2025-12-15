# app/profile/routes.py
import os
import shutil
from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from app.database import get_db
from app.auth.models import User
from app.products.models import Product
from app.orders.models import OrderItem, Order
from app.core.security import get_current_user_from_cookie
from app.utils import save_upload_file

router = APIRouter()
templates = Jinja2Templates(directory="templates")
UPLOAD_DIR = "app/static/profiles"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.get("/", response_class=HTMLResponse)
async def profile_dashboard(request: Request, db: Session = Depends(get_db)):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.email == user_payload["sub"]).first()

    # --- LOGIC BRANCHING ---
    
    if user.role == "seller":
        # 1. Get Listed Items
        products = db.query(Product).filter(Product.seller_id == user.id).all()
        
        # 2. Get Sales History (Items belonging to seller that were ordered)
        sales_query = db.query(OrderItem).join(Product).filter(Product.seller_id == user.id)
        total_sales_count = sales_query.count()
        total_revenue = db.query(func.sum(OrderItem.price * OrderItem.quantity)).join(Product).filter(Product.seller_id == user.id).scalar() or 0.0
        
        # 3. Get Top Selling Items
        # (Group by product ID, count occurrences, order by desc)
        top_items = db.query(
            Product.title, 
            func.sum(OrderItem.quantity).label('sold_count')
        ).join(OrderItem).filter(Product.seller_id == user.id)\
         .group_by(Product.id).order_by(desc('sold_count')).limit(3).all()

        return templates.TemplateResponse("profile/seller.html", {
            "request": request,
            "user": user,
            "products": products,
            "total_sales": total_sales_count,
            "revenue": total_revenue,
            "top_items": top_items
        })

    else:
        # BUYER LOGIC
        # 1. Get Buying History (Recent 5 orders)
        recent_orders = db.query(Order).filter(Order.user_id == user.id)\
            .order_by(Order.created_at.desc()).limit(5).all()

        return templates.TemplateResponse("profile/buyer.html", {
            "request": request,
            "user": user,
            "recent_orders": recent_orders
        })

# --- 2. UPDATE PROFILE ROUTE ---
@router.post("/update")
async def update_profile(
    request: Request,
    username: str = Form(...),
    avatar_file: UploadFile = File(None),  # Expect a file, default to None
    db: Session = Depends(get_db)
):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/auth/login", status_code=302)

    user = db.query(User).filter(User.email == user_payload["sub"]).first()
    
    if user:
        user.username = username
        
        # Only update avatar if a new file was actually uploaded
        if avatar_file and avatar_file.filename:
            image_url = await save_upload_file(avatar_file)
            user.avatar_url = image_url
            
        db.commit()
    
    return RedirectResponse(url="/profile", status_code=303)