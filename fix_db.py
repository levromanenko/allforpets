from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./petshelsi.db")
conn = engine.connect()

try:
    conn.execute(text("ALTER TABLE users ADD COLUMN role VARCHAR DEFAULT 'user'"))
    conn.commit()
    print("role added")
except Exception as e:
    print("role:", e)

try:
    conn.execute(text("ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT 0"))
    conn.commit()
    print("is_blocked added")
except Exception as e:
    print("is_blocked:", e)

conn.execute(text("UPDATE users SET role = 'admin' WHERE id = 1"))
conn.commit()
print("admin set for id=1")

conn.close()
print("DONE")