from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def run_migration():
    """ Manually synchronizes the DB schema with the new security/identity requirements. """
    
    with engine.connect() as conn:
        print("Checking for required schema updates...")
        
        # 1. Update 'users' table
        try:
            # Check for phone_number
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR"))
            print("Verified 'phone_number' in users table.")
            
            # Check for is_verified
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE"))
            conn.execute(text("UPDATE users SET is_verified = TRUE WHERE is_verified IS NULL"))
            print("Verified 'is_verified' in users table.")
        except Exception as e:
            print(f"Error updating users table: {e}")

        # 2. Update 'transactions' table (Rename metadata to tx_metadata)
        try:
            # Check if 'metadata' exists and 'tx_metadata' doesn't
            cols = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='transactions' AND column_name IN ('metadata', 'tx_metadata')
            """)).fetchall()
            
            col_names = [r[0] for r in cols]
            if 'metadata' in col_names and 'tx_metadata' not in col_names:
                conn.execute(text("ALTER TABLE transactions RENAME COLUMN metadata TO tx_metadata"))
                print("Renamed 'metadata' to 'tx_metadata' in transactions table.")
            elif 'tx_metadata' not in col_names:
                conn.execute(text("ALTER TABLE transactions ADD COLUMN tx_metadata JSON"))
                print("Added 'tx_metadata' to transactions table.")
            else:
                print("Verified 'tx_metadata' in transactions table.")
        except Exception as e:
            print(f"Error updating transactions table: {e}")

        # 3. Create 'verification_codes' table if missing
        # (Usually create_all does this, but let's be safe)
        try:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS verification_codes (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    code VARCHAR,
                    channel VARCHAR,
                    type VARCHAR,
                    is_used BOOLEAN DEFAULT FALSE,
                    expires_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            print("Verified 'verification_codes' table.")
        except Exception as e:
            print(f"Error creating verification_codes table: {e}")

        conn.commit()
    
    print("\nMigration completed successfully!")

if __name__ == "__main__":
    run_migration()
