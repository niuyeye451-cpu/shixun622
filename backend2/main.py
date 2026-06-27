from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.database import engine, Base
from app.routes.common import router as common_router
from app.routes.patient import router as patient_router
from app.routes.doctor import router as doctor_router
from app.routes.admin import router as admin_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="医药问答系统 API",
    description="基于FastAPI的医药问答系统后端API",
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

if not os.path.exists("uploads"):
    os.makedirs("uploads")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "医药问答系统 API 运行正常"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)