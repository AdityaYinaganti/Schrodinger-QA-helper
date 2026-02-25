import pandas as pd
import psycopg2
import sys

def sync_to_db(cases_csv, links_csv):
    conn = psycopg2.connect(dbname="testrail_db", user="yinagant", host="localhost")
    cur = conn.cursor()

    # Part A: Test Cases
    df_cases = pd.read_csv(cases_csv)
    for _, row in df_cases.iterrows():
        cur.execute("INSERT INTO test_feature (name) VALUES (%s) ON CONFLICT (name) DO NOTHING RETURNING feature_id;", (row['Feature'],))
        res = cur.fetchone()
        f_id = res[0] if res else cur.execute("SELECT feature_id FROM test_feature WHERE name=%s", (row['Feature'],)) or cur.fetchone()[0]
        cur.execute("INSERT INTO test_cases (feature_id, sub_feature, description) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING;", 
                    (f_id, row['SubFeature'], row['TestCase']))

    # Part B: Automation Links
    df_links = pd.read_csv(links_csv)
    for _, row in df_links.iterrows():
        cur.execute("SELECT case_id FROM test_cases WHERE description = %s LIMIT 1;", (row['TestCase'],))
        res = cur.fetchone()
        if res:
            cur.execute("INSERT INTO table_automation (case_id, test_type, test_name, automation_link) VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING;", 
                        (res[0], row['Type'], row['TestName'], row['Link']))

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Step 3 Complete: Database synced successfully.")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python 3_db_sync.py <cleaned_cases.csv> <automation_links.csv>")
    else:
        sync_to_db(sys.argv[1], sys.argv[2])