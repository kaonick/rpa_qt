from fastapi import APIRouter, Depends, status, HTTPException, Response, Query
from sqlalchemy.orm import Session
from fastapi.security.oauth2 import OAuth2PasswordRequestForm

from ..model import schemas, models
from ..model.models import User
from ..model.schemas import UserCreate, UserSignin
from ..service import user_create
from ..service.auth_service import create_jwt_token, send_verification_email, verify_jwt_token, \
    generate_verification_code, send_verification_code_email, signin_verify, verify_token
from ..service.user_service import send_email

router = APIRouter(
    prefix="/secure",
    dependencies=[Depends(verify_token)]  # 整組路由都會驗證
)


