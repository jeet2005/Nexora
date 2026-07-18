import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel

from app.config import settings
from app.middleware.admin_auth_guard import require_admin
from app.middleware.user_auth_guard import get_current_user
from app.services.persistence_service import collection

feedback_router = APIRouter(prefix="/api/community", tags=["community"])
admin_router = APIRouter(
    prefix="/api/admin/feedback",
    tags=["admin", "feedback"],
    dependencies=[Depends(require_admin)],
)

BADGE_DEFINITIONS = {
    "Founding Tester": "Joined Nexora's early community feedback program.",
    "Early Adopter": "Started contributing while Nexora is still growing.",
    "Community Supporter": "Helped improve Nexora through visible feedback.",
    "Research Contributor": "Shared research or dataset-focused feedback.",
    "Feedback Champion": "Submitted multiple useful ideas or reports.",
    "Top Tester": "Reported high-impact testing feedback.",
    "Bug Hunter": "Submitted actionable bug reports.",
    "Dataset Explorer": "Contributed dataset workflow feedback.",
    "Verified Researcher": "Received admin recognition for research input.",
    "Power User": "Earned strong contribution reputation.",
}

STATUS_VALUES = {
    "waiting",
    "under_review",
    "planned",
    "implemented",
    "closed",
    "duplicate",
}
CATEGORY_VALUES = {
    "bug",
    "feature",
    "dataset",
    "research",
    "ui",
    "performance",
    "other",
}
PRIORITY_VALUES = {"low", "normal", "high", "urgent"}
REACTION_VALUES = {
    "helpful",
    "interesting",
    "needs_more_info",
    "agree",
    "research_worthy",
}


class Attachment(BaseModel):
    name: str
    url: str | None = None
    kind: str = "file"


class FeedbackCreate(BaseModel):
    title: str
    category: str
    description: str
    priority: str = "normal"
    suggestion: str | None = None
    attachments: list[Attachment] = []


class FeedbackAdminUpdate(BaseModel):
    status: str | None = None
    priority: str | None = None
    pinned: bool | None = None
    duplicate_of: str | None = None
    stars: int | None = None
    badge_awarded: str | None = None
    assigned_to: str | None = None
    internal_note: str | None = None


class FeedbackReplyCreate(BaseModel):
    message: str


class ReactionCreate(BaseModel):
    reaction: str


def _local_path(name: str) -> Path:
    return settings.upload_dir / f"{name}.json"


def _load_local(name: str) -> list[dict]:
    path = _local_path(name)
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    return data if isinstance(data, list) else []


def _save_local(name: str, rows: list[dict]) -> None:
    path = _local_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")


def _strip_id(doc: dict) -> dict:
    out = dict(doc)
    out.pop("_id", None)
    return out


def _serialize(doc: dict) -> dict:
    out = _strip_id(doc)
    for key in ("created_at", "updated_at", "implemented_at"):
        if isinstance(out.get(key), datetime):
            out[key] = out[key].isoformat()
    replies = []
    for reply in out.get("admin_replies") or []:
        item = dict(reply)
        if isinstance(item.get("created_at"), datetime):
            item["created_at"] = item["created_at"].isoformat()
        replies.append(item)
    out["admin_replies"] = replies
    return out


def _current_user_id(token: dict) -> str:
    uid = token.get("uid")
    if not isinstance(uid, str) or not uid:
        raise HTTPException(status_code=401, detail="Invalid authentication token")
    return uid


def _feedback_collection():
    return collection("community_feedback")


def _notification_collection():
    return collection("notifications")


def _follow_collection():
    return collection("community_follows")


def _showcase_collection():
    return collection("community_showcases")


def _all_feedback() -> list[dict]:
    feedback_col = _feedback_collection()
    if feedback_col is None:
        return _load_local("community_feedback")
    return [_strip_id(doc) for doc in feedback_col.find({})]


def _find_feedback(feedback_id: str) -> dict | None:
    feedback_col = _feedback_collection()
    if feedback_col is None:
        return next(
            (
                item
                for item in _load_local("community_feedback")
                if item.get("id") == feedback_id
            ),
            None,
        )
    doc = feedback_col.find_one({"id": feedback_id})
    return _strip_id(doc) if doc else None


