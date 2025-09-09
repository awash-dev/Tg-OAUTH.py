from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.users import GetFullUserRequest
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
from fastapi import HTTPException
from .config import API_ID, API_HASH

async def connect_client(session: str = None):
    client = TelegramClient(StringSession(session) if session else StringSession(), API_ID, API_HASH)
    await client.connect()
    return client

async def get_user_info(client, me):
    full = await client(GetFullUserRequest(me.id))

    bio = getattr(full, "about", "") or ""
    profile_photo = getattr(full, "profile_photo", None)
    last_seen = str(getattr(me, "status", None)) if getattr(me, "status", None) else None

    return {
        "id": me.id,
        "username": me.username,
        "first_name": me.first_name,
        "last_name": me.last_name,
        "phone": me.phone,
        "bio": bio,
        "profile_photo": profile_photo.to_dict() if profile_photo else None,
        "last_seen": last_seen
    }

# Exception helpers
class InvalidCode(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Invalid verification code")

class PasswordRequired(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Password required for 2FA")

class InvalidPassword(HTTPException):
    def __init__(self):
        super().__init__(status_code=400, detail="Invalid 2FA password")
