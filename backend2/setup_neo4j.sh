#!/bin/bash

# 医药知识图谱系统 - Neo4j 导入脚本

echo "========================================"
echo "  Neo4j 数据导入工具"
echo "========================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3"
    exit 1
fi

# 检查Neo4j
echo "[检查] Neo4j服务状态..."
if ! nc -z localhost 7687 2>/dev/null; then
    echo "[警告] Neo4j未运行"
    echo ""
    echo "请先启动Neo4j："
    echo "  macOS: brew services start neo4j"
    echo "  Linux: sudo systemctl start neo4j"
    echo ""
    read -p "是否继续？（使用SQLite模式测试）[Y/N]: " choice
    if [ "$choice" != "Y" ] && [ "$choice" != "y" ]; then
        exit 1
    fi
fi

# 读取配置
echo ""
echo "[配置] 请输入Neo4j连接信息（直接回车使用默认值）："
echo ""

read -p "连接地址 [bolt://localhost:7687]: " NEO4J_URI
NEO4J_URI=${NEO4J_URI:-bolt://localhost:7687}

read -p "用户名 [neo4j]: " NEO4J_USER
NEO4J_USER=${NEO4J_USER:-neo4j}

read -s -p "密码 [neo4j]: " NEO4J_PASSWORD
echo ""
NEO4J_PASSWORD=${NEO4J_PASSWORD:-neo4j}

# 更新配置文件
echo ""
echo "[配置] 更新配置文件..."

cat > .env << EOF
# 业务数据库配置
DATABASE_URL=sqlite:///./db/medical_system.db

# 知识图谱数据库配置
GRAPH_BACKEND=neo4j

# Neo4j连接配置
NEO4J_URI=${NEO4J_URI}
NEO4J_USER=${NEO4J_USER}
NEO4J_PASSWORD=${NEO4J_PASSWORD}
NEO4J_DATABASE=neo4j

# 其他配置
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
EOF

echo "[完成] 配置文件已更新"

# 执行数据导入
echo ""
echo "========================================"
echo "[导入] 开始导入知识图谱数据..."
echo "========================================"
echo ""

python3 import_neo4j.py

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================"
    echo "[成功] 数据导入完成！"
    echo "========================================"
    echo ""
    echo "下一步："
    echo "  1. 启动后端服务：python3 main.py"
    echo "  2. 访问知识图谱：http://localhost:8000/graph/graph-browser.html"
    echo "  3. 在Neo4j Browser中查看：http://localhost:7474"
else
    echo ""
    echo "[错误] 数据导入失败"
    echo "请检查："
    echo "  1. Neo4j服务是否正在运行"
    echo "  2. 连接信息是否正确"
    echo "  3. 查看 neo4j_import.log 日志文件"
fi
