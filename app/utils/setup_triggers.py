import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

def setup_triggers():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL not found in .env")
        return

    engine = create_engine(database_url)

    trigger_sql = """
    -- 1. Create or Replace the Function
    CREATE OR REPLACE FUNCTION sync_user_quota_on_key_change()
    RETURNS TRIGGER AS $$
    BEGIN
        -- Handle INSERT
        IF (TG_OP = 'INSERT') THEN
            UPDATE users SET quota_used = quota_used + NEW.total_requests 
            WHERE id = NEW.user_id;
            
        -- Handle UPDATE (Propagate the difference)
        ELSIF (TG_OP = 'UPDATE') THEN
            IF (OLD.total_requests IS DISTINCT FROM NEW.total_requests) THEN
                UPDATE users SET quota_used = quota_used + (NEW.total_requests - OLD.total_requests) 
                WHERE id = NEW.user_id;
            END IF;
            
            -- If owner changed (rare, but professional to handle)
            IF (OLD.user_id IS DISTINCT FROM NEW.user_id) THEN
                UPDATE users SET quota_used = quota_used - OLD.total_requests WHERE id = OLD.user_id;
                UPDATE users SET quota_used = quota_used + NEW.total_requests WHERE id = NEW.user_id;
            END IF;

        -- Handle DELETE (Preserve usage in User's total by NOT subtracting)
        -- In some systems you might subtract here, but usually usage is historical.
        -- We will NOT subtract on delete to prevent 'resetting' quota by deleting keys.
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;

    -- 2. Drop existing trigger if exists
    DROP TRIGGER IF EXISTS trg_sync_user_quota ON api_keys;

    -- 3. Create the Trigger
    CREATE TRIGGER trg_sync_user_quota
    AFTER INSERT OR UPDATE ON api_keys
    FOR EACH ROW EXECUTE FUNCTION sync_user_quota_on_key_change();
    """

    try:
        with engine.connect() as conn:
            conn.execute(text(trigger_sql))
            conn.commit()
            print("Successfully deployed PostgreSQL triggers!")
    except Exception as e:
        print(f"Error deploying triggers: {e}")

if __name__ == "__main__":
    setup_triggers()
