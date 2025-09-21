from fastapi import APIRouter, Depends, status, HTTPException, Response, Query, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from ..config import adbPool
from ..model import schemas, models
from ..model.models import User
from ..model.schemas import UserCreate, UserSignin
from ..service import user_create
from ..service.auth_service import create_jwt_token, send_verification_email, verify_jwt_token, \
    generate_verification_code, send_verification_code_email, signin_verify, verify_token
from ..service.user_service import send_email

router = APIRouter(
    tags=["Authentication"]
)


@router.post("/signup")
# async def signup(user: UserCreate, db: Session = Depends(get_db)):
# async def signup(user: UserCreate, db: AsyncSession = Depends(get_depend_async_db)):
async def signup(user: UserCreate, db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    new_user:User=await user_create(user,db)
    if new_user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User Not Create")
    data:dict = {"sub":new_user.email}
    token = create_jwt_token(data=data)
    await send_verification_email(new_user.email, token)
    return {"msg": "註冊成功，請至信箱點擊驗證連結"}

@router.get("/verify-email")
async def verify_email(token: str = Query(...), db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    try:
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        data:dict= verify_jwt_token(token,credentials_exception)
        email = data["sub"]
    except Exception:
        raise HTTPException(status_code=400, detail="驗證失敗或過期")

    q = await db.execute(select(User).where(User.email == email))
    user = q.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到用戶")


    # if user.verified:
    #     raise HTTPException(status_code=400, detail="驗證已過期")

    user.verified = True
    await db.commit()
    await db.refresh(user)
    return {"msg": "信箱驗證成功"}



"""
json=plaintext，不是傳json
"kaonick@fpg.com.tw"

const response = await fetch(baseUrl+'/request_verification_code', {
    method: 'POST',
    headers: {
        'Content-Type': 'text/plain',
    },
    body: credential
});

"""
@router.post("/request_verification_code")
async def request_verification_code(email: str = Body(...), db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    # user = db.query(models.User).filter(models.User.email == email).first()

    q = await db.execute(select(User).where(User.email == email))
    user = q.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="找不到用戶")
    code = generate_verification_code()
    user.verification_code = code
    await db.commit()
    await db.refresh(user)

    await send_verification_code_email(user.email, code)
    return {"message": "Verification code sent to email"}


@router.post("/signin")
async def sign_in(user_signin_form: UserSignin, db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    user:User = await signin_verify(user_signin_form, db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User could not found")

    access_token = create_jwt_token(data={"sub": user.email})
    return {"message": "Login successful","access_token": access_token, "token_type": "bearer"}



@router.get("/protected")
def protected_route(payload: dict = Depends(verify_token)):
    return {"msg": "You are authorized", "user": payload}