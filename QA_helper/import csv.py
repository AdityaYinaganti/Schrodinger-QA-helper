import csv
import psycopg2

def migrate_test_cases(csv_filepath):
    try:
        conn = psycopg2.connect(
            dbname="testrail_db", 
            user="yinagant", 
            password="", 
            host="localhost"
        )
        cur = conn.cursor()

        # FIX: Use csv_filepath instead of hardcoded string
        with open(csv_filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            for row in reader:
                # SAFETY: Skip row if 'Feature' is missing
                if not row.get('Feature'):
                    continue

                feature_name = row['Feature']
                
                # Ensure the 'name' column is UNIQUE in your DB for this to work
                cur.execute("""
                    INSERT INTO test_feature (name) VALUES (%s) 
                    ON CONFLICT (name) DO NOTHING 
                    RETURNING feature_id;
                """, (feature_name,))
                
                result = cur.fetchone()
                
                if result:
                    feature_id = result[0]
                else:
                    cur.execute("SELECT feature_id FROM test_feature WHERE name = %s;", (feature_name,))
                    feature_id = cur.fetchone()[0]

                sub_feature = row['SubFeature']
                case_name = row['Test Case(s)']
                expected = row.get('Expected Outcome', 'See instructions')

                cur.execute("""
                    INSERT INTO test_cases (feature_id, sub_feature, description, expected_outcome)
                    VALUES (%s, %s, %s, %s)
                """, (feature_id, sub_feature, case_name, expected))

        conn.commit()
        print(f"✅ Migration Complete: {csv_filepath} transferred to DB.")

    except Exception as e:
        print(f"❌ Migration Error: {e}")
    finally:
        if 'cur' in locals(): cur.close()
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    # Ensure this file exists in your folder!
    migrate_test_cases('test_data.csv')