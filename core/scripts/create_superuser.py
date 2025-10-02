from app.database import SessionLocal
from app.models import User
from core.auth import hash_password

# Create default superuser (run once)
def create_superuser():
    db = SessionLocal()
    try:
        superuser = db.query(User).filter(User.is_superuser == True).first()
        if not superuser:
            default_superuser = User(
                email="admin@example.com",
                hashed_password=hash_password("admin123"),
                is_superuser=True,
                is_staff=True,
            )
            db.add(default_superuser)
            db.commit()
            print("✅ Default superuser created: admin@example.com / admin123")
        else:
            print("⚠️ Superuser already exists, skipping.")
    finally:
        db.close()

if __name__ == "__main__":
    create_superuser()