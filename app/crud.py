from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas
from core import auth


# --- USERS --- #
async def create_user(db: AsyncSession, user_in: schemas.UserCreate):
    hashed_pw = auth.hash_password(user_in.password)
    db_user = models.User(
        email=user_in.email,
        username=user_in.username,
        hashed_password=hashed_pw,
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_email(db: AsyncSession, email: str):
    result = await db.execute(select(models.User).where(models.User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    return result.scalar_one_or_none()


# --- TEMPLATES --- #
async def create_template(
    db: AsyncSession,
    template_in: schemas.TemplateCreate,
    owner_id: int,
    image_url: str,
    image_public_id: str,
    thumbnail_url: str,
    thumbnail_public_id: str,
):
    text_list = [t.model_dump() if hasattr(t, "model_dump") else dict(t) for t in template_in.text_elements]
    db_t = models.Template(
        name=template_in.name,
        description=template_in.description,
        tag=template_in.tag,
        text_elements=text_list,
        image_url=image_url,
        thumbnail_url=thumbnail_url,
        image_public_id=image_public_id,
        owner_id=owner_id,
        thumbnail_public_id=thumbnail_public_id,
    )
    db.add(db_t)
    await db.commit()
    return {
        "id": db_t.id,
        "name": template_in.name,
        "description":template_in.description,
        "owner_id": owner_id,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "text_elements": text_list,
        "tag":template_in.tag,
        "created_at": db_t.created_at
    }


async def update_template(db: AsyncSession, template: models.Template, update_data: dict):
    if "text_elements" in update_data:
        template.text_elements = update_data.pop("text_elements")
    for k, v in update_data.items():
        setattr(template, k, v)
    await db.commit()
    await db.refresh(template)
    return template


async def delete_template(db: AsyncSession, template: models.Template):
    await db.delete(template)
    await db.commit()
    return


async def list_templates(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10,
    search: str | None = None,
    tag: str | None = None,
):
    stmt = select(models.Template)
    if search:
        stmt = stmt.where(
            models.Template.name.ilike(f"%{search}%")
            | models.Template.description.ilike(f"%{search}%")
        )
    if tag:
        stmt = stmt.where(models.Template.tag.ilike(f"%{tag}%"))

    result = await db.execute(stmt.offset(skip).limit(limit))
    return result.scalars().all()


# --- VARIANTS --- #
async def create_variant(
    db: AsyncSession,
    thumb_url: str,
    thumb_id: str,
    owner_id: int,
    variant_in: schemas.VariantCreate,
):
    text_list = [t.model_dump() if hasattr(t, "model_dump") else dict(t) for t in variant_in.text_elements]
    db_v = models.Variant(
        text_elements=text_list,
        owner_id=owner_id,
        source_id=variant_in.source_id,
        thumbnail_url=thumb_url,
        thumbnail_public_id=thumb_id,
    )
    db.add(db_v)
    await db.commit()
    return {
        "id": db_v.id,
        "owner_id": owner_id,
        "source_id": variant_in.source_id,
        "thumbnail_url": thumb_url,
        "text_elements": text_list,
    }


async def list_variants_for_template(db: AsyncSession, template_id: int, skip: int = 0, limit: int = 10):
    stmt = select(models.Variant).where(models.Variant.source_id == template_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()