def _save_feedback(doc: dict) -> dict:
    feedback_col = _feedback_collection()
    if feedback_col is None:
        rows = _load_local("community_feedback")
        for index, item in enumerate(rows):
            if item.get("id") == doc.get("id"):
                rows[index] = doc
                break
        else:
            rows.append(doc)
        _save_local("community_feedback", rows)
        return doc
    feedback_col.update_one({"id": doc["id"]}, {"$set": doc}, upsert=True)
    saved = feedback_col.find_one({"id": doc["id"]}) or doc
    return _strip_id(saved)


def _public_upload_url(path: Path) -> str:
    try:
        return f"/uploads/{path.relative_to(settings.upload_dir).as_posix()}"
    except ValueError:
        return f"/uploads/community/{path.name}"


async def _store_uploads(files: list[UploadFile]) -> list[dict]:
    stored = []
    upload_root = settings.upload_dir / "community"
    upload_root.mkdir(parents=True, exist_ok=True)
    for file in files:
        if not file.filename:
            continue
        suffix = Path(file.filename).suffix
        safe_name = f"{uuid4()}{suffix}"
        target = upload_root / safe_name
        data = await file.read()
        target.write_bytes(data)
        stored.append(
            {
                "name": file.filename,
                "url": _public_upload_url(target),
                "kind": "screenshot"
                if (file.content_type or "").startswith("image/")
                else "file",
                "content_type": file.content_type,
                "size": len(data),
            }
        )
    return stored


def _reaction_counts(doc: dict) -> dict:
    return {
        key: len(value or []) for key, value in (doc.get("reactions") or {}).items()
    }


def _period_start(period: str) -> datetime | None:
    now = datetime.utcnow()
    if period == "weekly":
        return now - timedelta(days=7)
    if period == "monthly":
        return now - timedelta(days=30)
    return None


def _filter_period(rows: list[dict], period: str) -> list[dict]:
    start = _period_start(period)
    if not start:
        return rows
    return [item for item in rows if (item.get("created_at") or datetime.min) >= start]


def _all_follows() -> list[dict]:
    follows_col = _follow_collection()
    if follows_col is None:
        return _load_local("community_follows")
    return [_strip_id(doc) for doc in follows_col.find({})]


def _save_follow(doc: dict) -> dict:
    follows_col = _follow_collection()
    if follows_col is None:
        rows = [
            item
            for item in _load_local("community_follows")
            if not (
                item.get("follower_id") == doc["follower_id"]
                and item.get("following_id") == doc["following_id"]
            )
        ]
        rows.append(doc)
        _save_local("community_follows", rows)
        return doc
    follows_col.update_one(
        {"follower_id": doc["follower_id"], "following_id": doc["following_id"]},
        {"$set": doc},
        upsert=True,
    )
    return doc


def _delete_follow(follower_id: str, following_id: str) -> None:
    follows_col = _follow_collection()
    if follows_col is None:
        rows = [
            item
            for item in _load_local("community_follows")
            if not (
                item.get("follower_id") == follower_id
                and item.get("following_id") == following_id
            )
        ]
        _save_local("community_follows", rows)
        return
    follows_col.delete_one({"follower_id": follower_id, "following_id": following_id})


def _showcase_for_user(user_id: str) -> dict:
    showcase_col = _showcase_collection()
    if showcase_col is None:
        return next(
            (
                item
                for item in _load_local("community_showcases")
                if item.get("user_id") == user_id
            ),
            {"user_id": user_id},
        )
    doc = showcase_col.find_one({"user_id": user_id})
    return _strip_id(doc) if doc else {"user_id": user_id}


def _save_showcase(user_id: str, payload: dict) -> dict:
    doc = {"user_id": user_id, **payload, "updated_at": datetime.utcnow()}
    showcase_col = _showcase_collection()
    if showcase_col is None:
        rows = [
            item
            for item in _load_local("community_showcases")
            if item.get("user_id") != user_id
        ]
        rows.append(doc)
        _save_local("community_showcases", rows)
        return doc
    showcase_col.update_one({"user_id": user_id}, {"$set": doc}, upsert=True)
    return _strip_id(showcase_col.find_one({"user_id": user_id}) or doc)


