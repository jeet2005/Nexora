from datetime import datetime

from app.services.persistence_service import collection


def log_admin_action(
    admin_email: str,
    action: str,
    target: str,
    ip_address: str | None = None,
) -> None:
    col = collection("audit_log")
    if col is None:
        return
    col.insert_one({
        "admin_email": admin_email,
        "action": action,
        "target": target,
        "timestamp": datetime.utcnow(),
        "ip_address": ip_address,
    })
