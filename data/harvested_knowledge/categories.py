"""
Category endpoints
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def get_categories():
    """Get all categories"""
    return {"message": "Categories endpoint - to be implemented"}


@router.get("/{category_id}")
async def get_category(category_id: int):
    """Get category by ID"""
    return {"message": f"Category {category_id} - to be implemented"}


@router.post("/")
async def create_category():
    """Create new category"""
    return {"message": "Create category - to be implemented"}


@router.put("/{category_id}")
async def update_category(category_id: int):
    """Update category"""
    return {"message": f"Update category {category_id} - to be implemented"}


@router.delete("/{category_id}")
async def delete_category(category_id: int):
    """Delete category"""
    return {"message": f"Delete category {category_id} - to be implemented"}
