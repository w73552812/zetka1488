from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
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

class MediaItem(BaseModel):
    type: str  # image / video
    data: str  # base64 data URL
    main: bool = False

class MusicInfo(BaseModel):
    url: str
    title: Optional[str] = ""
    artist: Optional[str] = ""
    source: Optional[str] = "other"  # spotify / yandex / vk / other

class UserProfile(BaseModel):
    tg_id: Any
    name: str
    age: int
    city: str
    bio: Optional[str] = ""
    gender: str
    photo: Optional[str] = ""
    interests: Optional[List[str]] = []
    media: Optional[List[Dict]] = []
    music: Optional[Dict] = None

class LikeAction(BaseModel):
    from_id: Any
    to_id: Any
    action: str

@app.get("/")
def root():
    return {"status": "Spark API is running 🔥"}

@app.post("/profile")
def upsert_profile(profile: UserProfile):
    data = load_data()
    key = str(profile.tg_id)
    user_dict = profile.dict()
    user_dict["tg_id"] = key
    # Derive main photo from media if not set
    if not user_dict.get("photo") and user_dict.get("media"):
        main = next((m for m in user_dict["media"] if m.get("main")), None)
        if not main and user_dict["media"]:
            main = user_dict["media"][0]
        if main:
            user_dict["photo"] = main.get("data", "")
    data["users"][key] = user_dict
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

    opposite = "female" if me.get("gender") == "male" else "male"
    seen = {str(l["to_id"]) for l in data["likes"] if str(l["from_id"]) == str(tg_id)}

    feed = []
    for uid, u in data["users"].items():
        if str(uid) == str(tg_id): continue
        if str(uid) in seen: continue
        if u.get("gender") == opposite:
            feed.append(u)

    random.shuffle(feed)
    return feed[:limit]

@app.post("/like")
def like(action: LikeAction):
    data = load_data()
    from_id = str(action.from_id)
    to_id = str(action.to_id)
    data["likes"] = [l for l in data["likes"]
                     if not (str(l["from_id"]) == from_id and str(l["to_id"]) == to_id)]
    data["likes"].append({"from_id": from_id, "to_id": to_id, "action": action.action})
    matched = False
    if action.action in ("like", "super"):
        reverse = any(
            str(l["from_id"]) == to_id and str(l["to_id"]) == from_id and l["action"] in ("like", "super")
            for l in data["likes"]
        )
        if reverse:
            matched = True
            already = any(
                (str(m["user1"]) == from_id and str(m["user2"]) == to_id) or
                (str(m["user1"]) == to_id and str(m["user2"]) == from_id)
                for m in data["matches"]
            )
            if not already:
                data["matches"].append({"user1": from_id, "user2": to_id})
    save_data(data)
    return {"matched": matched}

@app.get("/matches/{tg_id}")
def get_matches(tg_id: str):
    data = load_data()
    matches = []
    for m in data["matches"]:
        other_id = None
        if str(m["user1"]) == str(tg_id): other_id = str(m["user2"])
        elif str(m["user2"]) == str(tg_id): other_id = str(m["user1"])
        if other_id:
            other = data["users"].get(other_id)
            if other: matches.append(other)
    return matches

@app.get("/stats/{tg_id}")
def get_stats(tg_id: str):
    data = load_data()
    likes = sum(1 for l in data["likes"]
                if str(l["to_id"]) == str(tg_id) and l["action"] in ("like", "super"))
    matches = sum(1 for m in data["matches"]
                  if str(tg_id) in (str(m["user1"]), str(m["user2"])))
    return {"likes": likes, "matches": matches, "views": likes * 3 + random.randint(0, 5)}

if os.path.exists("frontend"):
    app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
