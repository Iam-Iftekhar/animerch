# app/cart/routes.py
from fastapi import APIRouter, Depends, status, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.cart import models
from app.products.models import Product
from app.auth.models import User
from app.core.security import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Helper: Get or Create Cart for User ---
def get_user_cart(db: Session, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        cart = models.Cart(user_id=user_id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

# --- 1. View Cart Page ---
@router.get("/", response_class=HTMLResponse)
async def view_cart(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.email == user_data["sub"]).first()
    cart = get_user_cart(db, user.id)
    
    # Eager load items and products to prevent database spam
    cart_items = db.query(models.CartItem).options(joinedload(models.CartItem.product))\
        .filter(models.CartItem.cart_id == cart.id).all()

    # Calculate Total
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return templates.TemplateResponse("cart.html", {
        "request": request, 
        "cart_items": cart_items, 
        "total_price": total_price,
        "user":user
    })

# --- 2. Add Item to Cart ---
@router.post("/add/{product_id}")
async def add_to_cart(product_id: int, request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user = db.query(User).filter(User.email == user_data["sub"]).first()
    
    # Fetch the product to check who owns it
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # LOGIC CHECK: Prevent self-purchase
    if product.seller_id == user.id:
        # Optionally: Redirect back with an error message
        # For now, we just stop the action
        print("DEBUG: Seller tried to buy own product")
        return RedirectResponse(url=f"/products/{product_id}", status_code=status.HTTP_303_SEE_OTHER)

    # ... rest of cart logic (get_user_cart, add item) ...
    cart = get_user_cart(db, user.id)

    existing_item = db.query(models.CartItem).filter(
        models.CartItem.cart_id == cart.id,
        models.CartItem.product_id == product_id
    ).first()

    if existing_item:
        existing_item.quantity += 1
    else:
        new_item = models.CartItem(cart_id=cart.id, product_id=product_id, quantity=1)
        db.add(new_item)
    
    db.commit()
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)

# app/cart/routes.py
@router.get("/remove/{item_id}")
async def remove_item(item_id: int, request: Request, db: Session = Depends(get_db)):
    item = db.query(models.CartItem).filter(models.CartItem.id == item_id).first()
    if item:
        db.delete(item)
        db.commit()
    
    # This redirects back to the main cart page
    return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)