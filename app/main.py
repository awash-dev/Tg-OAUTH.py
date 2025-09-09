from fastapi import FastAPI, Form, HTTPException
from datetime import datetime, timedelta
from .db import cursor, conn
from .config import SESSION_EXPIRY_DAYS
from .telegram_client import connect_client, get_user_info, SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError, InvalidCode, PasswordRequired, InvalidPassword

app = FastAPI()
pending_clients = {}

# ----root endpoint----
@app.get("/")
async def root():
    return {"message": "Welcome to the Telegram Auth API"}


# --- login phone number ---
@app.post("/login")
async def login(phone: str = Form(...)):
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
@app.post("/profile")
async def profile(phone: str = Form(...)):
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
