from datetime import datetime, timedelta

from fastapi import APIRouter, Depends

from app.middleware.admin_auth_guard import require_admin
from app.services.persistence_service import collection

router = APIRouter(prefix="/api/admin/users", tags=["admin", "users"], dependencies=[Depends(require_admin)])


@router.get("")
def list_users():
    users_col = collection("users")
    datasets_col = collection("datasets")
    if users_col is None:
        return []

    users = list(users_col.find({}, {"_id": 0, "password_hash": 0}))
    dataset_counts: dict[str, int] = {}
    if datasets_col is not None:
        for doc in datasets_col.find({}, {"user_id": 1}):
            uid = doc.get("user_id")
            if uid:
                dataset_counts[uid] = dataset_counts.get(uid, 0) + 1

    for user in users:
        user["datasets_count"] = dataset_counts.get(user.get("user_id"), 0)

    users.sort(key=lambda u: u.get("created_at") or datetime.min, reverse=True)
    return users


@router.get("/stats/growth")
def user_growth_stats(days: int = 7):
    users_col = collection("users")
    if users_col is None:
        return {"daily": [], "total": 0, "training_jobs_24h": 0}

    since = datetime.utcnow() - timedelta(days=days)
    daily: dict[str, int] = {}
    total = 0
    for user in users_col.find({}, {"created_at": 1}):
        total += 1
        created = user.get("created_at")
        if created and created >= since:
            key = created.strftime("%Y-%m-%d")
            daily[key] = daily.get(key, 0) + 1

    labels = []
    daily_series = []
    for i in range(days):
        day = (datetime.utcnow() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        labels.append(day)
        daily_series.append({"date": day, "users": daily.get(day, 0)})

    training_jobs_24h = 0
    datasets_col = collection("datasets")
    if datasets_col is not None:
        cutoff = datetime.utcnow() - timedelta(hours=24)
        training_jobs_24h = datasets_col.count_documents({
            "$or": [
                {"updated_at": {"$gte": cutoff}},
                {"created_at": {"$gte": cutoff}},
            ]
        })

    return {"daily": daily_series, "total": total, "training_jobs_24h": training_jobs_24h}
