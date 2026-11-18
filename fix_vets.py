from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./petshelsi.db")
conn = engine.connect()

try:
    conn.execute(text("ALTER TABLE vets ADD COLUMN animal_type VARCHAR"))
    conn.commit()
    print("animal_type added")
except Exception as e:
    print("animal_type:", e)

try:
    conn.execute(text("ALTER TABLE vets ADD COLUMN service VARCHAR"))
    conn.commit()
    print("service added")
except Exception as e:
    print("service:", e)

conn.close()
print("DONE")