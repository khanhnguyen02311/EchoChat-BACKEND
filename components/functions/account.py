from typing import Any
from . import FunctionException, security
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from components.storages.postgres_models import Account, AccountInfo


def handle_create_account_info(session: Session) -> tuple[Any, AccountInfo | None]:
    """Create new AccountInfo item. \n
    Return: (error, AccountInfo_item)"""

    try:
        new_account_info = AccountInfo(name="TemporaryName")
        session.add(new_account_info)
        session.flush()
        return None, new_account_info

    except Exception as e:
        session.rollback()
        raise FunctionException(handle_create_account_info.__name__, e)


def handle_create_account(session: Session, new_account: Account) -> tuple[Any, Account | None]:
    """Create new Account item from input infos.\n
    Return tuple: (error, Account_item)"""

    try:
        # check existed accounts
        acc_query = select(Account).where(
            or_(Account.username == new_account.username, Account.email == new_account.email))
        if len(session.scalars(acc_query).all()) >= 1:
            return "Account already existed", None

        # add new account info with temp name
        error, new_account_info = handle_create_account_info(session)
        if error is not None:
            return error, None
        new_account.password = security.handle_create_hash(new_account.password)
        new_account.id_AccountInfo = new_account_info.id
        session.add(new_account)
        session.flush()
        return None, new_account

    except Exception as e:
        session.rollback()
        raise FunctionException(handle_create_account.__name__, e)


def handle_authenticate_account(session: Session, username_or_email: str, password: str) -> tuple[Any, Account | None]:
    """Authenticate the signin infos. Return the account infos if validated.\n
    Return tuple: (error, Account_item)"""
    try:
        acc_query = select(Account).where(
            or_(Account.username == username_or_email, Account.email == username_or_email))
        acc = session.scalar(acc_query)
        if not acc:
            return "Account not found", None
        if not security.handle_verify_password(password, acc.password):
            return "Incorrect username or password", None
        return None, acc

    except Exception as e:
        raise FunctionException(handle_authenticate_account.__name__, e)
