from sqlalchemy import create_engine, text
e = create_engine('sqlite:///./petshelsi.db')
c = e.connect()
try:
    c.execute(text("ALTER TABLE appointments ADD COLUMN status TEXT DEFAULT 'pending'"))
    c.commit()
    print('OK')
except Exception as x:
    print(x)
c.close()