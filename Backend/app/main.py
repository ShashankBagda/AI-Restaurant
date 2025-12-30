from datetime import datetime, timedelta
from typing import Dict, List
import hashlib
import json
import os
import sqlite3

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
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

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PWA_DIR = os.path.join(ROOT_DIR, "Frontend", "app")
if os.path.isdir(PWA_DIR):
    app.mount("/app", StaticFiles(directory=PWA_DIR, html=True), name="pwa")

TOKEN_TTL_SECONDS = 3600
_clients: Dict[str, Dict[str, str]] = {}
_ws_clients: List[WebSocket] = []
_chef_rr: Dict[str, int] = {}
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
    specialty: str | None = None

class UpdateUserRequest(BaseModel):
    password: str | None = None
    role: str | None = None
    specialty: str | None = None

class UpdateProfileRequest(BaseModel):
    password: str | None = None

class MenuItemCreateRequest(BaseModel):
    item_id: str
    name: str
    price: float
    tags: List[str]
    category: str

class MenuItemUpdateRequest(BaseModel):
    name: str | None = None
    price: float | None = None
    tags: List[str] | None = None
    category: str | None = None

class PreferenceRequest(BaseModel):
    veg_only: bool | None = None
    favorite_category: str | None = None

class PaymentRequest(BaseModel):
    method: str

class RatingRequest(BaseModel):
    rating: int
    comment: str | None = None

class InventoryUpdateRequest(BaseModel):
    stock: int

class OrderItem(BaseModel):
    item_id: str
    quantity: int

class CreateOrderRequest(BaseModel):
    table_id: str
    items: List[OrderItem]

class UpdateOrderStatusRequest(BaseModel):
    status: str
    assigned_to: str | None = None

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
            "role TEXT NOT NULL, "
            "specialty TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions ("
            "token TEXT PRIMARY KEY, "
            "user_id TEXT NOT NULL, "
            "role TEXT NOT NULL, "
            "specialty TEXT, "
            "expires_at TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS menu_items ("
            "item_id TEXT PRIMARY KEY, "
            "name TEXT NOT NULL, "
            "price REAL NOT NULL, "
            "tags_json TEXT NOT NULL, "
            "category TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS user_preferences ("
            "user_id TEXT PRIMARY KEY, "
            "veg_only INTEGER DEFAULT 0, "
            "favorite_category TEXT)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS orders ("
            "order_id TEXT PRIMARY KEY, "
            "user_id TEXT NOT NULL, "
            "table_id TEXT NOT NULL, "
            "status TEXT NOT NULL, "
            "items_json TEXT NOT NULL, "
            "assigned_to TEXT, "
            "total REAL NOT NULL DEFAULT 0, "
            "payment_status TEXT NOT NULL DEFAULT 'unpaid', "
            "created_at TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS payments ("
            "payment_id TEXT PRIMARY KEY, "
            "order_id TEXT NOT NULL, "
            "amount REAL NOT NULL, "
            "method TEXT NOT NULL, "
            "status TEXT NOT NULL, "
            "created_at TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS ratings ("
            "order_id TEXT PRIMARY KEY, "
            "rating INTEGER NOT NULL, "
            "comment TEXT, "
            "created_at TEXT NOT NULL)"
        )
        conn.execute(
            "CREATE TABLE IF NOT EXISTS inventory ("
            "item_id TEXT PRIMARY KEY, "
            "stock INTEGER NOT NULL, "
            "updated_at TEXT NOT NULL)"
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN specialty TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN assigned_to TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE menu_items ADD COLUMN category TEXT")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN total REAL")
        except sqlite3.OperationalError:
            pass
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()
        _seed_default_users(conn)
        _seed_menu(conn)
        _seed_inventory(conn)
    finally:
        conn.close()


