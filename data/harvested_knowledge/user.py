"""
User service
"""

from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from ..models.user import User, UserAddress
from ..schemas.user import UserCreate, UserUpdate, UserAddressCreate, UserAddressUpdate


class UserService:
    """User service"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).options(selectinload(User.addresses)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def create(self, user_data: UserCreate) -> User:
        """Create new user"""
        from ..services.auth import AuthService

        auth_service = AuthService(self.db)

        # Hash password
        hashed_password = auth_service.hash_password(user_data.password)

        # Create user
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            password_hash=hashed_password,
            phone=user_data.phone,
            bio=user_data.bio,
            timezone=user_data.timezone,
            language=user_data.language,
            currency=user_data.currency,
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)

        return db_user

    async def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user"""
        update_data = user_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(user, field, value)

        await self.db.commit()
        await self.db.refresh(user)

        return user

    async def delete(self, user: User) -> None:
        """Delete user"""
        await self.db.delete(user)
        await self.db.commit()

    async def create_address(self, user_id: int, address_data: UserAddressCreate) -> UserAddress:
        """Create user address"""
        db_address = UserAddress(
            user_id=user_id,
            **address_data.dict()
        )

        self.db.add(db_address)
        await self.db.commit()
        await self.db.refresh(db_address)

        return db_address

    async def get_address(self, address_id: int) -> Optional[UserAddress]:
        """Get user address by ID"""
        result = await self.db.execute(
            select(UserAddress).where(UserAddress.id == address_id)
        )
        return result.scalar_one_or_none()

    async def update_address(self, address: UserAddress, address_data: UserAddressUpdate) -> UserAddress:
        """Update user address"""
        update_data = address_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            setattr(address, field, value)

        await self.db.commit()
        await self.db.refresh(address)

        return address

    async def delete_address(self, address: UserAddress) -> None:
        """Delete user address"""
        await self.db.delete(address)
        await self.db.commit()

    async def get_user_addresses(self, user_id: int) -> List[UserAddress]:
        """Get all user addresses"""
        result = await self.db.execute(
            select(UserAddress).where(UserAddress.user_id == user_id)
        )
        return result.scalars().all()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Get all users with pagination"""
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()
