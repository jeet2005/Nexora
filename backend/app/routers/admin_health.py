import time

import psutil
import requests
from fastapi import APIRouter, Depends

from app.config import settings
from app.middleware.admin_auth_guard import require_admin
from app.services.persistence_service import collection

router = APIRouter(prefix="/api/admin/health", tags=["admin", "health"], dependencies=[Depends(require_admin)])

@router.get("")
def get_system_health():
    # Check MongoDB connection
    col = collection("datasets")
    mongo_status = "online" if col is not None else "offline"
    
    # Check Ollama
    ollama_status = "offline"
    try:
        res = requests.get(settings.ollama_base_url, timeout=2)
        if res.status_code == 200:
            ollama_status = "online"
    except Exception:
        pass
        
    return {
        "status": "healthy" if mongo_status == "online" and ollama_status == "online" else "degraded",
        "services": {
            "api": "online",
            "database": mongo_status,
            "frontend": "online",
            "ollama": ollama_status
        },
        "system": {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "uptime_seconds": time.time() - psutil.boot_time()
        }
    }
