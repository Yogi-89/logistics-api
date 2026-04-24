import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def sync_db():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        return

    # Handle postgresql:// vs postgresql+psycopg2://
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(url)
    
    # Define columns to sync for each table
    schema_updates = {
        "users": [
            ("phone_number", "VARCHAR"),
            ("is_verified", "BOOLEAN DEFAULT FALSE"),
            ("quota_limit", "INTEGER DEFAULT 1000"),
            ("quota_used", "INTEGER DEFAULT 0")
        ],
        "transactions": [
            ("payment_method", "VARCHAR DEFAULT 'midtrans'"),
            ("tx_metadata", "JSON"),
            ("tx_hash", "VARCHAR"),
            ("status_reason", "VARCHAR")
        ]
    }
    
    try:
        with engine.connect() as conn:
            print("Successfully connected to database.")
            
            for table_name, columns in schema_updates.items():
                print(f"\nChecking table '{table_name}'...")
                for col_name, col_type in columns:
                    try:
                        # Check if column exists
                        check_query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='{col_name}';")
                        if not conn.execute(check_query).fetchone():
                            print(f"  Adding column '{col_name}'...")
                            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};"))
                            # Post-add data normalization
                            if col_name == "is_verified":
                                conn.execute(text(f"UPDATE {table_name} SET is_verified = TRUE WHERE is_verified IS NULL;"))
                        
                            conn.commit()
                        else:
                            print(f"  Column '{col_name}' already exists.")
                            # Ensure nullability for specific columns
                            if table_name == "transactions" and col_name == "api_key_id":
                                conn.execute(text("ALTER TABLE transactions ALTER COLUMN api_key_id DROP NOT NULL;"))
                                conn.commit()
                    except Exception as col_err:
                        print(f"  Error processing {table_name}.{col_name}: {col_err}")

            print("\nDatabase synchronization complete!")
            
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    sync_db()
