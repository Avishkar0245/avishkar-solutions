
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

mongo_uri = os.getenv("MONGO_URI")

try:
    client = MongoClient(
        mongo_uri,
        serverSelectionTimeoutMS=10000
    )

    client.admin.command("ping")

    print("MongoDB Atlas Connected Successfully!")

    db = client["avishkar_solutions"]

    print("Database Name:", db.name)

except Exception as e:
    print("Connection Failed:", e)

finally:
    if "client" in globals():
        client.close()
