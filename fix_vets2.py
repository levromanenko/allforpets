from sqlalchemy import create_engine, text

engine = create_engine("sqlite:///./petshelsi.db")
conn = engine.connect()

columns = [
    ("description", "TEXT"),
    ("rating_sum", "FLOAT DEFAULT 0"),
    ("rating_count", "INTEGER DEFAULT 0")
]

for col, typ in columns:
    try:
        conn.execute(text(f"ALTER TABLE vets ADD COLUMN {col} {typ}"))
        conn.commit()
        print(f"{col} added")
    except Exception as e:
        print(f"{col}:", e)

conn.close()
print("DONE")