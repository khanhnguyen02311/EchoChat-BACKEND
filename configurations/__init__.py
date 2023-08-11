from dotenv import load_dotenv
from os import environ

load_dotenv(dotenv_path='.env')

if environ.get("POSTGRES_DB"):
    print("INFO: .env file loaded successfully")
else:
    print("ERROR: .env file loaded unsuccessfully")
