import time

from fastapi import APIRouter
from components.functions import testtable

router = APIRouter()


@router.get("/hello")
async def hello_world():
    return "Hello world"


@router.get("/setuptest")
async def setup_test():
    err = testtable.handle_setup_testing_table()
    if err is not None:
        return str(err)
    return "Done"


@router.get("/querytest")
async def query_test():
    err = testtable.handle_test_query()
    if err is not None:
        return str(err)
    return "Done"
