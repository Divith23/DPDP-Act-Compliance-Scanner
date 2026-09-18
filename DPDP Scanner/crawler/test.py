import os
import certifi

from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

print("Connecting to MongoDB Atlas...")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    tlsDisableOCSPEndpointCheck=True,
    serverSelectionTimeoutMS=10000
)

try:
    client.admin.command("ping")

    print("SUCCESS!")
    print("MongoDB Atlas connection works.")

except Exception as e:
    print("FAILED!")
    print(type(e).__name__)
    print(e)