def _seed_default_users(conn):
    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()["count"]
    if existing:
        return
    conn.execute(
        "INSERT INTO users (user_id, password, role, specialty) VALUES (?, ?, ?, ?)",
        ("demo", _hash_password("demo123"), "customer", None),
    )
    conn.execute(
        "INSERT INTO users (user_id, password, role, specialty) VALUES (?, ?, ?, ?)",
        ("admin", _hash_password("admin123"), "admin", None),
    )
    conn.execute(
        "INSERT INTO users (user_id, password, role, specialty) VALUES (?, ?, ?, ?)",
        ("chef1", _hash_password("chef123"), "chef", "pizza"),
    )
    conn.commit()


def _seed_menu(conn):
    if not MENU_ITEMS:
        return

    item_ids = [item["id"] for item in MENU_ITEMS]
    placeholders = ",".join(["?"] * len(item_ids))
    conn.execute(f"DELETE FROM menu_items WHERE item_id NOT IN ({placeholders})", item_ids)
    for item in MENU_ITEMS:
        conn.execute(
            "INSERT INTO menu_items (item_id, name, price, tags_json, category) VALUES (?, ?, ?, ?, ?) "
            "ON CONFLICT(item_id) DO UPDATE SET name = excluded.name, price = excluded.price, "
            "tags_json = excluded.tags_json, category = excluded.category",
            (item["id"], item["name"], item["price"], json.dumps(item["tags"]), item["category"]),
        )
    conn.commit()


def _hash_password(password: str):
    salt = os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return f"{salt}${digest}"


def _verify_password(stored: str, password: str):
    if "$" not in stored:
        return stored == password
    salt, digest = stored.split("$", 1)
    check = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000).hex()
    return check == digest


def _seed_inventory(conn):
    items = conn.execute("SELECT item_id FROM menu_items").fetchall()
    now = datetime.utcnow().isoformat() + "Z"
    for row in items:
        conn.execute(
            "INSERT OR IGNORE INTO inventory (item_id, stock, updated_at) VALUES (?, ?, ?)",
            (row["item_id"], 50, now),
        )
    conn.commit()


def _parse_specialties(value: str | None):
    if not value:
        return []
    parts = [part.strip().lower() for part in value.split(",")]
    return [part for part in parts if part]


def _get_chefs_by_category(category: str):
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT user_id, specialty FROM users WHERE role = 'chef' ORDER BY user_id"
        ).fetchall()
    finally:
        conn.close()
    matches = []
    for row in rows:
        specialties = _parse_specialties(row["specialty"])
        if category.lower() in specialties:
            matches.append(row["user_id"])
    return matches


def _auto_assign_chef(category: str):
    chefs = _get_chefs_by_category(category)
    if not chefs:
        return None
    index = _chef_rr.get(category, 0) % len(chefs)
    _chef_rr[category] = index + 1
    return chefs[index]


def _load_menu_from_db():
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT item_id, name, price, tags_json, category FROM menu_items ORDER BY name"
        ).fetchall()
    finally:
        conn.close()
    items = []
    for row in rows:
        items.append(
            {
                "id": row["item_id"],
                "name": row["name"],
                "price": row["price"],
                "tags": json.loads(row["tags_json"]),
                "category": row["category"],
            }
        )
    return items


def _adjust_inventory(items_payload: list):
    conn = _get_db()
    try:
        for item in items_payload:
            conn.execute(
                "UPDATE inventory SET stock = CASE WHEN stock - ? < 0 THEN 0 ELSE stock - ? END, "
                "updated_at = ? WHERE item_id = ?",
                (item["quantity"], item["quantity"], datetime.utcnow().isoformat() + "Z", item["item_id"]),
            )
        conn.commit()
    finally:
        conn.close()


@app.get("/api/health")
def health():
    return {"status": "ok", "server_time": datetime.utcnow().isoformat() + "Z"}


@app.websocket("/ws/orders")
async def orders_ws(websocket: WebSocket):
    await websocket.accept()
    _ws_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _ws_clients:
            _ws_clients.remove(websocket)


