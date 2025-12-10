# app/auth/routes.py
from fastapi import APIRouter, Depends, status, Request, Form, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import models, schemas
from app.core.security import get_password_hash, verify_password, create_access_token

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Render Pages ---
@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# --- API Logic ---
# app/auth/routes.py

# ... imports ...

@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: str = Form("buyer"),
    db: Session = Depends(get_db)
):
    # --- DEBUGGING START ---
    print(f"DEBUG REGISTER: Username is: {username}")
    print(f"DEBUG REGISTER: Email is: {email}")
    print(f"DEBUG REGISTER: Password length: {len(password)}")
    print(f"DEBUG REGISTER: Password content: '{password}'") 
    # --- DEBUGGING END ---

    # Check if user exists
    user = db.query(models.User).filter(models.User.email == email).first()
    if user:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})
    
    # Validation checks
    if len(password) > 72:
        return templates.TemplateResponse("register.html", {"request": request, "error": "Password too long (max 72 chars)"})
    if len(password) < 4:
         return templates.TemplateResponse("register.html", {"request": request, "error": "Password too short"})

    # Create new user
    new_user = models.User(
        username=username,
        email=email,
        # The crash happens here if password is huge
        password_hash=get_password_hash(password), 
        role=role
    )
    db.add(new_user)
    db.commit()
    
    # Redirect to Login
    return RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)


@router.post("/login")
async def login(
    request: Request,
    response: Response,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    print(f"DEBUG: Login attempt for {email}")
    print(f"DEBUG: Input Password length: {len(password)}")
    print(f"DEBUG: Input Password content: '{password}'") # View the actual text

    user = db.query(models.User).filter(models.User.email == email).first()
    
    if not user:
        print("DEBUG: User not found")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})

    print(f"DEBUG: Stored Hash length: {len(user.password_hash)}")
    
    # --- SAFETY CHECK ---
    # Bcrypt crashes if the first argument (plain password) is > 72 bytes.
    # We check this before calling verify to prevent the crash.
    if len(password) > 72:
        print("DEBUG: ERROR! Password input is too long!")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Password too long"})

    # IMPORTANT: Ensure arguments are (PLAIN, HASHED)
    is_valid = verify_password(password, user.password_hash)
    
    if not is_valid:
        print("DEBUG: Password mismatch")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    # ... rest of your code (token creation) ...
    access_token = create_access_token(data={"sub": user.email, "role": user.role.value})
    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response
@router.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response