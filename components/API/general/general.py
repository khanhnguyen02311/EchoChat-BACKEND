import time

from fastapi import APIRouter
from components.functions import testtable
from components.storages import scylla_models

router = APIRouter()


@router.get("/hello")
async def hello_world():
    return "Hello world"


@router.get("/setuptest/postgres")
async def setup_test():
    err = testtable.handle_setup_testing_table()
    if err is not None:
        return str(err)
    return "Done"


@router.get("/querytest/postgres")
async def query_test():
    err = testtable.handle_test_query()
    if err is not None:
        return str(err)
    return "Done"


@router.get("/setuptest/scylla")
async def setup_test_scylla():
    testitem = scylla_models.TestTable.create(text="Test 1", number=1024)
    return testitem