@app.post("/api/login")
def login(payload: LoginRequest):
    if not payload.device_id or not payload.user_id or not payload.password or not payload.table_id:
        raise HTTPException(status_code=400, detail="device_id, user_id, password, table_id required")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT user_id, password, role, specialty FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row or not _verify_password(row["password"], payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if "$" not in row["password"]:
        conn = _get_db()
        try:
            conn.execute(
                "UPDATE users SET password = ? WHERE user_id = ?",
                (_hash_password(payload.password), payload.user_id),
            )
            conn.commit()
        finally:
            conn.close()
    token = f"{payload.device_id}-{int(datetime.utcnow().timestamp())}"
    expires_at = (datetime.utcnow() + timedelta(seconds=TOKEN_TTL_SECONDS)).isoformat() + "Z"
    conn = _get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO sessions (token, user_id, role, specialty, expires_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (token, payload.user_id, row["role"], row["specialty"], expires_at),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "token": token,
        "welcome": f"Hello {payload.user_id}",
        "role": row["role"],
        "specialty": row["specialty"],
        "expires_at": expires_at,
    }


def _get_token(request: Request):
    token = request.headers.get("X-Token")
    if not token:
        token = request.query_params.get("token", "")
    return token


def _require_session(request: Request):
    token = _get_token(request)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid token")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT token, user_id, role, specialty, expires_at FROM sessions WHERE token = ?",
            (token,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Invalid token")
    try:
        expires_at = datetime.fromisoformat(row["expires_at"].replace("Z", ""))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")
    if expires_at < datetime.utcnow():
        conn = _get_db()
        try:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
        finally:
            conn.close()
        raise HTTPException(status_code=401, detail="Token expired")
    return {
        "token": row["token"],
        "user_id": row["user_id"],
        "role": row["role"],
        "specialty": row["specialty"],
    }


def _require_role(request: Request, role: str):
    session = _require_session(request)
    if session.get("role") != role:
        raise HTTPException(status_code=403, detail="Insufficient role")
    return session


async def _broadcast(message: dict):
    dead = []
    for ws in _ws_clients:
        try:
            await ws.send_json(message)
        except RuntimeError:
            dead.append(ws)
    for ws in dead:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


@app.post("/api/register")
def register(payload: RegisterRequest):
    if not payload.user_id or not payload.password:
        raise HTTPException(status_code=400, detail="user_id and password required")
    if payload.role not in ("customer", "admin", "chef"):
        raise HTTPException(status_code=400, detail="role must be customer, admin, or chef")
    conn = _get_db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM users WHERE user_id = ?",
            (payload.user_id,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="User already exists")
        conn.execute(
            "INSERT INTO users (user_id, password, role, specialty) VALUES (?, ?, ?, ?)",
            (payload.user_id, _hash_password(payload.password), payload.role, payload.specialty),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "status": "created",
        "user_id": payload.user_id,
        "role": payload.role,
        "specialty": payload.specialty,
    }


@app.get("/api/users")
def list_users(request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        rows = conn.execute("SELECT user_id, role, specialty FROM users ORDER BY user_id").fetchall()
    finally:
        conn.close()
    return {
        "users": [
            {"user_id": row["user_id"], "role": row["role"], "specialty": row["specialty"]}
            for row in rows
        ]
    }


@app.get("/api/users/{user_id}")
def get_user(user_id: str, request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT user_id, role, specialty FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": row["user_id"], "role": row["role"], "specialty": row["specialty"]}


@app.put("/api/users/{user_id}")
def update_user(user_id: str, payload: UpdateUserRequest, request: Request):
    _require_role(request, "admin")
    if payload.role and payload.role not in ("customer", "admin", "chef"):
        raise HTTPException(status_code=400, detail="role must be customer, admin, or chef")
    conn = _get_db()
    try:
        row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        if payload.password is not None:
            conn.execute("UPDATE users SET password = ? WHERE user_id = ?", (_hash_password(payload.password), user_id))
        if payload.role is not None:
            conn.execute("UPDATE users SET role = ? WHERE user_id = ?", (payload.role, user_id))
        if payload.specialty is not None:
            conn.execute("UPDATE users SET specialty = ? WHERE user_id = ?", (payload.specialty, user_id))
        conn.commit()
    finally:
        conn.close()
    return {"status": "updated", "user_id": user_id}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: str, request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        cur = conn.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted", "user_id": user_id}


@app.put("/api/profile/{user_id}")
def update_profile(user_id: str, payload: UpdateProfileRequest, request: Request):
    session = _require_session(request)
    if session.get("user_id") != user_id:
        raise HTTPException(status_code=403, detail="Cannot modify another user")
    if payload.password is None:
        raise HTTPException(status_code=400, detail="password required")
    conn = _get_db()
    try:
        row = conn.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="User not found")
        conn.execute("UPDATE users SET password = ? WHERE user_id = ?", (_hash_password(payload.password), user_id))
        conn.commit()
    finally:
        conn.close()
    return {"status": "updated", "user_id": user_id}


@app.delete("/api/profile")
def delete_profile(request: Request):
    session = _require_session(request)
    if session.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customers only")
    conn = _get_db()
    try:
        conn.execute("DELETE FROM users WHERE user_id = ?", (session["user_id"],))
        conn.execute("DELETE FROM user_preferences WHERE user_id = ?", (session["user_id"],))
        conn.execute("DELETE FROM sessions WHERE user_id = ?", (session["user_id"],))
        conn.commit()
    finally:
        conn.close()
    return {"status": "deleted"}


@app.post("/api/orders")
async def create_order(payload: CreateOrderRequest, request: Request):
    session = _require_session(request)
    if session.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Only customers can create orders")
    if not payload.items:
        raise HTTPException(status_code=400, detail="items required")
    order_id = f"ord-{int(datetime.utcnow().timestamp())}-{session['user_id']}"
    menu_index = {item["id"]: item for item in _load_menu_from_db()}
    items_payload = []
    total = 0.0
    for item in payload.items:
        if item.item_id not in menu_index:
            raise HTTPException(status_code=400, detail=f"Invalid item_id {item.item_id}")
        menu_item = menu_index[item.item_id]
        category = menu_item.get("category", "unknown").lower()
        assigned_to = _auto_assign_chef(category)
        line_total = float(menu_item.get("price", 0)) * item.quantity
        total += line_total
        items_payload.append(
            {
                "item_id": item.item_id,
                "quantity": item.quantity,
                "category": category,
                "name": menu_item.get("name"),
                "price": menu_item.get("price"),
                "assigned_to": assigned_to,
            }
        )
    items_json = json.dumps(items_payload)
    conn = _get_db()
    try:
        conn.execute(
            "INSERT INTO orders (order_id, user_id, table_id, status, items_json, created_at, total, payment_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                order_id,
                session["user_id"],
                payload.table_id,
                "placed",
                items_json,
                datetime.utcnow().isoformat() + "Z",
                total,
                "unpaid",
            ),
        )
        conn.commit()
    finally:
        conn.close()
    _adjust_inventory(items_payload)
    await _broadcast(
        {
            "type": "order_created",
            "order_id": order_id,
            "table_id": payload.table_id,
            "items": items_payload,
        }
    )
    return {"order_id": order_id, "status": "placed", "total": total}


@app.get("/api/orders")
def list_orders(request: Request):
    session = _require_session(request)
    if session.get("role") not in ("admin", "chef"):
        raise HTTPException(status_code=403, detail="Insufficient role")
    specialties = _parse_specialties(session.get("specialty")) if session.get("role") == "chef" else None
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT order_id, user_id, table_id, status, items_json, assigned_to, created_at, total, payment_status "
            "FROM orders ORDER BY created_at DESC"
        ).fetchall()
        rating_rows = conn.execute("SELECT order_id, rating FROM ratings").fetchall()
    finally:
        conn.close()
    ratings = {row["order_id"]: row["rating"] for row in rating_rows}
    orders = []
    for row in rows:
        items = json.loads(row["items_json"])
        if specialties:
            items = [
                item
                for item in items
                if item.get("category") in specialties or item.get("assigned_to") == session.get("user_id")
            ]
            if not items:
                continue
        orders.append(
            {
                "order_id": row["order_id"],
                "user_id": row["user_id"],
                "table_id": row["table_id"],
                "status": row["status"],
                "items": items,
                "assigned_to": row["assigned_to"],
                "created_at": row["created_at"],
                "total": row["total"] or 0,
                "payment_status": row["payment_status"] or "unpaid",
                "rating": ratings.get(row["order_id"]),
            }
        )
    return {"orders": orders}


@app.get("/api/preferences")
def get_preferences(request: Request):
    session = _require_session(request)
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT veg_only, favorite_category FROM user_preferences WHERE user_id = ?",
            (session["user_id"],),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"veg_only": False, "favorite_category": None}
    return {"veg_only": bool(row["veg_only"]), "favorite_category": row["favorite_category"]}