def _heatmap(rows: list[dict]) -> list[dict]:
    daily: dict[str, int] = {}
    for item in rows:
        created = item.get("created_at")
        if isinstance(created, str):
            try:
                created = datetime.fromisoformat(created)
            except ValueError:
                created = None
        if isinstance(created, datetime):
            key = created.strftime("%Y-%m-%d")
            daily[key] = daily.get(key, 0) + 1
    return [{"date": key, "count": daily[key]} for key in sorted(daily)]


def _add_notification(
    user_id: str, title: str, message: str, kind: str, feedback_id: str | None = None
) -> None:
    note = {
        "id": str(uuid4()),
        "user_id": user_id,
        "title": title,
        "message": message,
        "kind": kind,
        "feedback_id": feedback_id,
        "read": False,
        "created_at": datetime.utcnow(),
    }
    notes_col = _notification_collection()
    if notes_col is None:
        rows = _load_local("notifications")
        rows.append(note)
        _save_local("notifications", rows)
        return
    notes_col.insert_one(note)


def _sort_datetime(value: object) -> datetime:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return datetime.min
    return datetime.min


def _badge_objects(names: list[str]) -> list[dict]:
    return [
        {
            "name": name,
            "reason": BADGE_DEFINITIONS.get(
                name, "Earned through Nexora community activity."
            ),
        }
        for name in names
    ]


def _stats_for_user(user_id: str) -> dict:
    rows = [item for item in _all_feedback() if item.get("user_id") == user_id]
    stars = sum(int(item.get("stars") or 0) for item in rows)
    replies = sum(len(item.get("admin_replies") or []) for item in rows)
    badges = sorted(
        {str(item["badge_awarded"]) for item in rows if item.get("badge_awarded")}
    )
    bugs = sum(1 for item in rows if item.get("category") == "bug")
    features = sum(1 for item in rows if item.get("category") == "feature")
    accepted = sum(
        1 for item in rows if item.get("status") in {"planned", "implemented"}
    )
    implemented = sum(1 for item in rows if item.get("status") == "implemented")
    research = sum(1 for item in rows if item.get("category") == "research")
    datasets = sum(1 for item in rows if item.get("category") == "dataset")
    score = (
        len(rows) * 10
        + accepted * 20
        + implemented * 40
        + replies * 5
        + stars * 25
        + len(badges) * 30
    )
    earned = set(badges)
    if rows:
        earned.add("Early Adopter")
    if len(rows) >= 3:
        earned.add("Feedback Champion")
    if bugs:
        earned.add("Bug Hunter")
    if datasets:
        earned.add("Dataset Explorer")
    if research:
        earned.add("Research Contributor")
    if stars >= 3:
        earned.add("Community Supporter")
    if score >= 250:
        earned.add("Power User")
    level = "Explorer"
    if score >= 500:
        level = "Pioneer"
    elif score >= 350:
        level = "Innovator"
    elif score >= 220:
        level = "Researcher"
    elif score >= 100:
        level = "Contributor"
    return {
        "contribution_score": score,
        "feedback_submitted": len(rows),
        "feedback_accepted": accepted,
        "features_suggested": features,
        "bugs_reported": bugs,
        "replies_received": replies,
        "badges_earned": len(earned),
        "administrator_stars": stars,
        "implemented_suggestions": implemented,
        "level": level,
        "badges": _badge_objects(sorted(str(name) for name in earned)),
        "recent_feedback": [
            _serialize(item)
            for item in sorted(
                rows,
                key=lambda item: _sort_datetime(item.get("created_at")),
                reverse=True,
            )[:5]
        ],
    }


