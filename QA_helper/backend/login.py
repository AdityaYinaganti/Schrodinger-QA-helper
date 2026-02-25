import psycopg2
from passlib.context import CryptContext

# 1. Initialize the same hashing engine
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_user_login(email, plain_password):
    try:
        # 2. Connect using your specific laptop user
        conn = psycopg2.connect(
            dbname="testrail_db", 
            user="yinagant", 
            password="", 
            host="localhost"
        )
        cur = conn.cursor()

        # 3. Search for the user by email
        query = "SELECT user_id, name, password_hash FROM test_user WHERE email = %s"
        cur.execute(query, (email,))
        user_record = cur.fetchone()

        if user_record:
            user_id, name, stored_hash = user_record
            
            # 4. VERIFY the plain password against the stored hash
            if pwd_context.verify(plain_password, stored_hash):
                print(f"✅ Login Successful! Welcome, {name} (ID: {user_id})")
                return True
            else:
                print("❌ Login Failed: Incorrect password.")
                return False
        else:
            print("❌ Login Failed: User not found.")
            return False

    except Exception as e:
        print(f"⚠️ Error: {e}")
        return False
    finally:
        if cur: cur.close()
        if conn: conn.close()

# --- TEST THE LOGIN ---
if __name__ == "__main__":
    print("Testing Login System...")
    # Use the email you successfully registered earlier
    verify_user_login("test1@example.com", "SecurePassword123")