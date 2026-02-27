from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
import json, os, random

app = FastAPI(title="Spark Dating API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend
if os.path.exists("frontend"):
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")

# --- Simple file-based storage (replace with DB in prod) ---
DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"users": {}, "likes": [], "matches": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# --- Models ---
class UserProfile(BaseModel):
    tg_id: int
    name: str
    age: int
    city: str
    bio: Optional[str] = ""
    gender: str  # male / female
    photo: Optional[str] = ""

class LikeAction(BaseModel):
    from_id: int
    to_id: int
    action: str  # like / nope / super

# --- Routes ---
@app.get("/")
def root():
    return {"status": "Spark API is running 🔥"}

@app.post("/profile")
def upsert_profile(profile: UserProfile):
    data = load_data()
    data["users"][str(profile.tg_id)] = profile.dict()
    save_data(data)
    return {"ok": True}

@app.get("/profile/{tg_id}")
def get_profile(tg_id: int):
    data = load_data()
    user = data["users"].get(str(tg_id))
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.get("/feed/{tg_id}")
def get_feed(tg_id: int, limit: int = 20):
    """Return opposite gender profiles not yet seen"""
    data = load_data()
    me = data["users"].get(str(tg_id))
    if not me:
        raise HTTPException(404, "Register first")
    opposite = "female" if me["gender"] == "male" else "male"
    seen = {l["to_id"] for l in data["likes"] if l["from_id"] == tg_id}
    feed = [
        u for uid, u in data["users"].items()
        if u["gender"] == opposite and int(uid) != tg_id and int(uid) not in seen
    ]
    random.shuffle(feed)
    return feed[:limit]

@app.post("/like")
def like(action: LikeAction):
    data = load_data()
    data["likes"].append(action.dict())
    matched = False
    if action.action in ("like", "super"):
        # Check if other person liked us
        reverse = any(
            l["from_id"] == action.to_id and l["to_id"] == action.from_id and l["action"] in ("like", "super")
            for l in data["likes"]
        )
        if reverse:
            matched = True
            data["matches"].append({"user1": action.from_id, "user2": action.to_id})
    save_data(data)
    return {"matched": matched}

@app.get("/matches/{tg_id}")
def get_matches(tg_id: int):
    data = load_data()
    matches = []
    for m in data["matches"]:
        other_id = m["user2"] if m["user1"] == tg_id else m["user1"] if m["user2"] == tg_id else None
        if other_id:
            other = data["users"].get(str(other_id))
            if other:
                matches.append(other)
    return matches

@app.get("/stats/{tg_id}")
def get_stats(tg_id: int):
    data = load_data()
    likes_received = sum(1 for l in data["likes"] if l["to_id"] == tg_id and l["action"] == "like")
    matches = sum(1 for m in data["matches"] if tg_id in (m["user1"], m["user2"]))
    return {"likes": likes_received, "matches": matches, "views": likes_received * 3}
