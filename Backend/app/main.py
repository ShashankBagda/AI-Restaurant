from datetime import datetime, timedelta
from typing import Dict
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.data import MENU_ITEMS
from app.discovery import start_discovery_responder


APP_NAME = "Smart Restaurant Server"
HTTP_PORT = 8000

app = FastAPI(title=APP_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_sessions: Dict[str, Dict[str, str]] = {}
_clients: Dict[str, Dict[str, str]] = {}
DB_PATH = "app.db"


class LoginRequest(BaseModel):
    device_id: str
    user_id: str
    password: str
    table_id: str

class RegisterRequest(BaseModel):
    user_id: str
    password: str
    role: str = "customer"

class PingRequest(BaseModel):
    device_id: str
    table_id: str


@app.on_event("startup")
def _startup():
    start_discovery_responder(HTTP_PORT)
    _init_db()


def _get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    conn = _get_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "user_id TEXT PRIMARY KEY, "
            "password TEXT NOT NULL, "
            "role TEXT NOT NULL)"
        )
        conn.commit()
        _seed_default_users(conn)
    finally:
        conn.close()


def _seed_default_users(conn):
    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if existing:
        return
    conn.execute("INSERT INTO users (user_id, password, role) VALUES (?, ?, ?)", ("demo", "demo123", "customer"))
    conn.execute("INSERT INTO users (user_id, password, role) VALUES (?, ?, ?)", ("admin", "admin123", "admin"))
    conn.commit()


@app.get("/api/health")
def health():
    return {"status": "ok", "server_time": datetime.utcnow().isoformat() + "Z"}


@app.post("/api/login")
def login(payload: LoginRequest):
    if not payload.device_id or not payload.user_id or not payload.password or not payload.table_id:
        raise HTTPException(status_code=400, detail="device_id, user_id, password, table_id required")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT user_id, password, role FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or row["password"] != payload.password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = f"{payload.device_id}-{int(datetime.utcnow().timestamp())}"
    _sessions[token] = {
        "device_id": payload.device_id,
        "user_id": payload.user_id,
        "table_id": payload.table_id,
    }
    return {"token": token, "welcome": f"Hello {payload.user_id}", "role": row["role"]}


@app.post("/api/register")
def register(payload: RegisterRequest):
    if not payload.user_id or not payload.password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    if payload.role not in ("customer", "admin"):
        raise HTTPException(status_code=400, detail="role must be customer or admin")
    conn = _get_db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="User already exists")
        conn.execute(
            "INSERT INTO users (user_id, password, role) VALUES (?, ?, ?)",
            (payload.user_id, payload.password, payload.role),
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "created", "user_id": payload.user_id, "role": payload.role}


@app.post("/api/client/ping")
def client_ping(payload: PingRequest):
    if not payload.device_id or not payload.table_id:
        raise HTTPException(status_code=400, detail="device_id, table_id required")
    _clients[payload.device_id] = {
        "device_id": payload.device_id,
        "table_id": payload.table_id,
        "last_seen": datetime.utcnow().isoformat() + "Z",
    }
    return {"status": "ok"}


@app.get("/api/clients")
def clients():
    cutoff = datetime.utcnow() - timedelta(seconds=30)
    online = []
    for info in _clients.values():
        try:
            last_seen = datetime.fromisoformat(info["last_seen"].replace("Z", ""))
        except ValueError:
            continue
        if last_seen >= cutoff:
            online.append(info)
    return {"online": online, "count": len(online)}


@app.get("/api/menu")
def menu(token: str):
    if token not in _sessions:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {"items": MENU_ITEMS}
