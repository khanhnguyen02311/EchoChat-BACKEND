from fastapi import APIRouter

router = APIRouter(prefix="/group")


@router.get("/list")
def getgrouplist():
    pass
