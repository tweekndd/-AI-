"""
AI Trade Customer Analyzer V2.0 - 主程序入口
客户发现 + 客户分析 + 客户数据库平台
"""
import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.database import init_db
from app.api.routes import router

app = FastAPI(
    title="AI Trade Customer Analyzer V2.0",
    description="客户发现 + 客户分析 + 客户数据库平台",
    version="2.0.0",
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(router)


@app.get("/")
async def index_page():
    return FileResponse("app/templates/index.html")


@app.get("/discovery")
async def discovery_page():
    return FileResponse("app/templates/discovery.html")


@app.get("/customer/{customer_id}")
async def detail_page(customer_id: int):
    return FileResponse("app/templates/detail.html")


@app.on_event("startup")
def on_startup():
    init_db()
    print("=" * 50)
    print("  AI Trade Customer Analyzer V2.0")
    print(" 客户发现 + 数据分析 + 客户数据库平台")
    print("=" * 50)
    print(" 访问地址: http://localhost:8000")
    print(" 客户列表: http://localhost:8000")
    print(" 客户发现: http://localhost:8000/discovery")
    print("=" * 50)


if __name__ == "__main__":
    os.makedirs("app/uploads", exist_ok=True)
    os.makedirs("app/static/css", exist_ok=True)
    os.makedirs("app/templates", exist_ok=True)

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info",
    )
