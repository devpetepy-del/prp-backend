# app/routes.py
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from . import schemas, crud, database, cloud, models
from core import auth
from datetime import datetime, timezone
import json
from pydantic import ValidationError
from fastapi import HTTPException, Form, status
from typing import List, Optional
import asyncio
from core.scripts.analysis import start_time, calculate_time

router = APIRouter()

# --- User endpoints --- #
@router.post("/register", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_in: schemas.UserCreate, db: Session = Depends(database.get_db)):
    existing = crud.get_user_by_email(db, user_in.email)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    return await crud.create_user(db, user_in)

@router.post("/login")
async def login(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = await crud.get_user_by_email(db, user.email)
    if not db_user or not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = auth.create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@app.get("/auth/me", response_model=schemas.UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    return current_user

def parse_text_elements(text_elements: str = Form(...)) -> List[schemas.TextElement]:
    try:
        parsed = json.loads(text_elements)
        return [schemas.TextElement(**t) for t in parsed]
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid text_elements JSON: {e}")

# --- Template endpoints --- #
@router.post("/templates", response_model=schemas.TemplateCreateOut, status_code=status.HTTP_201_CREATED) # ✅
async def create_template(
    name: str = Form(...),
    description: str = Form(None),
    tag: Optional[str] = Form(None),
    text_elements: List[schemas.TextElement] = Depends(parse_text_elements),
    file: UploadFile = File(...),
    file2: UploadFile = File(...),  # second file
    current_user = Depends(auth.get_current_active_user),
    db: Session = Depends(database.get_db),
):
    upload_task = asyncio.create_task(cloud.upload_images(file, file2))
    tmpl_in = schemas.TemplateCreate(name=name, description=description, text_elements=text_elements, tag=tag)
    try:
        image_url, public_id, thumb_url, thumb_id  = await upload_task
    except HTTPException as e: raise e 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
    try:
        return await crud.create_template(db, tmpl_in, owner_id=current_user.id, image_url=image_url, 
                thumbnail_url=thumb_url, image_public_id=public_id, thumbnail_public_id=thumb_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/templates", response_model=List[schemas.TemplateOut])
async def list_templates(search: Optional[str] = None, skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return await crud.list_templates(db, skip=skip, limit=limit, search=search)

# @router.get("/templates/{template_id}", response_model=schemas.TemplateOut)
# def get_template(template_id: int, db: Session = Depends(database.get_db)):
#     tmpl = crud.get_template(db, template_id)
#     if not tmpl:
#         raise HTTPException(status_code=404, detail="Template not found")
#     return tmpl

@router.put("/templates/{template_id}", response_model=schemas.TemplateOut)
async def update_template(template_id: int, payload: dict, current_user = Depends(auth.get_current_active_user), db: Session = Depends(database.get_db)):
    tmpl = crud.get_template(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    if tmpl.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not permitted")
    return await crud.update_template(db, tmpl, payload)

@router.delete("/templates/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: int, current_user = Depends(auth.get_current_active_user), db: Session = Depends(database.get_db)):
    tmpl = crud.get_template(db, template_id)
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    if tmpl.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not permitted")
    await crud.delete_template(db, tmpl)
    return

# --- Variants --- #
@router.post("/variants", response_model=schemas.VariantOut, status_code=status.HTTP_201_CREATED) # ✅
async def create_variant(
    file: UploadFile = File(...),
    source_id: int = Form(...),
    text_elements: List[schemas.TextElement] = Depends(parse_text_elements),
    current_user = Depends(auth.get_current_active_user), 
    db: Session = Depends(database.get_db)
):
    st = start_time()
    upload_task = asyncio.create_task(cloud.upload_image(file, cloud.THUMBNAIL, cloud.THUMBNAIL_SIZE))
    variant_in = schemas.VariantCreate(text_elements=text_elements, source_id=source_id)

    try:
        thumb_url, thumb_id = await upload_task
        
    except HTTPException as e: raise e 
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {e}")
    try:
        result = await crud.create_variant(db, thumb_url, thumb_id,
            owner_id=current_user.id, variant_in=variant_in)
        print(calculate_time(st))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")

@router.get("/templates/{template_id}/variants", response_model=List[schemas.VariantOut])
async def list_variants(template_id: int, skip: int = 0, limit: int = 10, db: Session = Depends(database.get_db)):
    return await crud.list_variants_for_template(db, template_id, skip=skip, limit=limit)



# Health check
@router.get("/health") # ✅
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc)}

