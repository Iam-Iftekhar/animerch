# app/products/routes.py
import shutil
import os
from fastapi import APIRouter, Depends, File, UploadFile, Form, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.products import models
from app.auth.models import User
from app.core.security import get_current_user_from_cookie # We will add this helper next
from fastapi import HTTPException


router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Ensure image directory exists
UPLOAD_DIR = "app/static/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# --- Render "Add Product" Page ---
@router.get("/add", response_class=HTMLResponse)
async def add_product_page(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    
    # Check 1: Must be logged in
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    # Check 2: Must be a SELLER
    # We need to query the DB to get the role because the cookie might be old
    user = db.query(User).filter(User.email == user_data["sub"]).first()
    
    if user.role != "seller":
         # If a buyer tries to go here, send them home or show error
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
        
    return templates.TemplateResponse("add_product.html", {"request": request})



# --- Handle Product Creation ---
@router.post("/add")
async def create_product(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    category_name: str = Form(...),
    image: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user = db.query(User).filter(User.email == user_payload["sub"]).first()
    
    # SECURITY CHECK: Block if not a seller
    if user.role != "seller":
        raise HTTPException(status_code=403, detail="Only sellers can add products")

    # ... rest of the code (image saving, etc) remains the same ...
    # (Copy the previous logic here for saving image and product)
    file_location = f"{UPLOAD_DIR}/{image.filename}"
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    
    category = db.query(models.Category).filter(models.Category.name == category_name).first()
    if not category:
        category = models.Category(name=category_name)
        db.add(category)
        db.commit()
        db.refresh(category)

    new_product = models.Product(
        title=title,
        description=description,
        price=price,
        category_id=category.id,
        seller_id=user.id, 
        image_url=f"/static/images/{image.filename}"
    )
    db.add(new_product)
    db.commit()

    return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)



# app/products/routes.py -> product_detail function
@router.get("/{product_id}", response_class=HTMLResponse)
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    
    # Get current user
    user = None
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        user = db.query(User).filter(User.email == user_payload["sub"]).first()

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return templates.TemplateResponse("product_detail.html", {
        "request": request, 
        "product": product, 
        "user": user # Pass user
    })


