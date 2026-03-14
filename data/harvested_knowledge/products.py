"""
Product endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ....database import get_async_db
from ....models import Product
from ....schemas import product as product_schemas
from ....services.product import product_service

router = APIRouter()


@router.post(
    "/",
    response_model=product_schemas.ProductResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_product(
    product_in: product_schemas.ProductCreate,
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """
    Create new product.
    """
    return await product_service.create(db=db, obj_in=product_in)


@router.get("/", response_model=List[product_schemas.ProductResponse])
async def get_products(
    db: AsyncSession = Depends(get_async_db),
    skip: int = 0,
    limit: int = 100,
) -> List[Product]:
    """
    Retrieve all products.
    """
    return await product_service.get_all(db=db, skip=skip, limit=limit)


@router.get("/{product_id}", response_model=product_schemas.ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """
    Get product by ID.
    """
    product = await product_service.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.put("/{product_id}", response_model=product_schemas.ProductResponse)
async def update_product(
    product_id: int,
    product_in: product_schemas.ProductUpdate,
    db: AsyncSession = Depends(get_async_db),
) -> Product:
    """
    Update a product.
    """
    product = await product_service.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return await product_service.update(db=db, db_obj=product, obj_in=product_in)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a product.
    """
    product = await product_service.get(db=db, id=product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    await product_service.delete(db=db, id=product_id)
    return {"ok": True}