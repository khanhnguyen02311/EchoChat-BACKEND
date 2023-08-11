from typing import Any

from . import FunctionException, security
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from components.storages.postgres_models import Account, AccountInfo


def handle_create_account_info(session: Session) -> tuple[Any, Any]:
    """Create new AccountInfo item. \n
    Return: (error, AccountInfo)"""

    try:
        new_account_info = AccountInfo(name="temporary")
        session.add(new_account_info)
        session.flush()
        return None, new_account_info

    except Exception as e:
        return FunctionException(handle_create_account_info.__name__, e), None


def handle_create_account(session: Session, new_account: Account) -> tuple[Any, Account | None]:
    """Create new Account item from input infos.\n
    Return tuple: (error, Account)"""

    try:
        # check existed accounts
        acc_query = select(Account).where(
            or_(Account.username == new_account.username, Account.email == new_account.email))
        if len(session.scalars(acc_query).all()) >= 1:
            return "Account already existed", None
        new_account.password = security.handle_create_hash(new_account.password)
        session.add(new_account)
        session.flush()
        return None, new_account

    except Exception as e:
        return FunctionException(handle_create_account.__name__, e), None


def handle_validate_account(session: Session, username_or_email: str, password: str) -> tuple[Any, Account | None]:
    """Validate the signin infos.\n
    Return tuple: (error, Account)"""
    try:
        acc_query = select(Account).where(
            or_(Account.username == username_or_email, Account.email == username_or_email))
        acc = session.scalar(acc_query)
        if acc is not None:
            password_hash = security.handle_create_hash(password)
            if acc.password == password_hash:
                return None, acc

    except Exception as e:
        return FunctionException(handle_validate_account.__name__, e), None
