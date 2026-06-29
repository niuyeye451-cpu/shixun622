from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Admin
from app.utils import generate_id, get_password_hash


def init_default_admin():
    db: Session = SessionLocal()
    try:
        admin_count = db.query(Admin).count()
        if admin_count == 0:
            default_admin = Admin(
                admin_id=generate_id("admin_"),
                user_name="admin",
                phone="13800000000",
                password_hash=get_password_hash("admin123"),
                role_level=1,
                status=1
            )
            db.add(default_admin)
            db.commit()
            print("默认管理员账号创建成功: admin / admin123")
        else:
            print(f"管理员账号已存在，共 {admin_count} 个，跳过创建")
    except Exception as e:
        print(f"初始化默认管理员失败: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    init_default_admin()
