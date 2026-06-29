@echo off
chcp 65001 >nul
echo ========================================
echo   Neo4j 数据导入工具
echo ========================================
echo.

REM 设置颜色
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set NC=[0m

REM 检查Neo4j是否运行
echo [检查] Neo4j服务状态...
netstat -ano | findstr "7687" >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%[警告]%NC% Neo4j未运行！
    echo.
    echo 请先启动Neo4j：
    echo   1. Windows: 在服务中启动Neo4j服务
    echo   2. macOS: brew services start neo4j
    echo   3. Linux: sudo systemctl start neo4j
    echo.
    echo 或者下载Neo4j Desktop: https://neo4j.com/download-center/#desktop
    echo.
    set /p choice=是否继续？（使用SQLite模式测试）[Y/N]:
    if /i not "%choice%"=="Y" exit /b 1
)

REM 读取Neo4j配置
echo.
echo [配置] 请输入Neo4j连接信息（直接回车使用默认值）：
echo.

set /p NEO4J_URI="连接地址 [bolt://localhost:7687]: "
if "%NEO4J_URI%"=="" set NEO4J_URI=bolt://localhost:7687

set /p NEO4J_USER="用户名 [neo4j]: "
if "%NEO4J_USER%"=="" set NEO4J_USER=neo4j

set /p NEO4J_PASSWORD="密码 [neo4j]: "
if "%NEO4J_PASSWORD%"=="" set NEO4J_PASSWORD=neo4j

REM 更新.env文件
echo.
echo [配置] 更新配置文件...

(
    echo # 业务数据库配置
    echo DATABASE_URL=sqlite:///./db/medical_system.db
    echo.
    echo # 知识图谱数据库配置
    echo GRAPH_BACKEND=neo4j
    echo.
    echo # Neo4j连接配置
    echo NEO4J_URI=%NEO4J_URI%
    echo NEO4J_USER=%NEO4J_USER%
    echo NEO4J_PASSWORD=%NEO4J_PASSWORD%
    echo NEO4J_DATABASE=neo4j
    echo.
    echo # 其他配置
    echo SECRET_KEY=your-secret-key-here-change-in-production
    echo ALGORITHM=HS256
    echo ACCESS_TOKEN_EXPIRE_MINUTES=120
) > .env

echo %GREEN%[完成]%NC% 配置文件已更新

REM 执行数据导入
echo.
echo ========================================
echo [导入] 开始导入知识图谱数据...
echo ========================================
echo.

python import_neo4j.py

if errorlevel 1 (
    echo.
    echo %RED%[错误]%NC% 数据导入失败
    echo 请检查：
    echo   1. Neo4j服务是否正在运行
    echo   2. 连接信息是否正确
    echo   3. 查看 neo4j_import.log 日志文件
    pause
    exit /b 1
)

echo.
echo ========================================
echo %GREEN%[成功]%NC% 数据导入完成！
echo ========================================
echo.
echo 下一步：
echo   1. 启动后端服务：python main.py
echo   2. 访问知识图谱：http://localhost:8000/graph/graph-browser.html
echo   3. 在Neo4j Browser中查看：http://localhost:7474
echo.
pause
