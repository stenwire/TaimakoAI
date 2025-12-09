from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional

from app.db.session import get_db
from app.models.user import User
from app.schemas.user import Token, UserResponse, UserSignup, UserLogin
from app.auth.oauth import get_google_auth_url, exchange_code_for_token, get_google_user_info
from app.core.security import create_access_token, create_refresh_token, verify_token, get_password_hash, verify_password
from app.core.config import settings
from app.core.response_wrapper import success_response, error_response

router = APIRouter(prefix="/auth", tags=["auth"])

# --- Dependency: Get Current User ---
async def get_current_user(token: str = Depends(verify_token), db: Session = Depends(get_db)) -> User:
    # Note: verify_token dependency above is a placeholder. 
    # In FastAPI, we usually use OAuth2PasswordBearer to extract token.
    # But for simplicity here, we'll extract manually or assume middleware.
    # Let's fix this to be a proper dependency.
    pass

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# --- Endpoints ---

@router.post("/signup")
async def signup(user_in: UserSignup, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        return error_response(message="User with this email already exists", status_code=400)
    
    hashed_password = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        name=user_in.name
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return success_response(message="User created successfully", data={"id": user.id, "email": user.email})

@router.post("/login")
async def login(user_in: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if not user or not user.hashed_password or not verify_password(user_in.password, user.hashed_password):
        return error_response(message="Invalid credentials", status_code=401)
    
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        },
        message="Login successful"
    )

@router.get("/google/login")
async def login_google():
    auth_url = await get_google_auth_url()
    return success_response(data={"auth_url": auth_url})

@router.get("/google/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    # 1. Exchange code for tokens
    token_data = await exchange_code_for_token(code)
    if not token_data:
        raise HTTPException(status_code=400, detail="Failed to retrieve token from Google")
    
    google_access_token = token_data.get("access_token")
    
    # 2. Get User Info
    user_info = await get_google_user_info(google_access_token)
    if not user_info:
        raise HTTPException(status_code=400, detail="Failed to retrieve user info from Google")
    
    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    picture = user_info.get("picture")

    if not email:
        raise HTTPException(status_code=400, detail="Email not found in Google user info")

    # 3. Register or Fetch User
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user:
        # Check if email exists (maybe linked to another provider later, but for now just create)
        user = db.query(User).filter(User.email == email).first()
        if user:
            # Link google_id if email matches (optional logic, here we just update)
            user.google_id = google_id
            user.picture = picture
            user.name = name
        else:
            # Create new user
            user = User(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            db.add(user)
    else:
        # Update info
        user.name = name
        user.picture = picture
    
    db.commit()
    db.refresh(user)

    # 4. Generate JWT Tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    # 5. Redirect to Frontend
    redirect_url = f"{settings.FRONTEND_REDIRECT_URI}?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(url=redirect_url)

@router.post("/refresh", response_model=Token)
async def refresh_token_endpoint(refresh_token: str):
    payload = verify_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    
    user_id = payload.get("sub")
    # In a real app, check blacklist here
    
    new_access_token = create_access_token(subject=user_id)
    # Optionally rotate refresh token
    new_refresh_token = create_refresh_token(subject=user_id)
    
    return success_response(data={
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    })

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return success_response(data=UserResponse.model_validate(current_user))

@router.post("/logout")
async def logout():
    # In a stateless JWT setup, we can't really "logout" without a blacklist.
    # For now, we just return success and client discards token.
    return success_response(message="Successfully logged out")
