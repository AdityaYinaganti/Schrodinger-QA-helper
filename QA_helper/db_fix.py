import psycopg2

DB_PARAMS = {
    "dbname": "testrail_db",
    "user": "yinagant",
    "password": "",  
    "host": "localhost"
}

conn = psycopg2.connect(**DB_PARAMS)
cur = conn.cursor()

try:
    # Drop the old tables
    cur.execute("DROP TABLE IF EXISTS test_result;")
    cur.execute("DROP TABLE IF EXISTS test_run;")
    
    # Recreate test_run with a COMPOSITE Primary Key
    cur.execute("""
        CREATE TABLE test_run (
            ld_version VARCHAR(50) NOT NULL,
            run_id INT NOT NULL,
            name VARCHAR(100),
            environment VARCHAR(50),
            PRIMARY KEY (ld_version, run_id)
        );
    """)
    
    # Recreate test_result linking to both ld_version AND run_id
    cur.execute("""
        CREATE TABLE test_result (
            result_id SERIAL PRIMARY KEY,
            ld_version VARCHAR(50) NOT NULL,
            run_id INT NOT NULL,
            case_id INT NOT NULL,
            status VARCHAR(20),
            jira_link VARCHAR(255),
            UNIQUE(ld_version, run_id, case_id)
        );
    """)
    conn.commit()
    print("✅ Database fixed! You can now have duplicate Run IDs across different LD Versions.")
except Exception as e:
    print(f"⚠️ Error: {e}")
finally:
    cur.close()
    conn.close()