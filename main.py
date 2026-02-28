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

DATA_FILE = "data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE) as f:
            return json.load(f)
    return {"users": {}, "likes": [], "matches": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

class UserProfile(BaseModel):
    tg_id: str
    name: str
    age: int
    city: str
    bio: Optional[str] = ""
    gender: str
    photo: Optional[str] = ""
    interests: Optional[List[str]] = []

class LikeAction(BaseModel):
    from_id: str
    to_id: str
    action: str

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
def get_profile(tg_id: str):
    data = load_data()
    user = data["users"].get(str(tg_id))
    if not user:
        raise HTTPException(404, "User not found")
    return user

@app.get("/feed/{tg_id}")
def get_feed(tg_id: str, limit: int = 20):
    data = load_data()
    me = data["users"].get(str(tg_id))
    if not me:
        raise HTTPException(404, "Register first")
    opposite = "female" if me["gender"] == "male" else "male"
    seen = {l["to_id"] for l in data["likes"] if l["from_id"] == str(tg_id)}
    feed = [
        u for uid, u in data["users"].items()
        if u.get("gender") == opposite
        and str(uid) != str(tg_id)
        and str(uid) not in seen
    ]
    random.shuffle(feed)
    return feed[:limit]

@app.post("/like")
def like(action: LikeAction):
    data = load_data()
    data["likes"] = [l for l in data["likes"] if not (l["from_id"] == str(action.from_id) and l["to_id"] == str(action.to_id))]
    data["likes"].append({"from_id": str(action.from_id), "to_id": str(action.to_id), "action": action.action})
    matched = False
    if action.action in ("like", "super"):
        reverse = any(
            l["from_id"] == str(action.to_id) and l["to_id"] == str(action.from_id) and l["action"] in ("like", "super")
            for l in data["likes"]
        )
        if reverse:
            matched = True
            already = any(
                (m["user1"] == str(action.from_id) and m["user2"] == str(action.to_id)) or
                (m["user1"] == str(action.to_id) and m["user2"] == str(action.from_id))
                for m in data["matches"]
            )
            if not already:
                data["matches"].append({"user1": str(action.from_id), "user2": str(action.to_id)})
    save_data(data)
    return {"matched": matched}

@app.get("/matches/{tg_id}")
def get_matches(tg_id: str):
    data = load_data()
    matches = []
    for m in data["matches"]:
        other_id = m["user2"] if m["user1"] == str(tg_id) else m["user1"] if m["user2"] == str(tg_id) else None
        if other_id:
            other = data["users"].get(str(other_id))
            if other:
                matches.append(other)
    return matches

@app.get("/stats/{tg_id}")
def get_stats(tg_id: str):
    data = load_data()
    likes = sum(1 for l in data["likes"] if l["to_id"] == str(tg_id) and l["action"] in ("like","super"))
    matches = sum(1 for m in data["matches"] if str(tg_id) in (m["user1"], m["user2"]))
    return {"likes": likes, "matches": matches, "views": likes * 3 + random.randint(0, 5)}

if os.path.exists("frontend"):
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
