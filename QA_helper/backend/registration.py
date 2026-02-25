import psycopg2
from passlib.context import CryptContext

# 1. Setup the hashing engine
# This is the "logic" that creates the secure hash before saving to DB
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def register_user_in_db(name, email, plain_password):
    # --- STEP 1: HASH THE PASSWORD ---
    # This turns "mypassword123" into a secure scrambled string
    hashed_password = pwd_context.hash(plain_password)

    # --- STEP 2: CONNECT TO YOUR LOCAL DB ---
    try:
        conn = psycopg2.connect(
            dbname="testrail_db", 
            user="yinagant", 
            password="", # Update this!
            host="localhost"
        )
        cur = conn.cursor()

        # --- STEP 3: EXECUTE THE INSERT ---
        # We use the 'test_user' table from your SQL code
        insert_query = """
            INSERT INTO test_user (name, email, password_hash)
            VALUES (%s, %s, %s)
            RETURNING user_id;
        """
        
        cur.execute(insert_query, (name, email, hashed_password))
        user_id = cur.fetchone()[0]
        
        conn.commit()
        print(f"User created successfully! ID: {user_id}")
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

# Example: Run this once to create your first user
register_user_in_db("My Name", "test1@example.com", "SecurePassword123")