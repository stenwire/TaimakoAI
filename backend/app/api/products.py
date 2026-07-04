from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
import csv
import io
from app.db.session import get_db
from app.auth.router import get_current_user
from app.models.user import User
from app.models.business import Business
from app.models.product import Product
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.core.response_wrapper import success_response

router = APIRouter(prefix="/products", tags=["products"])

def get_business(db: Session, user_id: str):
    business = db.query(Business).filter(Business.user_id == user_id).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found. Please create a business profile first."
        )
    return business

@router.post("/", response_model=None)
async def create_product(
    product_in: ProductCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    
    product = Product(
        **product_in.model_dump(),
        business_id=business.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response(
        message="Product created successfully",
        data=ProductResponse.from_orm(product)
    )

@router.get("/", response_model=None)
async def list_products(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    products = db.query(Product).filter(Product.business_id == business.id).all()
    return success_response(
        data=[ProductResponse.from_orm(p) for p in products]
    )

@router.get("/{product_id}", response_model=None)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == business.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return success_response(data=ProductResponse.from_orm(product))

@router.put("/{product_id}", response_model=None)
async def update_product(
    product_id: str,
    product_in: ProductUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == business.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.add(product)
    db.commit()
    db.refresh(product)
    return success_response(
        message="Product updated successfully",
        data=ProductResponse.from_orm(product)
    )

@router.delete("/{product_id}", response_model=None)
async def delete_product(
    product_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    product = db.query(Product).filter(
        Product.id == product_id,
        Product.business_id == business.id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product)
    db.commit()
    return success_response(message="Product deleted successfully")

@router.post("/bulk", response_model=None)
async def bulk_upload_products(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    business = get_business(db, current_user.id)
    
    try:
        content = await file.read()
        decoded = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        imported = 0
        updated = 0
        errors = []
        
        for row in reader:
            try:
                sku = row.get('sku')
                if not sku:
                    errors.append(f"Missing SKU for product: {row.get('name', 'Unknown')}")
                    continue
                
                # Check if product exists
                product = db.query(Product).filter(
                    Product.business_id == business.id,
                    Product.sku == sku
                ).first()
                
                price_str = row.get('price', '0').replace(',', '')
                price = float(price_str) if price_str else 0.0
                stock = int(row.get('stock_quantity', 0))
                is_active = row.get('is_active', 'true').lower() == 'true'
                
                if product:
                    product.name = row.get('name', product.name)
                    product.description = row.get('description', product.description)
                    product.price = price
                    product.stock_quantity = stock
                    product.category = row.get('category', product.category)
                    product.is_active = is_active
                    updated += 1
                else:
                    product = Product(
                        business_id=business.id,
                        name=row.get('name', 'Unnamed Product'),
                        description=row.get('description', ''),
                        price=price,
                        sku=sku,
                        stock_quantity=stock,
                        category=row.get('category', ''),
                        is_active=is_active
                    )
                    db.add(product)
                    imported += 1
            except Exception as e:
                errors.append(f"Error processing row with SKU {row.get('sku')}: {str(e)}")
        
        db.commit()
        return success_response(
            message=f"Bulk upload complete. Imported: {imported}, Updated: {updated}",
            data={
                "imported": imported,
                "updated": updated,
                "errors": errors
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process CSV file: {str(e)}")
