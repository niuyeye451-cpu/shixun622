@echo off
chcp 65001 >nul
echo ========================================
echo   医药知识图谱系统 - 快速启动
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python，请先安装Python 3.9+
    echo 下载地址：https://www.python.org/downloads/
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo [检查] 检查Python依赖...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo [安装] 正在安装Python依赖...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
)

REM 检查Neo4j状态
echo.
echo [检查] Neo4j状态检查...
netstat -ano | findstr "7474" >nul 2>&1
if errorlevel 1 (
    echo [警告] Neo4j未运行（端口7474未检测到）
    echo        如需使用Neo4j，请先启动Neo4j服务
    echo        当前将使用SQLite模式运行
    echo.
)

REM 检查.env配置
echo [检查] 配置文件...
if not exist ".env" (
    echo [警告] .env配置文件不存在，将使用默认配置
)

REM 启动服务
echo ========================================
echo [启动] 正在启动医药知识图谱系统...
echo ========================================
echo.
echo 服务地址：
echo   - API文档：http://localhost:8000/docs
echo   - 知识图谱可视化：http://localhost:8000/graph/graph-browser.html
echo.
echo 按 Ctrl+C 停止服务
echo ========================================
echo.

python main.py

pause
