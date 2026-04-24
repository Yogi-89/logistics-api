import os
import psycopg2
from urllib.parse import urlparse

def get_stats():
    # Read .env manually
    env_vars = {}
    env_path = r"C:\Users\Developer\Documents\Semester 8\pemograman_api\logistics-api\.env"
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            for line in f:
                if "=" in line:
                    key, value = line.strip().split("=", 1)
                    env_vars[key] = value

    db_url = env_vars.get('DATABASE_URL')
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    try:
        # Parse URL for psycopg2
        result = urlparse(db_url)
        username = result.username
        password = result.password
        database = result.path[1:]
        hostname = result.hostname
        port = result.port

        print(f"Connecting to: {hostname}:{port}/{database} as {username}")

        conn = psycopg2.connect(
            database=database,
            user=username,
            password=password,
            host=hostname,
            port=port
        )
        cur = conn.cursor()
        
        print("\n=== SYSTEM AUDIT FOR 'whooo' ===")
        
        # 1. User Stats
        cur.execute("SELECT id, quota_limit, quota_used, is_verified FROM users WHERE username = 'whooo'")
        user = cur.fetchone()
        if not user:
            print("User 'whooo' not found.")
            return
        
        user_id, q_limit, q_used, is_verified = user
        print(f"User ID: {user_id}")
        print(f"Verified: {is_verified}")
        print(f"Remaining Quota: {int(q_limit) - int(q_used)} (Limit: {q_limit}, Used: {q_used})")
        
        # 2. Key Stats
        cur.execute("SELECT label, key, total_requests, is_active FROM api_keys WHERE user_id = %s", (user_id,))
        keys = cur.fetchall()
        print(f"\nActive Keys: {len(keys)}")
        for k in keys:
            status = "ACTIVE" if k[3] else "INACTIVE"
            print(f"- {k[0].ljust(12)} | Usage: {str(k[2]).ljust(5)} | Status: {status}")
            
        # 3. Billing Stats
        cur.execute("SELECT count(*) FROM transactions WHERE user_id = %s", (user_id,))
        total_tx = cur.fetchone()[0]
        cur.execute("SELECT status, count(*) FROM transactions WHERE user_id = %s GROUP BY status", (user_id,))
        tx_stats = cur.fetchall()
        print(f"\nTotal Transactions: {total_tx}")
        for s in tx_stats:
            print(f"- {s[0].ljust(12)}: {s[1]}")

        # 4. Scalability Audit: Indexes
        print("\n=== SCALABILITY AUDIT: INDEXES ===")
        cur.execute("""
            SELECT tablename, indexname 
            FROM pg_indexes 
            WHERE schemaname = 'public' 
            AND tablename IN ('users', 'api_keys', 'api_keys_usage', 'transactions', 'cities', 'couriers', 'tracking')
            ORDER BY tablename;
        """)
        indexes = cur.fetchall()
        for idx in indexes:
            print(f"Table: {idx[0].ljust(15)} | Index: {idx[1]}")

        # 5. Scalability Audit: Relations & Row counts
        print("\n=== SCALABILITY AUDIT: TABLE SIZES ===")
        for table in ['cities', 'couriers', 'tracking']:
            cur.execute(f"SELECT count(*) FROM {table}")
            print(f"- {table.ljust(10)}: {cur.fetchone()[0]} rows")

        cur.close()
        conn.close()
        print("\n=== AUDIT COMPLETE ===")
    except Exception as e:
        print(f"Audit error: {e}")

if __name__ == "__main__":
    get_stats()