@app.put("/api/preferences")
def update_preferences(payload: PreferenceRequest, request: Request):
    session = _require_session(request)
    conn = _get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO user_preferences (user_id, veg_only, favorite_category) VALUES (?, ?, ?)",
            (
                session["user_id"],
                1 if payload.veg_only else 0,
                payload.favorite_category,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "updated"}


@app.get("/api/recommendations")
def recommendations(request: Request):
    session = _require_session(request)
    items = _load_menu_from_db()
    now = datetime.utcnow().hour
    conn = _get_db()
    try:
        pref = conn.execute(
            "SELECT veg_only, favorite_category FROM user_preferences WHERE user_id = ?",
            (session["user_id"],),
        ).fetchone()
        order_rows = conn.execute("SELECT order_id, user_id, items_json FROM orders").fetchall()
        rating_rows = conn.execute("SELECT order_id, rating FROM ratings").fetchall()
    finally:
        conn.close()
    veg_only = bool(pref["veg_only"]) if pref else False
    favorite = pref["favorite_category"] if pref else None

    popularity = {}
    user_item_counts = {}
    user_category_counts = {}
    ratings = {row["order_id"]: row["rating"] for row in rating_rows}
    item_rating_sum = {}
    item_rating_count = {}
    for row in order_rows:
        items_in_order = json.loads(row["items_json"])
        for item in items_in_order:
            popularity[item["item_id"]] = popularity.get(item["item_id"], 0) + item["quantity"]
            if row["user_id"] == session["user_id"]:
                user_item_counts[item["item_id"]] = user_item_counts.get(item["item_id"], 0) + item["quantity"]
                user_category_counts[item["category"]] = user_category_counts.get(item["category"], 0) + item["quantity"]
            if row["order_id"] in ratings:
                item_rating_sum[item["item_id"]] = item_rating_sum.get(item["item_id"], 0) + ratings[row["order_id"]]
                item_rating_count[item["item_id"]] = item_rating_count.get(item["item_id"], 0) + 1

    top_user_category = None
    if user_category_counts:
        top_user_category = sorted(user_category_counts.items(), key=lambda x: x[1], reverse=True)[0][0]

    scored = []
    for item in items:
        if veg_only and "vegetarian" not in item["tags"]:
            continue
        score = popularity.get(item["id"], 0)
        if item["id"] in user_item_counts:
            score += user_item_counts[item["id"]] * 2
        if top_user_category and item["category"] == top_user_category:
            score += 3
        if favorite and item["category"] == favorite:
            score += 5
        if item["id"] in item_rating_sum:
            avg_rating = item_rating_sum[item["id"]] / item_rating_count[item["id"]]
            score += avg_rating * 2
        if now < 11 and "breakfast" in item["tags"]:
            score += 3
        if 11 <= now < 17 and "lunch" in item["tags"]:
            score += 3
        if now >= 17 and "dinner" in item["tags"]:
            score += 3
        scored.append((score, item))

    scored.sort(key=lambda x: x[0], reverse=True)
    top = [item for _, item in scored[:5]]
    return {"items": top}