@feedback_router.post("/feedback")
def submit_feedback(payload: FeedbackCreate, token: dict = Depends(get_current_user)):
    category = payload.category.lower().replace(" ", "_")
    priority = payload.priority.lower().replace(" ", "_")
    if category not in CATEGORY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid feedback category")
    if priority not in PRIORITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    now = datetime.utcnow()
    doc: dict = {
        "id": str(uuid4()),
        "user_id": _current_user_id(token),
        "user_email": token.get("email"),
        "user_name": token.get("name") or token.get("email") or "Nexora User",
        "title": payload.title.strip(),
        "category": category,
        "description": payload.description.strip(),
        "priority": priority,
        "suggestion": (payload.suggestion or "").strip() or None,
        "attachments": [item.dict() for item in payload.attachments],
        "status": "waiting",
        "stars": 0,
        "pinned": False,
        "duplicate_of": None,
        "badge_awarded": None,
        "reactions": {},
        "admin_replies": [],
        "created_at": now,
        "updated_at": now,
    }
    if not doc["title"] or not doc["description"]:
        raise HTTPException(
            status_code=400, detail="Title and description are required"
        )
    return _serialize(_save_feedback(doc))


@feedback_router.get("/feedback/me")
def my_feedback(token: dict = Depends(get_current_user)):
    user_id = _current_user_id(token)
    rows = [item for item in _all_feedback() if item.get("user_id") == user_id]
    rows.sort(key=lambda item: _sort_datetime(item.get("created_at")), reverse=True)
    return [_serialize(item) for item in rows]


