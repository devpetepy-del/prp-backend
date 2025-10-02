from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

# USERS
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    is_staff = Column(Boolean, default=False)
    
    templates = relationship("Template", back_populates="owner")
    works = relationship("Variant", back_populates="owner")


# TEMPLATES
class Template(Base):
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=True)
    text_elements = Column(JSONB, nullable=True, default=list)
    tag = Column(String, index=True, nullable=True)
    image_url = Column(String, nullable=False)
    image_public_id = Column(String, nullable=False)
    thumbnail_url = Column(String, nullable=False)
    thumbnail_public_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    owner = relationship("User", back_populates="templates")
    variants = relationship("Variant", back_populates="source", cascade="all, delete-orphan")

# defer the public key when not needed
# VARIANTS
class Variant(Base):
    __tablename__ = "variants"

    id = Column(Integer, primary_key=True, index=True)
    text_elements = Column(JSONB, nullable=True, default=list)

    thumbnail_url = Column(String, nullable=False)
    thumbnail_public_id = Column(String, nullable=False)

    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    owner = relationship("User", back_populates="works")

    source_id = Column(Integer, ForeignKey("templates.id", ondelete="CASCADE"))
    source = relationship("Template", back_populates="variants")
    

# text_elements_json = Column(JSONB, nullable=False, default=list)
# always search with email
# comments = a later feature
# an update mage function to delete the old image and upload the new one
