from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.routes.common import router as common_router
from app.routes.patient import router as patient_router
from app.routes.doctor import router as doctor_router
from app.routes.admin import router as admin_router
from app.routes.knowledge_graph import router as knowledge_graph_router
from app.routes.llm import router as llm_router
from app.init_db import init_default_admin

Base.metadata.create_all(bind=engine)
init_default_admin()

app = FastAPI(
    title="医药问答系统 API",
    description="基于FastAPI的医药问答系统后端API，包含知识图谱查询、用户认证、问诊、大模型分析等功能",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(common_router)
app.include_router(patient_router)
app.include_router(doctor_router)
app.include_router(admin_router)
app.include_router(knowledge_graph_router)
app.include_router(llm_router)

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Mount frontend static HTML prototype directory (compatibility)
fronted_dir = os.path.join(os.path.dirname(__file__), "..", "fronted")
if os.path.exists(fronted_dir):
    app.mount("/fronted", StaticFiles(directory=fronted_dir, html=True), name="fronted")

# Mount graph static dir if exists (for knowledge graph HTML pages)
if not os.path.exists("static"):
    os.makedirs("static")
app.mount("/graph", StaticFiles(directory="static", html=True), name="static")


@app.get("/api/health", include_in_schema=False)
@app.get("/")
def health_check():
    return {"code": 200, "message": "success", "data": {"status": "ok", "message": "医药问答系统 API 运行正常"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)