@app.put("/api/orders/{order_id}")
async def update_order(order_id: str, payload: UpdateOrderStatusRequest, request: Request):
    session = _require_session(request)
    if session.get("role") not in ("admin", "chef"):
        raise HTTPException(status_code=403, detail="Insufficient role")
    if payload.status not in ("placed", "preparing", "ready", "served"):
        raise HTTPException(status_code=400, detail="Invalid status")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT order_id, items_json FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if payload.assigned_to is not None and session.get("role") == "admin":
            items = json.loads(row["items_json"])
            for item in items:
                item["assigned_to"] = payload.assigned_to
            conn.execute(
                "UPDATE orders SET items_json = ? WHERE order_id = ?",
                (json.dumps(items), order_id),
            )
        conn.execute("UPDATE orders SET status = ? WHERE order_id = ?", (payload.status, order_id))
        conn.commit()
    finally:
        conn.close()
    await _broadcast(
        {
            "type": "order_status",
            "order_id": order_id,
            "status": payload.status,
            "assigned_to": payload.assigned_to,
        }
    )
    return {"status": "updated", "order_id": order_id}


@app.get("/api/orders/mine")
def list_my_orders(request: Request):
    session = _require_session(request)
    if session.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customers only")
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT order_id, table_id, status, items_json, created_at, total, payment_status "
            "FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (session["user_id"],),
        ).fetchall()
        rating_rows = conn.execute("SELECT order_id, rating FROM ratings").fetchall()
    finally:
        conn.close()
    ratings = {row["order_id"]: row["rating"] for row in rating_rows}
    orders = []
    for row in rows:
        orders.append(
            {
                "order_id": row["order_id"],
                "table_id": row["table_id"],
                "status": row["status"],
                "items": json.loads(row["items_json"]),
                "created_at": row["created_at"],
                "total": row["total"] or 0,
                "payment_status": row["payment_status"] or "unpaid",
                "rating": ratings.get(row["order_id"]),
            }
        )
    return {"orders": orders}


