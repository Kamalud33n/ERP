from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from app.core.database import engine, Base
from app.models import user, employee, hr, finance, procurement, inventory, asset, workflow, workflow_config

from app.api.v1 import (
    auth,
    employee as employee_router,
    hr as hr_router,
    finance as finance_router,
    dashboard,
    admin as admin_router,
    procurement as procurement_router,
    inventory as inventory_router,
    asset as asset_router,
    admin_extra as admin_extra_router,
    workflow as workflow_router,
    workflow_config as workflow_config_router,
    workflows as workflows_router,          # Phase 2: Advanced workflows
    notifications as notifications_router,  # NEW
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ERP System", version="1.0.0", docs_url="/api/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,                   prefix="/api/v1/auth",           tags=["Auth"])
app.include_router(employee_router.router,        prefix="/api/v1/employee",       tags=["Employee"])
app.include_router(hr_router.router,              prefix="/api/v1/hr",             tags=["HR"])
app.include_router(finance_router.router,         prefix="/api/v1/finance",        tags=["Finance"])
app.include_router(dashboard.router,              prefix="/api/v1/dashboard",      tags=["Dashboard"])
app.include_router(admin_router.router,           prefix="/api/v1/admin",          tags=["Admin"])
app.include_router(admin_extra_router.router,     prefix="/api/v1/admin",          tags=["Admin"])
app.include_router(workflow_router.router,        prefix="/api/v1/workflow",       tags=["Workflow"])
app.include_router(workflow_config_router.router, prefix="/api/v1/workflow-config",tags=["Workflow Config"])
app.include_router(workflows_router.router,       prefix="/api/v1/workflows",      tags=["Advanced Workflows"])
app.include_router(procurement_router.router,     prefix="/api/v1/procurement",    tags=["Procurement"])
app.include_router(inventory_router.router,       prefix="/api/v1/inventory",      tags=["Inventory"])
app.include_router(asset_router.router,           prefix="/api/v1/asset",          tags=["Asset"])
app.include_router(notifications_router.router,   prefix="/api/v1/notifications",  tags=["Notifications"])  # NEW

@app.get("/health")
@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(BASE_DIR, "static")

print(f"Static dir: {static_dir}")
print(f"Static exists: {os.path.exists(static_dir)}")

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
    i18n_dir = os.path.join(static_dir, "i18n")
    if os.path.exists(i18n_dir):
        app.mount("/i18n", StaticFiles(directory=i18n_dir), name="i18n")

@app.get("/")
def serve_login():
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))

@app.get("/{page}.html")
def serve_page(page: str):
    file_path = os.path.join(BASE_DIR, "static", f"{page}.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return FileResponse(os.path.join(BASE_DIR, "static", "index.html"))