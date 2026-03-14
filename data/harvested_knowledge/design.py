"""
Design models for visual editor
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import String, Boolean, DateTime, Text, Enum, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
import enum

from ..database.base import Base


class DesignStatus(str, enum.Enum):
    """Design status enumeration"""
    DRAFT = "draft"
    SAVED = "saved"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class DesignTemplate(Base):
    """Design template model"""
    __tablename__ = "design_templates"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Template data
    template_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Canvas state, layers, etc.
    preview_images: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)

    # Metadata
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    price: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Creator
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="templates")
    designs: Mapped[List["Design"]] = relationship("Design", back_populates="template", cascade="all, delete-orphan")


class Design(Base):
    """Design model for user creations"""
    __tablename__ = "designs"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    template_id: Mapped[Optional[int]] = mapped_column(ForeignKey("design_templates.id"), nullable=True)

    # Design data
    design_data: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # Canvas state, layers, elements
    preview_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    print_ready_file_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Product association
    product_id: Mapped[Optional[int]] = mapped_column(ForeignKey("products.id"), nullable=True)
    variant_id: Mapped[Optional[int]] = mapped_column(ForeignKey("product_variants.id"), nullable=True)

    # Status and visibility
    status: Mapped[DesignStatus] = mapped_column(Enum(DesignStatus), default=DesignStatus.DRAFT, nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    share_token: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Metadata
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Versioning
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    parent_design_id: Mapped[Optional[int]] = mapped_column(ForeignKey("designs.id"), nullable=True)  # For versioning

    # Usage stats
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="designs")
    template: Mapped[Optional["DesignTemplate"]] = relationship("DesignTemplate", back_populates="designs")
    product: Mapped[Optional["Product"]] = relationship("Product")
    variant: Mapped[Optional["ProductVariant"]] = relationship("ProductVariant")
    versions: Mapped[List["Design"]] = relationship("Design", remote_side=[parent_design_id], back_populates="parent_design")

    @property
    def is_template(self) -> bool:
        """Check if design is based on a template"""
        return self.template_id is not None

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.last_used_at = func.now()


class DesignElement(Base):
    """Design element model for individual elements in a design"""
    __tablename__ = "design_elements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id"), nullable=False)

    # Element properties
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # text, image, shape, etc.
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Position and size
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    rotation: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)

    # Styling
    properties: Mapped[Dict[str, Any]] = mapped_column(JSON, nullable=False)  # color, font, opacity, etc.

    # Layering
    z_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    locked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    design: Mapped["Design"] = relationship("Design", back_populates="elements")


class DesignAsset(Base):
    """Design asset model for uploaded images and files"""
    __tablename__ = "design_assets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    design_id: Mapped[int] = mapped_column(ForeignKey("designs.id"), nullable=False)

    # Asset info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    thumbnail_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # File metadata
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)  # in bytes
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dpi: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Processing status
    processing_status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    design: Mapped["Design"] = relationship("Design", back_populates="assets")
