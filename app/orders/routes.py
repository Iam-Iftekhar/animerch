# app/orders/routes.py
from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.orders import models as order_models
from app.cart import models as cart_models
from app.auth.models import User
from app.core.security import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- 1. Checkout Page (Review Order) ---
@router.get("/checkout", response_class=HTMLResponse)
async def checkout_page(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)

    user = db.query(User).filter(User.email == user_data["sub"]).first()
    
    # Get Cart
    cart = db.query(cart_models.Cart).filter(cart_models.Cart.user_id == user.id).first()
    if not cart or not cart.items:
        return RedirectResponse(url="/cart", status_code=status.HTTP_303_SEE_OTHER)
    
    # Calculate Total
    cart_items = db.query(cart_models.CartItem).options(joinedload(cart_models.CartItem.product))\
        .filter(cart_models.CartItem.cart_id == cart.id).all()
    total_price = sum(item.product.price * item.quantity for item in cart_items)

    return templates.TemplateResponse("checkout.html", {
        "request": request, 
        "cart_items": cart_items, 
        "total_price": total_price,
        "user": user
    })

# --- 2. Place Order (The Real Work) ---
@router.post("/place-order")
async def place_order(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user = db.query(User).filter(User.email == user_data["sub"]).first()
    cart = db.query(cart_models.Cart).filter(cart_models.Cart.user_id == user.id).first()
    cart_items = db.query(cart_models.CartItem).filter(cart_models.CartItem.cart_id == cart.id).all()

    if not cart_items:
        return RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)

    # A. Create Order
    total_price = sum(item.product.price * item.quantity for item in cart_items)
    new_order = order_models.Order(
        user_id=user.id,
        total_price=total_price,
        status="Pending (Cash on Delivery)"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # B. Move Items from Cart -> OrderItems
    for item in cart_items:
        order_item = order_models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            price=item.product.price
        )
        db.add(order_item)
        
        # C. Remove from Cart
        db.delete(item)
    
    db.commit()

    return RedirectResponse(url="/orders/success", status_code=status.HTTP_303_SEE_OTHER)

# --- 3. Order Success Page ---
@router.get("/success", response_class=HTMLResponse)
async def order_success(request: Request):
    return templates.TemplateResponse("order_success.html", {"request": request})

# --- 4. My Orders History ---
@router.get("/my-orders", response_class=HTMLResponse)
async def my_orders(request: Request, db: Session = Depends(get_db)):
    user_data = get_current_user_from_cookie(request)
    if not user_data:
        return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    
    user = db.query(User).filter(User.email == user_data["sub"]).first()
    
    # Fetch orders ordered by newest first
    orders = db.query(order_models.Order).filter(order_models.Order.user_id == user.id)\
        .order_by(order_models.Order.created_at.desc()).all()
        
    return templates.TemplateResponse("my_orders.html", {"request": request, "orders": orders})