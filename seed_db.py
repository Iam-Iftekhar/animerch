import sys
import os

# Ensure we can import from 'app'
sys.path.append(os.getcwd())

import requests
import random
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError, ProgrammingError, IntegrityError
from app.database import SessionLocal, engine, Base

# --- CRITICAL: Import ALL models so SQLAlchemy knows how to drop them in order ---
from app.auth.models import User
from app.products.models import Category, Product
# Adding these allows drop_all to see the foreign keys and delete children first
from app.cart import models as cart_models   
from app.orders import models as order_models 
# -------------------------------------------------------------------------------

# --- CONFIG ---
AUTO_FIX_SCHEMA = True

# --- DATA GENERATORS ---
def get_manga():
    print("📡 Fetching Manga from Jikan API...")
    try:
        res = requests.get('https://api.jikan.moe/v4/top/manga?filter=bypopularity&limit=5')
        data = res.json().get('data', [])
        return [{
            "title": i['title'],
            "description": i['synopsis'][:200] + "..." if i['synopsis'] else "No text.",
            "price": round(random.uniform(500, 1500), 2),
            "image_url": i['images']['jpg']['large_image_url'],
            "stock": random.randint(5, 50)
        } for i in data]
    except:
        return []

def get_merch():
    return [{
        "title": f"Merch Item {i}", 
        "description": "Cool anime stuff", 
        "price": 1200.0, 
        "image_url": "https://images.unsplash.com/photo-1550751827-4bd374c3f58b", 
        "stock": 10
    } for i in range(3)]

# --- MAIN SEED LOGIC ---
def seed(reset=False):
    if reset:
        print("⚠️  Resetting Tables...")
        # This will now work because we imported ALL models above
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ Tables Recreated.")

    db = SessionLocal()
    try:
        # Check for schema mismatch
        db.query(Product).first()

        print("🌱 Seeding Database...")
        
        # Create Admin
        if not db.query(User).filter_by(email="admin@animerch.com").first():
            db.add(User(username="Admin", email="admin@animerch.com", password_hash="pw", role="seller"))
            db.commit()

        # Create Categories
        cats = {}
        for name in ["Merchandise", "Manga", "Accessories"]:
            c = db.query(Category).filter_by(name=name).first()
            if not c:
                c = Category(name=name)
                db.add(c)
                db.commit()
            cats[name] = c

        # Add Products
        admin = db.query(User).filter_by(email="admin@animerch.com").first()
        
        # Add Manga
        for p in get_manga():
            if not db.query(Product).filter_by(title=p['title']).first():
                p.update({"category_id": cats["Manga"].id, "seller_id": admin.id})
                db.add(Product(**p))

        # Add Merch
        for p in get_merch():
            if not db.query(Product).filter_by(title=p['title']).first():
                p.update({"category_id": cats["Merchandise"].id, "seller_id": admin.id})
                db.add(Product(**p))

        db.commit()
        print("✅ DONE! Database seeded.")

    except (OperationalError, ProgrammingError) as e:
        if "Unknown column" in str(e) or "no such column" in str(e):
            print("⚠️  Schema Error Detected. Fixing...")
            db.close()
            seed(reset=True) # Retry with reset
        else:
            print(f"❌ Error: {e}")
            
    except IntegrityError as e:
        print("❌ Integrity Error: Foreign Key Constraint.")
        print("💡 TIP: If this persists, delete your database manually via MySQL Workbench.")
        
    finally:
        db.close()

if __name__ == "__main__":
    seed()