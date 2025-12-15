# app/products/schemas.py
from pydantic import BaseModel
from typing import Optional

class ProductCreate(BaseModel):
    title: str
    description: str
    price: float
    category_id: int

class ProductOut(BaseModel):
    id: int
    title: str
    price: float
    image_url: str

    class Config:
        from_attributes = True