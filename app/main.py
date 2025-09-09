from fastapi import FastAPI, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
from app.db import cursor, conn
from app.config import SESSION_EXPIRY_DAYS
from app.telegram_client import connect_client, get_user_info
from app.telegram_client import InvalidCode, PasswordRequired, InvalidPassword
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import httpx

app = FastAPI()
pending_clients = {}

# --- CORS Middleware (allow all origins) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow requests from any origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Send code ---
@app.post("/send-code")
async def send_code(phone: str = Form(...)):
    client = await connect_client()
    try:
        await client.send_code_request(phone)
        pending_clients[phone] = client
        return {"status": "ok", "message": "Code sent to Telegram"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# --- Verify code ---
@app.post("/verify-code")
async def verify_code(phone: str = Form(...), code: str = Form(...), password: str = Form(None)):
    client = pending_clients.get(phone)
    if not client:
        raise HTTPException(status_code=400, detail="No pending login for this phone")

    try:
        await client.sign_in(phone=phone, code=code)
    except SessionPasswordNeededError:
        if not password:
            raise PasswordRequired()
        try:
            await client.sign_in(password=password)
        except PasswordHashInvalidError:
            raise InvalidPassword()
    except PhoneCodeInvalidError:
        raise InvalidCode()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Unexpected error: {str(e)}")

    string_session = client.session.save()

    # Save session in DB
    cursor.execute("""
    INSERT INTO sessions (phone, string_session, created_at)
    VALUES (%s, %s, NOW())
    ON CONFLICT (phone)
    DO UPDATE SET string_session=EXCLUDED.string_session, created_at=NOW()
    """, (phone, string_session))
    conn.commit()
    del pending_clients[phone]

    # Save user info
    me = await client.get_me()
    user_info = await get_user_info(client, me)
    cursor.execute("""
    INSERT INTO users (phone, telegram_id, username, first_name, last_name, bio, profile_photo, last_seen, created_at)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW())
    ON CONFLICT (phone) DO UPDATE SET
        telegram_id=EXCLUDED.telegram_id,
        username=EXCLUDED.username,
        first_name=EXCLUDED.first_name,
        last_name=EXCLUDED.last_name,
        bio=EXCLUDED.bio,
        profile_photo=EXCLUDED.profile_photo,
        last_seen=EXCLUDED.last_seen,
        created_at=NOW()
    """, (
        me.phone, me.id, user_info["username"], user_info["first_name"],
        user_info["last_name"], user_info["bio"], user_info["profile_photo"], user_info["last_seen"]
    ))
    conn.commit()

    return {"status": "ok", "user": {"id": me.id, "username": me.username, "phone": me.phone}, "session": string_session}

# --- Get current user ---
@app.post("/me")
async def me(phone: str = Form(...)):
    cursor.execute("SELECT string_session, created_at FROM sessions WHERE phone=%s", (phone,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=400, detail="User not logged in")

    string_session, created_at = row
    now = datetime.utcnow()
    if now - created_at.replace(tzinfo=None) > timedelta(days=SESSION_EXPIRY_DAYS):
        # Delete expired session & user
        cursor.execute("DELETE FROM sessions WHERE phone=%s", (phone,))
        cursor.execute("DELETE FROM users WHERE phone=%s", (phone,))
        conn.commit()
        raise HTTPException(status_code=400, detail="Session expired, please login again")

    client = await connect_client(string_session)
    me_obj = await client.get_me()
    user_info = await get_user_info(client, me_obj)
    return user_info

# --- Logout ---
@app.post("/logout")
async def logout(phone: str = Form(...)):
    cursor.execute("DELETE FROM sessions WHERE phone=%s", (phone,))
    cursor.execute("DELETE FROM users WHERE phone=%s", (phone,))
    conn.commit()
    return {"status": "ok", "message": "Logged out successfully"}

# --- APScheduler Task: example task every 14 minutes ---
scheduler = AsyncIOScheduler()

async def scheduled_task():
    cursor.execute("SELECT phone FROM sessions")
    phones = cursor.fetchall()
    for (phone,) in phones:
        try:
            async with httpx.AsyncClient() as client:
                await client.post("https://tg-oauth-v3.onrender.com/me", data={"phone": phone})
            print(f"Checked session for {phone}")
        except Exception as e:
            print(f"Error checking {phone}: {e}")

scheduler.add_job(scheduled_task, "interval", minutes=14)
scheduler.start()
