from sqlalchemy.ext.asyncio import AsyncSession

from ..config import dbPool, adbPool
from ..model import schemas
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session



from ..service.user_service import user_profile_editor

router = APIRouter(
    prefix="/user",
    tags=["Users"]
)

@router.post("/get_profile", status_code=status.HTTP_201_CREATED, response_model=schemas.UserProfile)
def get_profile(email: str, db: Session = Depends(dbPool.get_depend_db)):
    # user=user_profile_editor(user_profile,db)

    return None


@router.post("/profile_update", status_code=status.HTTP_201_CREATED, response_model=schemas.UserProfile)
def profile_update(user_profile: schemas.UserProfile, db: AsyncSession = Depends(adbPool.get_depend_async_db)):
    user=user_profile_editor(user_profile,db)

    return user
