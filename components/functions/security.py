import uuid
from datetime import timedelta, datetime
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy import select
from pydantic import BaseModel, ConfigDict
from configurations.conf import Env
from components.data import PostgresSession, RedisSession
from components.data.models.postgres_models import Account, Accountinfo

pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/signin", scheme_name="JWT")


class AccountToken(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    accountinfo_id: int


def _create_token(user: Account, token_type: str) -> str:
    """Return the token based on the subject (account)"""

    now = datetime.utcnow()
    to_encode = {"iat": now, "sub": AccountToken.model_validate(user).model_dump(), "typ_token": token_type}
    if token_type == "access":
        to_encode["exp"] = now + timedelta(minutes=Env.SCR_ACCESS_TOKEN_EXPIRE_MINUTES)
    elif token_type == "refresh":
        to_encode["exp"] = now + timedelta(minutes=Env.SCR_REFRESH_TOKEN_EXPIRE_MINUTES)
        to_encode["jti"] = str(uuid.uuid4())
    else:
        to_encode["exp"] = now + timedelta(minutes=30)
    encoded_jwt = jwt.encode(to_encode, Env.SCR_JWT_SECRET_KEY, Env.SCR_JWT_ALGORITHM)
    return encoded_jwt


def _decode_token(token: str):
    """Decode the token and return the internal payload"""

    payload = jwt.decode(token, Env.SCR_JWT_SECRET_KEY, algorithms=[Env.SCR_JWT_ALGORITHM],
                         options={"verify_exp": True, "require_sub": False, "verify_sub": False})
    return payload


def handle_verify_password(plain_password, hashed_password) -> bool:
    """Verify account password \n"""

    return pwd_context.verify(plain_password, hashed_password)


def handle_create_hash(password) -> str:
    """Create hash from password string \n
    Return values: (password_hash)"""

    return pwd_context.hash(password)


def handle_create_access_token(user: Account) -> str:
    """Return the access token based on the subject (account)"""

    return _create_token(user, "access")


def handle_create_refresh_token(user: Account) -> str:
    """Return the refresh token based on the subject (account)"""

    return _create_token(user, "refresh")


def handle_get_current_user(access_token: str, query_type="Account") -> Account | Accountinfo:
    """Return the decoded user info from the input access token. Raise error if needed. \n
        Return values: (account or accountinfo)"""
    try:
        payload = _decode_token(access_token)
        if payload.get("typ_token") == "refresh":
            raise Exception("Cannot use refresh token")

        user = payload.get("sub")
        with PostgresSession.begin() as session:
            if query_type == "Account":
                user_query = select(Account).where(Account.id == user.get("id"))
            else:
                user_query = select(Accountinfo).where(Accountinfo.id == user.get("accountinfo_id"))
            user = session.scalar(user_query)
            if user is None:
                raise Exception("User not found")
            session.expunge_all()
            print(user)
            return user

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


def handle_get_current_account(access_token: Annotated[str, Depends(oauth2_scheme)]) -> Account:
    """Return the decoded user info from the Bearer access token. Raise error if needed. \n
    Return values: (account)"""

    return handle_get_current_user(access_token, "Account")


def handle_get_current_accountinfo(access_token: Annotated[str, Depends(oauth2_scheme)]) -> Accountinfo:
    """Return the decoded user info from the Bearer access token. Raise error if needed. \n
    Return values: (accountinfo)"""

    return handle_get_current_user(access_token, "Accountinfo")


def handle_renew_access_token(refresh_token: Annotated[str, Depends(oauth2_scheme)]) -> str | None:
    """Return the new access token with the provided refresh token. Raise error if needed. \n
    Return values: (access_token)"""

    try:
        payload = _decode_token(refresh_token)
        if payload.get("typ_token") == "access":
            raise Exception("Cannot use access token")

        # Check from deactivated database
        if RedisSession.get(payload.get("jti")) is not None:
            raise Exception("Token expired")

        user = payload.get("sub")
        with PostgresSession.begin() as session:
            user_query = select(Account).where(Account.id == user.get("id"))
            user = session.scalar(user_query)
            if user is None:
                raise Exception("User not found")
            return handle_create_access_token(user)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))


async def handle_deactivate_token(refresh_token: Annotated[str, Depends(oauth2_scheme)]) -> None:
    """Deactivate/blacklist the refresh token. Raise error if needed."""

    try:
        payload = _decode_token(refresh_token)
        if payload.get("typ_token") == "access":
            raise Exception("Cannot use access token")

        RedisSession.set(payload.get("jti"), "deactivate", ex=Env.SCR_REFRESH_TOKEN_EXPIRE_MINUTES * 60)

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=str(e))
