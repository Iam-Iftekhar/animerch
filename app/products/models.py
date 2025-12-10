# app/products/models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base

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
    
    category = relationship("Category", back_populates="products")
    seller = relationship("app.auth.models.User")