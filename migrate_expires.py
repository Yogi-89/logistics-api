from app.database import engine
from sqlalchemy import text

with engine.connect() as conn:
    conn.execute(text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS expires_at TIMESTAMP"))
    conn.commit()
    print("Migration done: expires_at column added to transactions")
