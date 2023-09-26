from typing import Any
from sqlalchemy import select, or_, update
from sqlalchemy.orm import Session
from components.storages.postgres_models import Account, Accountinfo
from components.storages.postgres_schemas import AccountSchemaPOST, AccountinfoSchemaPUT
from components.functions import security


def handle_create_account(session: Session, input_account: AccountSchemaPOST) -> tuple[Any, Any]:
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
        return None, acc

    except Exception as e:
        return str(e), None


def handle_edit_accountinfo(session: Session, account_token: Accountinfo, accountinfo_new: AccountinfoSchemaPUT) -> Any:

    try:
        accountinfo_update = update(Accountinfo).where(Accountinfo.id == account_token.id).values(
            **accountinfo_new.model_dump()
        )
        session.execute(accountinfo_update)
        return None
    except Exception as e:
        return str(e)