@app.post("/api/orders/{order_id}/pay")
async def pay_order(order_id: str, payload: PaymentRequest, request: Request):
    session = _require_session(request)
    if session.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customers only")
    if payload.method not in ("card", "cash", "upi"):
        raise HTTPException(status_code=400, detail="Invalid payment method")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT order_id, user_id, total, payment_status FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not row or row["user_id"] != session["user_id"]:
            raise HTTPException(status_code=404, detail="Order not found")
        if row["payment_status"] == "paid":
            raise HTTPException(status_code=409, detail="Already paid")
        payment_id = f"pay-{int(datetime.utcnow().timestamp())}-{order_id}"
        conn.execute(
            "INSERT INTO payments (payment_id, order_id, amount, method, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (payment_id, order_id, row["total"], payload.method, "paid", datetime.utcnow().isoformat() + "Z"),
        )
        conn.execute("UPDATE orders SET payment_status = ? WHERE order_id = ?", ("paid", order_id))
        conn.commit()
    finally:
        conn.close()
    await _broadcast({"type": "payment", "order_id": order_id, "status": "paid"})
    return {"status": "paid", "order_id": order_id}


@app.post("/api/orders/{order_id}/rate")
async def rate_order(order_id: str, payload: RatingRequest, request: Request):
    session = _require_session(request)
    if session.get("role") != "customer":
        raise HTTPException(status_code=403, detail="Customers only")
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be 1-5")
    conn = _get_db()
    try:
        row = conn.execute(
            "SELECT order_id, user_id, status FROM orders WHERE order_id = ?",
            (order_id,),
        ).fetchone()
        if not row or row["user_id"] != session["user_id"]:
            raise HTTPException(status_code=404, detail="Order not found")
        if row["status"] != "served":
            raise HTTPException(status_code=400, detail="Order not served yet")
        conn.execute(
            "INSERT OR REPLACE INTO ratings (order_id, rating, comment, created_at) VALUES (?, ?, ?, ?)",
            (order_id, payload.rating, payload.comment, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
    finally:
        conn.close()
    await _broadcast({"type": "rating", "order_id": order_id, "rating": payload.rating})
    return {"status": "rated", "order_id": order_id}


@app.get("/api/billing")
def billing(request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT payment_id, order_id, amount, method, status, created_at FROM payments "
            "ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    payments = [
        {
            "payment_id": row["payment_id"],
            "order_id": row["order_id"],
            "amount": row["amount"],
            "method": row["method"],
            "status": row["status"],
            "created_at": row["created_at"],
        }
        for row in rows
    ]
    total = sum(payment["amount"] for payment in payments)
    return {"payments": payments, "total": total}


@app.get("/api/inventory")
def inventory(request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        rows = conn.execute(
            "SELECT inventory.item_id, inventory.stock, inventory.updated_at, menu_items.name "
            "FROM inventory LEFT JOIN menu_items ON inventory.item_id = menu_items.item_id "
            "ORDER BY menu_items.name"
        ).fetchall()
    finally:
        conn.close()
    return {
        "items": [
            {
                "item_id": row["item_id"],
                "name": row["name"],
                "stock": row["stock"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]
    }


@app.put("/api/inventory/{item_id}")
def update_inventory(item_id: str, payload: InventoryUpdateRequest, request: Request):
    _require_role(request, "admin")
    if payload.stock < 0:
        raise HTTPException(status_code=400, detail="stock must be >= 0")
    conn = _get_db()
    try:
        conn.execute(
            "INSERT OR REPLACE INTO inventory (item_id, stock, updated_at) VALUES (?, ?, ?)",
            (item_id, payload.stock, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "updated", "item_id": item_id}


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
def clients(request: Request):
    _require_role(request, "admin")
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


@app.delete("/api/clients/{device_id}")
def remove_client(device_id: str, request: Request):
    _require_role(request, "admin")
    if device_id in _clients:
        del _clients[device_id]
        return {"status": "removed", "device_id": device_id}
    raise HTTPException(status_code=404, detail="Device not found")


@app.post("/api/clients/clear")
def clear_clients(request: Request):
    _require_role(request, "admin")
    _clients.clear()
    return {"status": "cleared"}


@app.get("/api/menu")
def menu(request: Request):
    _require_session(request)
    return {"items": _load_menu_from_db()}


@app.get("/api/menu/admin")
def menu_admin(request: Request):
    _require_role(request, "admin")
    return {"items": _load_menu_from_db()}


@app.post("/api/menu")
def create_menu_item(payload: MenuItemCreateRequest, request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        exists = conn.execute(
            "SELECT 1 FROM menu_items WHERE item_id = ?",
            (payload.item_id,),
        ).fetchone()
        if exists:
            raise HTTPException(status_code=409, detail="Item already exists")
        conn.execute(
            "INSERT INTO menu_items (item_id, name, price, tags_json, category) VALUES (?, ?, ?, ?, ?)",
            (payload.item_id, payload.name, payload.price, json.dumps(payload.tags), payload.category),
        )
        conn.execute(
            "INSERT OR IGNORE INTO inventory (item_id, stock, updated_at) VALUES (?, ?, ?)",
            (payload.item_id, 0, datetime.utcnow().isoformat() + "Z"),
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "created", "item_id": payload.item_id}


@app.put("/api/menu/{item_id}")
def update_menu_item(item_id: str, payload: MenuItemUpdateRequest, request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        row = conn.execute("SELECT item_id FROM menu_items WHERE item_id = ?", (item_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Item not found")
        if payload.name is not None:
            conn.execute("UPDATE menu_items SET name = ? WHERE item_id = ?", (payload.name, item_id))
        if payload.price is not None:
            conn.execute("UPDATE menu_items SET price = ? WHERE item_id = ?", (payload.price, item_id))
        if payload.tags is not None:
            conn.execute(
                "UPDATE menu_items SET tags_json = ? WHERE item_id = ?",
                (json.dumps(payload.tags), item_id),
            )
        if payload.category is not None:
            conn.execute("UPDATE menu_items SET category = ? WHERE item_id = ?", (payload.category, item_id))
        conn.commit()
    finally:
        conn.close()
    return {"status": "updated", "item_id": item_id}


@app.delete("/api/menu/{item_id}")
def delete_menu_item(item_id: str, request: Request):
    _require_role(request, "admin")
    conn = _get_db()
    try:
        cur = conn.execute("DELETE FROM menu_items WHERE item_id = ?", (item_id,))
        conn.execute("DELETE FROM inventory WHERE item_id = ?", (item_id,))
        conn.commit()
    finally:
        conn.close()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted", "item_id": item_id}
