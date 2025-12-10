# app/main.py
from fastapi import FastAPI, Request,Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.auth import routes as auth_routes
from app.database import engine, Base
from sqlalchemy.orm import Session
from app.products import routes as product_routes
from app.products import models as product_models # Import to create tables
from app.database import engine, Base, get_db
from app.cart import routes as cart_routes
from app.cart import models as cart_models
from app.orders import routes as order_routes
from app.orders import models as order_models
from app.auth.models import User # Import User model
from app.core.security import get_current_user_from_cookie # Import security helper
from app.profile import routes as profile_routes

# Create tables (for dev only - use Alembic in prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Animerch")

# Mount Static Files (CSS, Images)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Include Routers
app.include_router(auth_routes.router, prefix="/auth", tags=["Auth"])
app.include_router(product_routes.router, prefix="/products", tags=["Products"])
app.include_router(cart_routes.router, prefix="/cart", tags=["Cart"])
app.include_router(order_routes.router, prefix="/orders", tags=["Orders"])
app.include_router(profile_routes.router, prefix="/profile", tags=["Profile"])







@app.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    products = db.query(product_models.Product).all()
    
    # Get current user to check role in template
    user = None
    user_payload = get_current_user_from_cookie(request)
    if user_payload:
        user = db.query(User).filter(User.email == user_payload["sub"]).first()

    return templates.TemplateResponse("index.html", {
        "request": request, 
        "products": products,
        "user": user # Pass user to template
    })