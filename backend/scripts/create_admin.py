import argparse
import datetime
import sys
from pathlib import Path

import bcrypt

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(backend_dir))

from app.config import settings
from app.services.persistence_service import collection


def create_admin(
    email: str, password: str, name: str | None = None, avatar: str = "a1"
):
    if settings.persistence_backend != "mongodb":
        print("Error: Persistence backend must be 'mongodb' to create an admin.")
        sys.exit(1)

    admins_coll = collection("admins")
    if admins_coll is None:
        print("Error: Failed to connect to MongoDB.")
        sys.exit(1)

    if admins_coll.find_one({"email": email}):
        print(f"Admin with email {email} already exists.")
        sys.exit(1)

    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode(
        "utf-8"
    )
    avatar_num = avatar.replace("a", "").replace(".png", "")
    avatar_url = f"/avatars/admins/a{avatar_num}.png"

    admin_doc = {
        "email": email,
        "password_hash": password_hash,
        "name": name or email.split("@")[0],
        "avatar_url": avatar_url,
        "created_at": datetime.datetime.utcnow(),
        "last_login": None,
    }

    admins_coll.insert_one(admin_doc)
    print(f"Successfully created admin user: {email} (avatar: {avatar_url})")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Create an admin user for Nexora")
    parser.add_argument("email", help="Admin email address")
    parser.add_argument("password", help="Admin password")
    parser.add_argument("--name", help="Display name", default=None)
    parser.add_argument("--avatar", help="Admin avatar id a1-a5", default="a1")

    args = parser.parse_args()
    create_admin(args.email, args.password, args.name, args.avatar)
