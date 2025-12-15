# app/admin/routes.py
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.products.models import Product, Category
from app.auth.models import User
from app.core.security import get_current_user_from_cookie
from app.utils import save_upload_file 

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- DEPENDENCY: VERIFY ADMIN/SELLER ---
def get_current_seller(request: Request, db: Session = Depends(get_db)):
    user_payload = get_current_user_from_cookie(request)
    if not user_payload:
        return None
    user = db.query(User).filter(User.email == user_payload["sub"]).first()
    # Allow if user is admin or seller
    if user and user.role in ["admin", "seller"]:
        return user
    return None

# --- ROUTE 1: DASHBOARD ---
@router.get("/")
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_current_seller(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    # Fetch products uploaded by THIS seller
    my_products = db.query(Product).filter(Product.seller_id == user.id).order_by(Product.created_at.desc()).all()
    
    return templates.TemplateResponse("admin/dashboard.html", {
        "request": request,
        "user": user,  # Fixes "Login" button issue
        "products": my_products
    })

# --- ROUTE 2: SHOW ADD PRODUCT FORM ---
@router.get("/add")
async def show_add_product_form(request: Request, db: Session = Depends(get_db)):
    user = get_current_seller(request, db)
    if not user:
        return RedirectResponse(url="/auth/login", status_code=302)

    categories = db.query(Category).all()
    
    return templates.TemplateResponse("admin/add_product.html", {
        "request": request,
        "categories": categories,
        "user": user   # Fixes "Login" button issue
    })

# --- ROUTE 3: PROCESS THE FORM SUBMISSION ---
@router.post("/add")
async def create_product(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    price: float = Form(...),
    stock: int = Form(...),
    category_id: int = Form(...),
    # REMOVED image_url: str = Form(...) 
    image_file: UploadFile = File(...), # We only accept the file now
    db: Session = Depends(get_db)
):
    user = get_current_seller(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # 1. Save the file and generate the URL string
    image_url = await save_upload_file(image_file)

    # 2. Create the new product using that generated URL
    new_product = Product(
        title=title,
        description=description,
        price=price,
        image_url=image_url, # Using the variable from step 1
        stock=stock,
        category_id=category_id,
        seller_id=user.id
    )

    db.add(new_product)
    db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)

# --- ROUTE 4: DELETE PRODUCT ---
@router.post("/delete/{product_id}")
async def delete_product(product_id: int, request: Request, db: Session = Depends(get_db)):
    user = get_current_seller(request, db)
    if not user:
        raise HTTPException(status_code=401, detail="Unauthorized")

    product = db.query(Product).filter(Product.id == product_id, Product.seller_id == user.id).first()
    if product:
        db.delete(product)
        db.commit()
    
    return RedirectResponse(url="/admin", status_code=303)