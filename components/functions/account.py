import random, string
from typing import Any
from sqlalchemy import select, or_
from sqlalchemy.orm import Session
from components.storages.postgres_models import Account, Accountinfo
from components.functions import security


def handle_create_account(session: Session, new_account: Account) -> tuple[Any, Any]:
    """Create new Account item from input info.\n
    Return tuple: (error, Account item)"""

    try:
        # check existed accounts
        account_query = select(Account).where(
            or_(Account.username == new_account.username, Account.email == new_account.email))
        if session.scalars(account_query).first() is not None:
            return "Account already existed", None
        # add new account info and point it to new account
        new_accountinfo = Accountinfo()
        session.add(new_accountinfo)
        session.flush()
        new_account.password = security.handle_create_hash(new_account.password)
        new_account.accountinfo_id = new_accountinfo.id
        session.add(new_account)
        session.flush()
        return None, new_account

    except Exception as e:
        return str(e), None


def handle_authenticate_account(session: Session, username_or_email: str, password: str) -> tuple[Any, Any]:
    """Authenticate the signin info. Return the account info if validated.\n
    Return tuple: (error, Account item)"""

    try:
        account_query = select(Account).where(
            or_(Account.username == username_or_email, Account.email == username_or_email))
        acc = session.scalar(account_query)
        if not acc:
            return "Account not found", None
        if not security.handle_verify_password(password, acc.password):
            return "Incorrect username or password", None
        return None, acc

    except Exception as e:
        return str(e), None


def handle_edit_accountinfo(session: Session, accountinfo_token: Accountinfo, accountinfo_new: Accountinfo):

    try:
        accountinfo_query = select(Accountinfo).where(
            Accountinfo.id == accountinfo_token.id
        )
        accountinfo = session.scalar(accountinfo_query)
        if not accountinfo:
            return "Account not found", None

        return True  # on progress

    except Exception as e:
        return str(e), None
