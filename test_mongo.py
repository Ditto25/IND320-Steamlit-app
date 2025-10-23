# test_mongo.py
import toml
import traceback
from pathlib import Path
from urllib.parse import quote_plus
from pymongo import MongoClient
from pymongo.server_api import ServerApi

# Load local secrets.toml created for Streamlit (or use environment variables instead)
secrets_path = Path(".streamlit/secrets.toml")
print("secrets file exists:", secrets_path.exists())

secrets = {}
if secrets_path.exists():
    secrets = toml.load(secrets_path)
    print("secrets top-level keys:", list(secrets.keys()))

# Try multiple locations/formats
uri = None
# 1) If user stored a full URI under uppercase MONGO.uri
if "MONGO" in secrets and secrets["MONGO"].get("uri"):
    uri = secrets["MONGO"]["uri"]

# 2) If a lowercase [mongo] table with user/password is present, build the URI safely
if not uri and "mongo" in secrets:
    m = secrets["mongo"]
    user = m.get("user")
    pwd = m.get("password")
    host = m.get("host") or "your-cluster-host.mongodb.net"  # replace with your actual host
    default_db = m.get("db", "")
    if user and pwd:
        user_enc = quote_plus(user)
        pwd_enc = quote_plus(pwd)
        # mongodb+srv example (change host/db as needed)
        uri = f"mongodb+srv://{user_enc}:{pwd_enc}@{host}/"
        if default_db:
            uri += default_db
        uri += "?retryWrites=true&w=majority"

# If still no URI, print helpful message and exit
if not uri:
    print("No Mongo URI found in secrets. Either add [MONGO] uri = \"...\" or [mongo] user/password + host.")
    raise SystemExit(1)

print("Using URI (masked):", uri[:50] + "..." if uri else None)

# Try to connect and ping
try:
    client = MongoClient(uri, server_api=ServerApi("1"))
    client.admin.command("ping")
    print("Ping succeeded: connected to MongoDB")
except Exception:
    print("Ping failed, full exception follows:")
    traceback.print_exc()