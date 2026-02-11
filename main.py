from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import RedirectResponse  # < ESTO ARREGLA TU PROBLEMA DEL 404
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

# CONFIGURACIÓN DE BASE DE DATOS 
SQLALCHEMY_DATABASE_URL = "sqlite:///./inventory.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# MODELO SQ
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, default="Sin descripción")
    price = Column(Float)
    quantity = Column(Integer)

Base.metadata.create_all(bind=engine)

#  ESQUEMAS PYDANTIC
class ProductBase(BaseModel):
    name: str
    description: str | None = None
    price: float
    quantity: int

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        orm_mode = True

# INICIALIZAR APP 
app = FastAPI(title="Smart Inventory API", version="1.0.0")

# Dependencia para obtener la DB
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

#  REDIRECCIÓN AUTOMÁTICA

@app.get("/", include_in_schema=False)
def main():
    return RedirectResponse(url="/docs")

#  ENDPOINTS

@app.post("/products/", response_model=ProductResponse, tags=["Productos"])
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    db_product = Product(**product.dict())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=list[ProductResponse], tags=["Productos"])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    products = db.query(Product).offset(skip).limit(limit).all()
    return products

@app.get("/products/{product_id}", response_model=ProductResponse, tags=["Productos"])
def read_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@app.delete("/products/{product_id}", tags=["Productos"])
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(product)
    db.commit()
    return {"mensaje": f"Producto {product.name} eliminado correctamente"}