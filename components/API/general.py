import time

from fastapi import APIRouter
from components.functions import testtable

router = APIRouter()


@router.get("/hello")
async def hello_world():
    return "Hello world"


@router.get("/setuptest")
async def setup_test():
    try:
        testtable.handle_setup_testing_table()
    except Exception as e:
        return str(e)
    return "Done"


@router.get("/querytest")
async def query_test():
    try:
        testtable.test_query()
    except Exception as e:
        return str(e)
    return "Done"

# @router.get("/employees/{id}")
# async def get_employees(id: int, department: Department, gender: str = None):
#     print(id, department, gender)
#     return {"id": 1, "name": "Bob"}
#
#
# @router.post("/employees", response_model=Employee, status_code=status.HTTP_201_CREATED)
# async def create_employees(employee: Employee):
#     if employee.id in [200, 300, 400]:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Not a valid ID")
#     return employee
#
#
# @router.post("/send_email")
# async def send_email(background_tasks: BackgroundTasks,
#                      notification_payload: NotificationPayload,
#                      token: Optional[str] = Cookie(None),
#                      user_agent: Optional[str] = Header(None)):
#     print(notification_payload)
#
#     background_tasks.add_task(example_background_notification(notification_payload.email))
#
#     return {
#         "cookie_received": token,
#         "user_agent_received": user_agent,
#         "custom_message": "No message"
#     }
#
#
# # for todo app
# @router.get("/todo/get")
# async def get_todo():
#     response = await dbs.get_all_todo()
#     return response
#
#
# @router.get("/todo/get/{title}", response_model=Todo)
# async def get_todo_by_title(title: str):
#     response = await dbs.get_single_todo(title)
#     if response:
#         return response
#     else:
#         return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Todo item title '{title}' found")
#
#
# @router.post("/todo/create")
# async def create_todo(todo: Todo):
#     response = await dbs.create_todo(todo.dict())
#     if response:
#         return Todo(**response)
#     else:
#         return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Something went wrong")
#
#
# @router.post("/todo/update")
# async def edit_todo(todo: Todo):
#     response = await dbs.update_todo(todo.title, todo.description)
#     if response:
#         return response
#     else:
#         return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Todo item title '{todo.title}' found")
#
#
# @router.delete("/todo/delete/{title}")
# async def edit_todo(title: str):
#     response = await dbs.remove_todo(title)
#     if response:
#         return response
#     else:
#         return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No Todo item title '{title}' found")
