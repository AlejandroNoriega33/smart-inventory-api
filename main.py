from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Optional, List

# --- 1. CONFIGURACIÓN DE BASE DE DATOS (SQL) ---
# Se creará un archivo local 'inventory.db' automáticamente
SQLALCHEMY_DATABASE_URI = "sqlite:///./inventory.db"

engine = create_engine(SQLALCHEMY_DATABASE_URI, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. MODELOS DE BASE DE DATOS (Tablas SQL) ---¨P
class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)

# Crear las tablas en la BD si no existen
Base.metadata.create_all(bind=engine)

# --- 3. ESQUEMAS PYDANTIC (Validación de datos) ---
class ProductBase(BaseModel):
    name: str = Field(..., example="Laptop Gamer", min_length=3)
    description: Optional[str] = Field(None, example="16GB RAM, 512GB SSD")
    price: float = Field(..., gt=0, example=1200.50)
    stock: int = Field(..., ge=0, example=10)

class ProductCreate(ProductBase):
    pass

class ProductResponse(ProductBase):
    id: int
    class Config:
        from_attributes = True # Permite leer desde el modelo ORM

# --- 4. CONFIGURACIÓN DE LA APP ---
app = FastAPI(
    title="Smart Inventory API",
    description="API para gestión de stock desarrollada con Python y SQL.",
    version="1.0.0"
)

# Dependencia para obtener la sesión de BD en cada petición
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. ENDPOINTS (RUTAS) ---

@app.post("/products/", response_model=ProductResponse, status_code=201)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Crea un nuevo producto en el inventario."""
    db_product = ProductModel(**product.model_dump())
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@app.get("/products/", response_model=List[ProductResponse])
def read_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtiene la lista de productos con paginación."""
    return db.query(ProductModel).offset(skip).limit(limit).all()

@app.get("/products/{product_id}", response_model=ProductResponse)
def read_product(product_id: int, db: Session = Depends(get_db)):
    """Busca un producto específico por su ID."""
    product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return product

@app.put("/products/{product_id}", response_model=ProductResponse)
def update_stock(product_id: int, product_update: ProductCreate, db: Session = Depends(get_db)):
    """Actualiza la información y el stock de un producto."""
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    # Actualizamos los campos
    db_product.name = product_update.name
    db_product.description = product_update.description
    db_product.price = product_update.price
    db_product.stock = product_update.stock
    
    db.commit()
    db.refresh(db_product)
    return db_product

@app.delete("/products/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Elimina un producto de la base de datos."""
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    
    db.delete(db_product)
    db.commit()
    return {"detail": "Producto eliminado correctamente"}