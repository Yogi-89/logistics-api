from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import base as models
from app.schemas import schemas
from app.utils import security
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/apikey", tags=["API Key Management"])

@router.post("/generate", response_model=schemas.APIKey)
def generate_key(key_data: schemas.APIKeyCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # if not current_user.is_verified:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="Akun Anda belum terverifikasi. Silakan lakukan verifikasi OTP terlebih dahulu."
    #     )
    new_key_str = security.generate_api_key()
    new_key = models.APIKey(
        key=new_key_str,
        label=key_data.label,
        user_id=current_user.id,
        request_limit=key_data.request_limit # Optional sub-limit
    )
    db.add(new_key)
    db.commit()
    db.refresh(new_key)
    return new_key

@router.put("/{key_id}/settings", response_model=schemas.APIKey)
def update_key_settings(key_id: int, settings: schemas.APIKeyUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = db.query(models.APIKey).filter(models.APIKey.id == key_id, models.APIKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found or unauthorized")
    
    if settings.label is not None:
        key.label = settings.label
    if settings.request_limit is not None:
        key.request_limit = settings.request_limit
        # If limit is increased, reset status if it was limited
        if key.status == "limited":
            key.status = "active"
    if 'ip_whitelist' in settings.model_fields_set:
        key.ip_whitelist = settings.ip_whitelist if settings.ip_whitelist else None
    if settings.is_active is not None:
        key.is_active = settings.is_active
        
    db.commit()
    db.refresh(key)
    return key

@router.get("/list", response_model=List[schemas.APIKey])
def list_keys(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.APIKey).filter(models.APIKey.user_id == current_user.id).all()

@router.delete("/revoke/{key_id}")
def revoke_key(key_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    key = db.query(models.APIKey).filter(models.APIKey.id == key_id, models.APIKey.user_id == current_user.id).first()
    if not key:
        raise HTTPException(status_code=404, detail="API Key not found or unauthorized")
    
    # Nullify references in transactions before deletion
    db.query(models.Transaction).filter(models.Transaction.api_key_id == key_id).update({models.Transaction.api_key_id: None})
    
    db.delete(key)
    db.commit()
    return {"message": "API Key revoked successfully"}
