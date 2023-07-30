from sqlmodel import SQLModel, create_engine
from configurations.conf import SQLModelConfig, MongoDBConfig
from motor.motor_asyncio import AsyncIOMotorClient
from components.models_mongo import Todo

# MySQL
engine = create_engine(url=SQLModelConfig.SQLMODEL_DATABASE_URL,
                       echo=SQLModelConfig.ECHO,
                       pool_size=SQLModelConfig.POOL_SIZE,
                       max_overflow=SQLModelConfig.MAX_OVERFLOW,
                       pool_pre_ping=SQLModelConfig.POOL_PRE_PING)

SQLModel.metadata.create_all(engine)

# MongoDB
client = AsyncIOMotorClient(MongoDBConfig.MONGODB_DATABASE_URL)
mongo_db = client.TodoDB
mongo_collection = mongo_db.Todo


async def get_single_todo(title: str):
    document = await mongo_collection.find_one({"title": title})
    return document


async def get_all_todo():
    todos = []
    cursor = mongo_collection.find({})
    async for document in cursor:
        todos.append(Todo(**document))
    return todos


async def create_todo(todo: dict):
    result = await mongo_collection.insert_one(todo)
    return todo


async def update_todo(title, desc):
    await mongo_collection.update_one({"title": title}, {"$set": {"description": desc}})
    document = await mongo_collection.find_one({"title": title})
    return document


async def remove_todo(title):
    await mongo_collection.delete_one({"title": title})
    return True
