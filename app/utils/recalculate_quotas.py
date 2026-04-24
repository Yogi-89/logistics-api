import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

def recalculate():
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        return

    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)

    engine = create_engine(url)
    
    try:
        with engine.connect() as conn:
            print("Successfully connected to database for quota recalculation.")
            
            # Get all users
            users = conn.execute(text("SELECT id, username, quota_used FROM users;")).fetchall()
            
            for user in users:
                user_id = user[0]
                username = user[1]
                old_quota = user[2] or 0
                
                # Calculate sum of total_requests from api_keys
                sum_query = text("SELECT SUM(total_requests) FROM api_keys WHERE user_id = :u_id;")
                new_quota = conn.execute(sum_query, {"u_id": user_id}).scalar() or 0
                
                if old_quota != new_quota:
                    print(f"Updating user '{username}' (ID: {user_id}): {old_quota} -> {new_quota}")
                    update_query = text("UPDATE users SET quota_used = :new_val WHERE id = :u_id;")
                    conn.execute(update_query, {"new_val": new_quota, "u_id": user_id})
                    conn.commit()
                else:
                    print(f"User '{username}' (ID: {user_id}) is already in sync ({new_quota}).")

            print("\nQuota recalculation complete!")
            
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    recalculate()
