import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def migrate():
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/logistics_api")
    print(f"Connecting to: {db_url}")
    
    try:
        conn = psycopg2.connect(db_url)
        cur = conn.cursor()
        
        # Check if column exists
        cur.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='transactions' AND column_name='payment_method';
        """)
        
        if not cur.fetchone():
            print("Adding 'payment_method' column to 'transactions' table...")
            cur.execute("ALTER TABLE transactions ADD COLUMN payment_method VARCHAR DEFAULT 'midtrans';")
            conn.commit()
            print("Migration successful.")
        else:
            print("Column 'payment_method' already exists.")
            
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Migration failed: {e}")

if __name__ == "__main__":
    migrate()
