from typing import Any
from sqlalchemy import select, and_, or_, update
from sqlalchemy.orm import Session
from components.data.DAOs import redis as d_redis
from components.data.models.postgres_models import Account, Accountinfo
from components.data.schemas.postgres_schemas import AccountPOST, AccountinfoPUT
from components.functions import security


def handle_create_account(session: Session, input_account: AccountPOST) -> tuple[Any, Any]:
    """Create new Account item from input info.\n
    Return tuple: (error, Account item)"""

    try:
        # check existed accounts
        account_query = select(Account).where(
            or_(Account.username == input_account.username, Account.email == input_account.email))
        if session.scalars(account_query).first() is not None:
            return "Account already existed", None

        # add new account info and point it to new account
        new_accountinfo = Accountinfo()
        session.add(new_accountinfo)
        session.flush()
        new_account = Account(username=input_account.username,
                              email=input_account.email,
                              password=security.handle_create_hash(input_account.password),
                              accountinfo_id=new_accountinfo.id)
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
        d_redis.set_user_info(acc, "Account")
        return None, acc

    except Exception as e:
        return str(e), None


def handle_edit_accountinfo(session: Session, accountinfo_token: Accountinfo,
                            accountinfo_new: AccountinfoPUT) -> Any:
    """Check and update existing Accountinfo. Return error if needed. \n
    Return: (error)"""

    try:
        if accountinfo_new.name != accountinfo_token.name or accountinfo_new.identifier != accountinfo_token.identifier:
            existed_name_identifier_query = select(Accountinfo).where(
                and_(Accountinfo.name == accountinfo_new.name, Accountinfo.identifier == accountinfo_new.identifier))
            existed_user = session.scalar(existed_name_identifier_query)
            if existed_user is not None:
                return "User with similar name & identify number existed. You should change identify number or your name."

        accountinfo = session.scalar(select(Accountinfo).where(Accountinfo.id == accountinfo_token.id))
        accountinfo.name = accountinfo_new.name
        accountinfo.identifier = accountinfo_new.identifier
        accountinfo.description = accountinfo_new.description
        session.flush()
        d_redis.set_user_info(accountinfo, "Accountinfo")
        return None
    except Exception as e:
        return str(e)


def handle_edit_password(session: Session, account_token: Account, password_old: str, password_new: str, validate_old_password: bool = True) -> Any:
    """Check and update existing Account password. Return error if needed. \n
    Return: (error)"""

    try:
        account = session.scalar(select(Account).where(Account.accountinfo_id == account_token.id))
        if validate_old_password:
            if not security.handle_verify_password(password_old, account.password):
                raise Exception("Incorrect old password")
        account.password = security.handle_create_hash(password_new)
        session.flush()
        return None
    except Exception as e:
        return str(e)