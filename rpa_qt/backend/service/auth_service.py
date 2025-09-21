import random
from email.message import EmailMessage
from logging import setLoggerClass

from aiosmtplib import send
from passlib.context import CryptContext
# from .service import check_user_in_redis, write_to_redis, read_from_redis, card_status_update, list_card

from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from websockets.cli import send_outgoing_messages

from ..config import settings, adbPool

from ..model import schemas, models
from ..model.models import User
from ..model.schemas import UserSignin

oauth2_schema = OAuth2PasswordBearer(tokenUrl="token") #驗證header=Authorization: Bearer xxxxx

SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto") # passward hash


def generate_verification_code():
    return f"{random.randint(100000, 999999)}"

# password
def password_hash(password: str):
    return pwd_context.hash(password)


async def signin_verify(signin_form:UserSignin, db: AsyncSession):
    email=signin_form.email
    plain_password=signin_form.password
    verification_code=signin_form.verification_code

    q = await db.execute(select(User).where(User.email == email))
    user = q.scalars().first()
    # user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="找不到用戶")

    if pwd_context.verify(plain_password, user.password):
        if user.password== "PASSIVE":
            user.status= "ACTIVE"

    if user.verification_code != verification_code:
        raise HTTPException(status_code=400, detail="Invalid verification_code")

    user.verified = True
    await db.commit()
    await db.refresh(user)
    return user



    # if not check_user_in_redis(email):
    #     return None
    # data = read_from_redis(email)
    # if pwd_context.verify(plain_password, data["hashed_password"]):
    #     if data["status"] == "PASSIVE":
    #         data["status"] = "ACTIVE"
    #         write_to_redis(email, data)
    #
    #     return data["id"]
    # return False



def create_jwt_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def verify_jwt_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        # check expire
        expire = payload.get("exp")
        now_utc_timestamp=datetime.utcnow().replace(tzinfo=timezone.utc).timestamp() #注意：是用格林威治時間，換算成timestamp
        print(now_utc_timestamp)
        if expire is None:
            raise credentials_exception
        if now_utc_timestamp > expire:
            raise credentials_exception

        return payload
    except JWTError:
        raise credentials_exception
    except Exception as e:
        print(f"e={e}")
        raise credentials_exception

def verify_token(token: str = Depends(oauth2_schema)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload=verify_jwt_token(token,credentials_exception)
    return payload



# def verify_jwt_token(token: str, credentials_exception):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         id: str = payload.get("user_id")
#
#         if id is None:
#             raise credentials_exception
#
#         token_data = schemas.TokenData(id=str(id))
#
#     except JWTError:
#         raise credentials_exception
#
#     return token_data


async def get_current_user(token: str = Depends(oauth2_schema), db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    paylaod = verify_jwt_token(token, credentials_exception)

    q=await db.execute(select(models.User).where(models.User.id == paylaod.get("id")))
    user=q.scalars().first()
    # user = db.query(models.User).filter(models.User.id == token.id).first()

    return user

async def send_verification_email(to_email: str, token: str):

    verify_url = f"{settings.base_url}/verify-email?token={token}"
    await send_email(subject="請驗證您的信箱", body=f"請點擊以下連結驗證：{verify_url}", to_email=to_email)



async def send_verification_code_email(to_email: str, code: str):
    await send_email(subject="Your verification code", body=f"Your verification code is: {code}", to_email=to_email)

async def send_email(subject: str, body: str, to_email: str):
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.sender_email
    msg["To"] = to_email
    msg.set_content(body)

    try:
        await send(
            msg,
            hostname=settings.smtp_server,
            port=settings.smtp_port,
            username=settings.mail_user,
            password=settings.mail_password,
            start_tls=False,
        )
    except Exception as ex:
        print(f"error:{ex}")