@feedback_router.post("/feedback/{feedback_id}/reactions")
def react_to_feedback(
    feedback_id: str, payload: ReactionCreate, token: dict = Depends(get_current_user)
):
    reaction = payload.reaction.lower().replace(" ", "_")
    if reaction not in REACTION_VALUES:
        raise HTTPException(status_code=400, detail="Invalid reaction")
    doc = _find_feedback(feedback_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Feedback not found")
    reactions = doc.get("reactions") or {}
    users = set(reactions.get(reaction) or [])
    users.add(_current_user_id(token))
    reactions[reaction] = sorted(users)
    doc["reactions"] = reactions
    doc["updated_at"] = datetime.utcnow()
    return _serialize(_save_feedback(doc))


@feedback_router.get("/profile/{user_id}/reputation")
def profile_reputation(user_id: str):
    return _stats_for_user(user_id)


@feedback_router.get("/leaderboard")
def leaderboard(period: str = "all"):
    del period
    users: dict[str, dict] = {}
    for item in _all_feedback():
        user_id = item.get("user_id")
        if not user_id:
            continue
        entry = users.setdefault(
            user_id,
            {
                "user_id": user_id,
                "name": item.get("user_name") or "Nexora User",
                "email": item.get("user_email"),
            },
        )
        entry.update(_stats_for_user(user_id))
    rows = sorted(
        users.values(), key=lambda item: item.get("contribution_score", 0), reverse=True
    )
    return rows[:50]


@feedback_router.get("/notifications")
def list_notifications(token: dict = Depends(get_current_user)):
    user_id = _current_user_id(token)
    notes_col = _notification_collection()
    if notes_col is None:
        rows = [
            item
            for item in _load_local("notifications")
            if item.get("user_id") == user_id
        ]
    else:
        rows = [_strip_id(item) for item in notes_col.find({"user_id": user_id})]
    rows.sort(key=lambda item: _sort_datetime(item.get("created_at")), reverse=True)
    return [_serialize(item) for item in rows[:50]]


@admin_router.get("")
def admin_list_feedback():
    rows = _all_feedback()
    rows.sort(
        key=lambda item: (
            bool(item.get("pinned")),
            _sort_datetime(item.get("updated_at")),
        ),
        reverse=True,
    )
    return [_serialize(item) for item in rows]


@admin_router.get("/analytics")
def admin_feedback_analytics():
    rows = _all_feedback()
    implemented = sum(1 for item in rows if item.get("status") == "implemented")
    closed = sum(1 for item in rows if item.get("status") in {"closed", "duplicate"})
    open_count = sum(
        1
        for item in rows
        if item.get("status") not in {"closed", "duplicate", "implemented"}
    )
    categories: dict[str, int] = {}
    research_topics: dict[str, int] = {}
    response_times = []
    
    for item in rows:
        category = item.get("category") or "other"
        categories[category] = categories.get(category, 0) + 1
        
        if category == "research":
            # Very simple topic extraction from title for trending research
            words = item.get("title", "").lower().split()
            for word in words:
                if len(word) > 4 and word not in {"about", "using", "with", "from", "could", "would"}:
                    research_topics[word] = research_topics.get(word, 0) + 1

        if item.get("admin_replies"):
            first_reply = item["admin_replies"][0]
            try:
                created = _sort_datetime(item.get("created_at"))
                replied = _sort_datetime(first_reply.get("created_at"))
                if replied > created:
                    response_times.append((replied - created).total_seconds() / 3600.0)
            except Exception:
                pass

    top_categories = sorted(categories.items(), key=lambda item: item[1], reverse=True)[:5]
    top_research = sorted(research_topics.items(), key=lambda item: item[1], reverse=True)[:5]
    
    avg_response = sum(response_times) / len(response_times) if response_times else 0.0

    return {
        "submitted": len(rows),
        "open": open_count,
        "closed": closed,
        "implemented": implemented,
        "average_response_time_hours": round(avg_response, 1),
        "most_requested_features": [
            {"category": key, "count": value} for key, value in top_categories
        ],
        "trending_research_topics": [
            {"topic": key.capitalize(), "count": value} for key, value in top_research
        ],
        "top_contributors": leaderboard()[:5],
        "most_active_users": leaderboard()[:5], # Using leaderboard as proxy for active users
    }


@admin_router.patch("/{feedback_id}")
def admin_update_feedback(
    feedback_id: str, payload: FeedbackAdminUpdate, admin: dict = Depends(require_admin)
):
    doc = _find_feedback(feedback_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Feedback not found")
    before_status = doc.get("status")
    updates = payload.dict(exclude_none=True)
    if "status" in updates and updates["status"] not in STATUS_VALUES:
        raise HTTPException(status_code=400, detail="Invalid status")
    if "priority" in updates and updates["priority"] not in PRIORITY_VALUES:
        raise HTTPException(status_code=400, detail="Invalid priority")
    if "stars" in updates:
        updates["stars"] = max(0, min(3, int(updates["stars"])))
    if "badge_awarded" in updates and updates["badge_awarded"] not in BADGE_DEFINITIONS:
        raise HTTPException(status_code=400, detail="Invalid badge")
    doc.update(updates)
    doc["updated_at"] = datetime.utcnow()
    if doc.get("status") == "implemented" and before_status != "implemented":
        doc["implemented_at"] = datetime.utcnow()
        if not doc.get("badge_awarded"):
            doc["badge_awarded"] = "Feedback Champion"
        _add_notification(
            doc["user_id"],
            "Suggestion implemented",
            f'Your suggestion "{doc.get("title")}" has been implemented. Thank you for improving Nexora.',
            "implemented",
            feedback_id,
        )
    if updates.get("stars"):
        _add_notification(
            doc["user_id"],
            "Feedback starred",
            f'An admin gave {updates["stars"]} star(s) to "{doc.get("title")}".',
            "starred",
            feedback_id,
        )
    if updates.get("badge_awarded"):
        _add_notification(
            doc["user_id"],
            "Badge earned",
            f"You earned the {updates['badge_awarded']} badge.",
            "badge",
            feedback_id,
        )
    doc["last_reviewed_by"] = admin.get("email")
    return _serialize(_save_feedback(doc))


@admin_router.post("/{feedback_id}/replies")
def admin_reply_feedback(
    feedback_id: str, payload: FeedbackReplyCreate, admin: dict = Depends(require_admin)
):
    doc = _find_feedback(feedback_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Feedback not found")
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Reply message is required")
    reply = {
        "id": str(uuid4()),
        "admin_email": admin.get("email"),
        "message": message,
        "created_at": datetime.utcnow(),
    }
    doc["admin_replies"] = [*(doc.get("admin_replies") or []), reply]
    doc["status"] = (
        "under_review" if doc.get("status") == "waiting" else doc.get("status")
    )
    doc["updated_at"] = datetime.utcnow()
    _add_notification(doc["user_id"], "Admin replied", message, "reply", feedback_id)
    return _serialize(_save_feedback(doc))
