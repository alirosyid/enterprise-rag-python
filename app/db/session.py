import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

# Mengambil konfigurasi kredensial dari file .env
DB_USER = os.getenv("POSTGRES_USER", "admin")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "securepassword2026")
DB_NAME = os.getenv("POSTGRES_DB", "enterprise_state")

# URL Koneksi (Menggunakan 'postgres' sebagai host karena kita berada dalam satu jaringan Docker internal)
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@postgres:5432/{DB_NAME}"

# Inisialisasi Engine SQLAlchemy
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Generator sesi database untuk disuntikkan ke endpoint FastAPI
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()