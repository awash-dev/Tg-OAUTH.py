Sure! Here’s the full `README.md` in **copyable format**:

```markdown
# Telegram Authentication API

A FastAPI-based backend to manage Telegram login via phone number and code verification. It stores user sessions in PostgreSQL and allows retrieving user info, login, logout, and session management.

---

## Features

- Send Telegram login code to a phone number
- Verify code and optional 2FA password
- Store Telegram sessions securely in PostgreSQL
- Get current user info
- Logout and remove sessions
- Automatic session expiration

---

## Folder Structure

```

project/
├─ app/
│  ├─ main.py             # FastAPI app
│  ├─ db.py               # Database connection and cursor
│  ├─ config.py           # Configuration like SESSION\_EXPIRY\_DAYS
│  ├─ telegram_client.py  # Telegram client helper functions
│  └─ **init**.py
   |_ .env
   |_ requirements.txt
   |_ db/
        |_ db.sql

````

---

## Installation

1. Clone the repository:

```bash
git clone <repo-url>
cd project
````

2. Create a virtual environment:

```bash
python -m venv venv
source venv/bin/activate   # Linux / macOS
venv\Scripts\activate      # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up PostgreSQL and update `config.py` with database credentials.

---

## Environment Variables

| Variable              | Description                           |
| --------------------- | ------------------------------------- |
| `SESSION_EXPIRY_DAYS` | Number of days before session expires |
| `DB_HOST`             | PostgreSQL host                       |
| `DB_PORT`             | PostgreSQL port                       |
| `DB_NAME`             | PostgreSQL database name              |
| `DB_USER`             | PostgreSQL username                   |
| `DB_PASSWORD`         | PostgreSQL password                   |

---

## Run the App

Run from the project root:

```bash
uvicorn app.main:app --reload --port 8000
```

Open in browser or API client:

```
http://127.0.0.1:8000/docs
```

---

## API Endpoints

### 1. Send Code

`POST /send-code`
Form data:

* `phone` – Phone number in international format

Response:

```json
{
  "status": "ok",
  "message": "Code sent to Telegram"
}
```

---

### 2. Verify Code

`POST /verify-code`
Form data:

* `phone`
* `code`
* `password` (optional if 2FA is enabled)

Response:

```json
{
  "status": "ok",
  "user": {
    "id": 123456,
    "username": "example",
    "phone": "+1234567890"
  },
  "session": "<string_session>"
}
```

---

### 3. Get Current User

`POST /me`
Form data:

* `phone`

Response: User info from Telegram.

---

### 4. Logout

`POST /logout`
Form data:

* `phone`

Response:

```json
{
  "status": "ok",
  "message": "Logged out successfully"
}
```

---

## Notes

* Make sure `app` folder has `__init__.py` to support relative imports.
* Add missing Telethon error imports if needed:

```python
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PasswordHashInvalidError
```

* Run uvicorn **from the parent folder**, not inside `app/`:

```bash
uvicorn app.main:app --reload
```

---

## License

MIT License

```

---

If you want, I can also provide a **ready-to-use `requirements.txt`** that works with this project.  

Do you want me to create it?
```
# Tg-OAUTH.py
