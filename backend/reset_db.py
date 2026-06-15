import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, init_db
from sqlalchemy import text

def reset_database():
    print("reseteando base de datos")
    try:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS fragmentos_ayudas CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS ayudas CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS historial_consultas CASCADE;"))
            conn.execute(text("DROP TABLE IF EXISTS usuarios CASCADE;"))
        
        print("Creando tablas...")
        init_db()
        
        import hashlib
        from app.database import SessionLocal
        from app.models import Usuario
        
        db = SessionLocal()
        pwd_hash = hashlib.sha256("admin".encode("utf-8")).hexdigest()
        admin_user = db.query(Usuario).filter(Usuario.username == "admin").first()
        if not admin_user:
            admin_user = Usuario(
                username="admin",
                password_hash=pwd_hash,
                role="admin",
                accessibility_profile="standard"
            )
            db.add(admin_user)
            db.commit()
            print("creando admin por defecto")
        db.close()
        
        print("DB LISTA")
    except Exception as e:
        print(e)

if __name__ == "__main__":
    reset_database()


