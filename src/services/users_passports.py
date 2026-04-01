from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from src.exceptions import NotFoundError, ConflictError
from src.services.base import BaseService
from src.middleware.request_id import get_request_id
from src.models.users import UserModel
from src.schemas.users import UserCreate, UserUpdate
from src.models.passports import PassportModel
from src.schemas.passports import PassportCreate, PassportUpdate

class UsersPassportsService(BaseService):

    @classmethod
    async def create_user(cls, **kwargs) -> UserModel:
        db = kwargs.get("db")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Creating user", request_id=request_id, username=data.username, phone=data.phone)

        await cls._check_uniqueness(
            db=db,
            model=UserModel,
            fields={"username": data.username, "phone": data.phone},
            request_id=request_id,
        )

        user = UserModel.from_schema(data)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        cls._log_info("Created user", entity_id=user.id,  request_id=request_id)

        return user

    @classmethod
    async def get_user(cls, **kwargs) -> UserModel | None:
        db = kwargs.get("db")
        user_id = kwargs.get("user_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Fetching user", entity_id=user_id, request_id=request_id)

        query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(query)
        user =  result.scalar_one_or_none()

        if not user:
            cls._log_warning("User not found", entity_id=user_id, request_id=request_id)

        return user

    @classmethod
    async def update_user(cls, **kwargs) -> UserModel:
        db = kwargs.get("db")
        user_id = kwargs.get("user_id")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Updating user", entity_id=user_id, request_id=request_id)

        user = await cls.get_user(db=db, user_id=user_id, request_id=request_id)

        if not user:
            cls._log_error("User not found for update", entity_id=user_id, request_id=request_id)
            raise NotFoundError("User", str(user_id))

        await cls._check_uniqueness(
            db=db,
            model=UserModel,
            fields={"username": data.username, "phone": data.phone},
            exclude_id=user_id,
            request_id=request_id)

        user.username = data.username
        user.phone = data.phone
        await db.commit()
        await db.refresh(user)

        cls._log_info("Updated user", entity_id=user.id, request_id=request_id)
        return user

    @classmethod
    async def delete_user(cls, **kwargs) -> None:
        db = kwargs.get("db")
        user_id = kwargs.get("user_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Deleting user", entity_id=user_id, request_id=request_id)

        user = await cls.get_user(db=db, user_id=user_id, request_id=request_id)
        if not user:
            cls._log_error("User not found for deletion", entity_id=user_id, request_id=request_id)
            raise NotFoundError("User", str(user_id))

        await db.delete(user)
        await db.commit()
        cls._log_info("Deleted user", entity_id=user.id, request_id=request_id)

    @classmethod
    async def create_passport(cls, **kwargs) -> PassportModel:
        db = kwargs.get("db")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Creating passport", request_id=request_id, passport_number=data.passport_number, user_id=str(data.user_id))

        user = await cls.get_user(db=db, user_id=data.user_id, request_id=request_id)

        if not user:
            cls._log_error("User not found for passport creation", entity_id=data.user_id, request_id=request_id)
            raise NotFoundError("User", str(data.user_id))

        await cls._check_uniqueness(
            db=db,
            model=PassportModel,
            fields={"user_id": data.user_id, "passport_number": data.passport_number},
            request_id=request_id
        )
        passport = PassportModel.from_schema(data)
        db.add(passport)
        await db.commit()
        await db.refresh(passport)

        cls._log_info("Created passport", entity_id=passport.id, request_id=request_id, user_id=str(data.user_id))
        return passport

    @classmethod
    async def get_passport(cls, **kwargs) -> PassportModel | None:
        db = kwargs.get("db")
        passport_id = kwargs.get("passport_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Fetching passport", entity_id=passport_id, request_id=request_id)

        query = select(PassportModel).where(PassportModel.id == passport_id)
        result = await db.execute(query)
        passport = result.scalar_one_or_none()

        if not passport:
            cls._log_warning("Passport not found", entity_id=passport_id, request_id=request_id)

        return passport

    @classmethod
    async def update_passport(cls, **kwargs) -> PassportModel:
        db = kwargs.get("db")
        passport_id = kwargs.get("passport_id")
        data = kwargs.get("data")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Updating passport", entity_id=passport_id, request_id=request_id)

        passport = await cls.get_passport(db=db, passport_id=passport_id, request_id=request_id)
        if not passport:
            cls._log_error("Passport not found for update", entity_id=passport_id, request_id=request_id)
            raise NotFoundError("Passport", str(passport_id))

        await cls._check_uniqueness(
            db=db,
            model=PassportModel,
            fields={"passport_number": data.passport_number},
            exclude_id=passport_id,
            request_id=request_id
        )
        passport.passport_number = data.passport_number
        await db.commit()
        await db.refresh(passport)

        cls._log_info("Passport updated", entity_id=passport.id, request_id=request_id)
        return passport

    @classmethod
    async def delete_passport(cls, **kwargs) -> None:
        db = kwargs.get("db")
        passport_id = kwargs.get("passport_id")
        request_id = kwargs.get("request_id", get_request_id())

        cls._log_info("Deleting passport", entity_id=passport_id, request_id=request_id)

        passport = await cls.get_passport(db=db, passport_id=passport_id, request_id=request_id)

        if not passport:
            cls._log_error("Passport not found for deletion", entity_id=passport_id, request_id=request_id)
            raise NotFoundError("Passport", str(passport_id))

        await db.delete(passport)
        await db.commit()

        cls._log_info("Deleted passport", entity_id=passport.id, request_id=request_id)


