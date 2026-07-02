from datetime import datetime
import json

import bcrypt
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import (
    admin_api_keys,
    admin_audit,
    admin_auth,
    admin_content,
    admin_datasets,
    admin_drift,
    admin_health,
    admin_users,
    advanced,
    auth,
    chat,
    content,
    cyber_stream,
    datasets,
    explainability,
    pipeline,
    training,
    users,
)
from app.services.persistence_service import collection

app = FastAPI(
    title=settings.app_name,
    description="Autonomous AI-powered predictive analytics platform",
    version="0.4.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(content.router)
app.include_router(pipeline.router)
app.include_router(training.router)
app.include_router(training.public_router)
app.include_router(chat.router)
app.include_router(explainability.router)
app.include_router(advanced.router)
app.include_router(cyber_stream.router)
app.include_router(admin_auth.router)
app.include_router(admin_api_keys.router)
app.include_router(admin_datasets.router)
app.include_router(admin_content.router)
app.include_router(admin_health.router)
app.include_router(admin_audit.router)
app.include_router(admin_drift.router)
app.include_router(admin_users.router)

def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


@app.on_event("startup")
async def seed_admin_users():
    if settings.persistence_backend != "mongodb":
        return

    if not settings.admin_seed_json or not settings.admin_seed_password:
        return

    try:
        admins_to_seed = json.loads(settings.admin_seed_json)
    except ValueError:
        return

    if not isinstance(admins_to_seed, list):
        return

    admins_coll = collection("admins")
    if admins_coll is None:
        return

    for index, admin in enumerate(admins_to_seed, start=1):
        if not isinstance(admin, dict):
            continue
        email = admin.get("email")
        name = admin.get("name")
        if not isinstance(email, str) or not isinstance(name, str):
            continue

        if admins_coll.find_one({"email": email}) is None:
            admins_coll.insert_one(
                {
                    "email": email,
                    "password_hash": _hash_password(settings.admin_seed_password),
                    "name": name,
                    "avatar_url": f"/avatars/admins/a{index}.png",
                    "created_at": datetime.utcnow(),
                    "last_login": None,
                }
            )

from fastapi.responses import HTMLResponse


@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nexora API | Predictive Intelligence Engine</title>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
        <style>
            :root {
                --bg: #090d16;
                --text: #f3f4f6;
                --text-muted: #9ca3af;
                --primary: #10b981;
                --primary-glow: rgba(16, 185, 129, 0.15);
                --glass-bg: rgba(17, 24, 39, 0.7);
                --glass-border: rgba(255, 255, 255, 0.08);
            }
            * {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }
            body {
                background-color: var(--bg);
                color: var(--text);
                font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                overflow-x: hidden;
                position: relative;
            }
            body::before {
                content: '';
                position: absolute;
                width: 400px;
                height: 400px;
                border-radius: 50%;
                background: radial-gradient(circle, var(--primary-glow) 0%, transparent 70%);
                top: 10%;
                left: 15%;
                z-index: 1;
                pointer-events: none;
            }
            body::after {
                content: '';
                position: absolute;
                width: 350px;
                height: 350px;
                border-radius: 50%;
                background: radial-gradient(circle, rgba(16, 185, 129, 0.1) 0%, transparent 70%);
                bottom: 10%;
                right: 15%;
                z-index: 1;
                pointer-events: none;
            }
            .container {
                max-width: 640px;
                width: 90%;
                background: var(--glass-bg);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid var(--glass-border);
                border-radius: 24px;
                padding: 48px;
                text-align: center;
                z-index: 10;
                box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
                animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .logo {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 24px;
            }
            .logo-icon {
                width: 40px;
                height: 40px;
                border-radius: 12px;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                color: #fff;
                font-weight: 700;
                font-size: 20px;
                box-shadow: 0 4px 12px var(--primary-glow);
            }
            .logo-text {
                font-size: 24px;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(to right, #ffffff, #9ca3af);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }
            h1 {
                font-size: 28px;
                font-weight: 600;
                margin-bottom: 12px;
                letter-spacing: -0.5px;
            }
            p {
                color: var(--text-muted);
                font-size: 16px;
                line-height: 1.6;
                margin-bottom: 36px;
            }
            .links {
                display: flex;
                flex-direction: column;
                gap: 12px;
                margin-bottom: 32px;
            }
            .btn {
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding: 14px 24px;
                border-radius: 12px;
                font-size: 15px;
                font-weight: 500;
                text-decoration: none;
                transition: all 0.2s ease;
                cursor: pointer;
            }
            .btn-primary {
                background: var(--primary);
                color: #06090e;
                box-shadow: 0 4px 15px var(--primary-glow);
            }
            .btn-primary:hover {
                background: #059669;
                transform: translateY(-1px);
                box-shadow: 0 6px 20px var(--primary-glow);
            }
            .btn-secondary {
                background: rgba(255, 255, 255, 0.05);
                color: var(--text);
                border: 1px solid var(--glass-border);
            }
            .btn-secondary:hover {
                background: rgba(255, 255, 255, 0.08);
                border-color: rgba(255, 255, 255, 0.15);
                transform: translateY(-1px);
            }
            .meta {
                font-family: 'JetBrains Mono', monospace;
                font-size: 12px;
                color: rgba(16, 185, 129, 0.85);
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
                padding-top: 16px;
                border-top: 1px solid var(--glass-border);
            }
            .pulse {
                width: 8px;
                height: 8px;
                background-color: var(--primary);
                border-radius: 50%;
                box-shadow: 0 0 0 0 var(--primary-glow);
                animation: pulse 1.6s infinite;
            }
            @keyframes pulse {
                0% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
                70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
                100% { transform: scale(0.9); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">
                <div class="logo-icon">N</div>
                <div class="logo-text">Nexora</div>
            </div>
            <h1>Predictive Analytics Backend</h1>
            <p>Welcome to the Nexora AI-powered predictive engine. This is the running REST API service powering intelligent dataset profiling, preprocessing pipelines, model benchmarks, and production studio predictions.</p>
            
            <div class="links">
                <a href="https://nexoraprediction.netlify.app" class="btn btn-primary">
                    Launch Application Dashboard
                </a>
                <a href="/docs" class="btn btn-secondary">
                    Explore API Reference & Interactive Docs
                </a>
                <a href="/api/health" class="btn btn-secondary">
                    Check Health Status (/api/health)
                </a>
            </div>

            <div class="meta">
                <div class="pulse"></div>
                <span>Service Operational · v0.4.0</span>
            </div>
        </div>
    </body>
    </html>
    """


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "nexora-api", "version": "0.4.0"}
