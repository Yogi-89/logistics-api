from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import base as models
from app.utils import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    token_data = security.get_current_user_from_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username = token_data.get("username")
    jti = token_data.get("jti")

    user = db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Stateful session check: Ensure session is active in DB
    session = db.query(models.UserSession).filter(
        models.UserSession.jti == jti,
        models.UserSession.is_active == True
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Session has been revoked or expired"
        )
    
    # Update last_active for the session
    from datetime import datetime
    session.last_active = datetime.utcnow()
    db.commit()

    return user
