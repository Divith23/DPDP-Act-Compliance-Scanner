from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings

client: AsyncIOMotorClient = None


async def connect():
    global client
    client = AsyncIOMotorClient(settings.MONGODB_URI)


async def disconnect():
    global client
    if client:
        client.close()


def get_db():
    return client[settings.MONGODB_DB_NAME]
