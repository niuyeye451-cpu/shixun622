import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import Patient, Doctor, Admin, Department, Hospital
from app.utils import generate_id, get_password_hash

def init_sqlite_db():
    print('=' * 60)
    print('  初始化 SQLite 数据库')
    print('=' * 60)
    print()

    print('【1/4】创建所有表结构...')
    Base.metadata.create_all(bind=engine)
    print('  ✅ 表结构创建完成')
    print()

    db = SessionLocal()

    print('【2/4】初始化默认管理员账号...')
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
        db.refresh(default_admin)
        print(f'  ✅ 默认管理员创建成功: admin / admin123')
        print(f'     管理员ID: {default_admin.admin_id}')
    else:
        print(f'  ℹ️  管理员已存在 ({admin_count} 个)，跳过创建')
    print()

    print('【3/4】初始化测试医生账号...')
    doctor_count = db.query(Doctor).count()
    if doctor_count == 0:
        test_doctor = Doctor(
            doctor_id=generate_id("doc_"),
            user_name="doctor01",
            phone="13900002222",
            password_hash=get_password_hash("123456"),
            department="内科",
            title="主治医师",
            hospital="市人民医院",
            is_first_login=True,
            status=1
        )
        db.add(test_doctor)
        db.commit()
        db.refresh(test_doctor)
        print(f'  ✅ 测试医生创建成功: doctor01 / 123456')
        print(f'     医生ID: {test_doctor.doctor_id}')
    else:
        print(f'  ℹ️  医生已存在 ({doctor_count} 个)，跳过创建')
    print()

    print('【4/4】初始化测试患者账号...')
    patient_count = db.query(Patient).count()
    if patient_count == 0:
        test_patient = Patient(
            patient_id=generate_id("pat_"),
            user_name="测试用户",
            phone="13900001111",
            password_hash=get_password_hash("123456"),
            gender="男",
            age=30,
            status=1
        )
        db.add(test_patient)
        db.commit()
        db.refresh(test_patient)
        print(f'  ✅ 测试患者创建成功: 13900001111 / 123456')
        print(f'     患者ID: {test_patient.patient_id}')
    else:
        print(f'  ℹ️  患者已存在 ({patient_count} 个)，跳过创建')
    print()

    print('=' * 60)
    print('  SQLite 数据库初始化完成！')
    print('=' * 60)
    print()
    print('数据库文件位置: db/medical_system.db')
    print()
    print('默认账号:')
    print('  管理员: admin / admin123')
    print('  医生:   doctor01 / 123456')
    print('  患者:   13900001111 / 123456')
    print()

    db.close()

if __name__ == "__main__":
    init_sqlite_db()
