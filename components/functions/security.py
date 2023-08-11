import hashlib
import os
from configurations.conf import Env

from . import FunctionException
from components.storages.postgres_models import Account


def handle_create_hash(password: str) -> str:
    password += Env.SCR_HASHSALT
    password_hash = hashlib.sha512(password.encode('UTF-8'))
    return password_hash.hexdigest()
