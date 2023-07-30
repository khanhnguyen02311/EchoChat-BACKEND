from enum import Enum
from pydantic import BaseModel, Field


class Department(str, Enum):
    MATH = "math"
    ENGLISH = "english"
    CHEMISTRY = "chemistry"


class Employee(BaseModel):
    id: int = Field(description="The id that the employee uses to login")
    department: Department = Field(description="The department of that employee", default="english", max_length=8)
    age: int = Field(description="The official age of that employee")
    gender: str = Field(description="The official gender of that employee", default=None)


class NotificationPayload(BaseModel):
    email: str
    notification_type: int
