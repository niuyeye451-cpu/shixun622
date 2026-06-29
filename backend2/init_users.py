import sys
sys.path.insert(0, 'd:\\medical system')

from app.database import SessionLocal
from app.models import Admin, Patient, Doctor
from app.utils import get_password_hash, generate_id

db = SessionLocal()

try:
    print('=== 初始化默认管理员 ===')
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
        print('默认管理员创建成功: admin / admin123')
    else:
        print(f'管理员已存在 ({admin_count} 个)，重置admin密码...')
        admin = db.query(Admin).filter(Admin.user_name == "admin").first()
        if admin:
            admin.password_hash = get_password_hash("admin123")
            db.commit()
            print('admin密码已重置为: admin123')
        else:
            print('未找到admin用户')

    print()
    print('=== 检查并修复患者账号 ===')
    patients = db.query(Patient).all()
    print(f'患者总数: {len(patients)}')
    for p in patients:
        if not p.password_hash:
            print(f'  患者 {p.phone} 无密码，设置默认密码 123456')
            p.password_hash = get_password_hash("123456")
    db.commit()
    print('患者账号修复完成')

    print()
    print('=== 检查医生账号 ===')
    doctors = db.query(Doctor).all()
    print(f'医生总数: {len(doctors)}')

    print()
    print('=== 初始化完成 ===')

except Exception as e:
    print(f'初始化失败: {e}')
    import traceback
    traceback.print_exc()
    db.rollback()
finally:
    db.close()
