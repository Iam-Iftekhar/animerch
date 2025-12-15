# app/products/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from sqlalchemy.sql import func

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, index=True)
    
    products = relationship("Product", back_populates="category")

class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("users.id"))  # Links to User
    category_id = Column(Integer, ForeignKey("categories.id")) # Links to Category
    
    title = Column(String(100), index=True)
    description = Column(Text)
    price = Column(Float)
    image_url = Column(String(255)) # We will store the file path here
    created_at = Column(DateTime(timezone=True), server_default=func.now()) 
    stock = Column(Integer, default=1)
    category = relationship("Category", back_populates="products")
    seller = relationship("app.auth.models.User")




#-----------------------------------------------------------------------------------
# class Category(Base):
#     __tablename__ = "categories"
#     id = Column(Integer, primary_key=True, index=True)
#     name = Column(String, unique=True, index=True)
#     description = Column(String)
#     products = relationship("Product", back_populates="category")

# class Product(Base):
#     __tablename__ = "products"

#     id = Column(Integer, primary_key=True, index=True)
#     title = Column(String, index=True)
#     description = Column(String)
#     price = Column(Float)
#     image_url = Column(String)
#     stock = Column(Integer, default=1)
    
#     # --- ADD THIS NEW COLUMN ---
#     created_at = Column(DateTime(timezone=True), server_default=func.now()) 
#     # ---------------------------

#     category_id = Column(Integer, ForeignKey("categories.id"))
#     seller_id = Column(Integer, ForeignKey("users.id"))

#     category = relationship("Category", back_populates="products")
#     seller = relationship("User", back_populates="products")