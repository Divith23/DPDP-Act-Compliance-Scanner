import os
import certifi

from pymongo import MongoClient
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)
else:
    load_dotenv()

MONGODB_URI = os.getenv("MONGODB_URI")

if not MONGODB_URI:
    raise RuntimeError("MONGODB_URI is not set in .env")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    retryWrites=True
)

# Verify MongoDB connection when this module starts
try:
    client.admin.command("ping")
    print("MongoDB Atlas connection successful!")
except Exception as e:
    raise RuntimeError(f"MongoDB Atlas connection failed: {e}")

db = client["dpdp_guard"]
collection = db["crawler_results"]


def save_website(data):
    print("Inside save_website()")

    try:
        result = collection.insert_one(data)

        print("Website data stored in MongoDB Atlas successfully!")
        print("Inserted ID:", result.inserted_id)

        return str(result.inserted_id)

    except Exception as e:
        print(f"MongoDB insert failed: {e}")
        raise