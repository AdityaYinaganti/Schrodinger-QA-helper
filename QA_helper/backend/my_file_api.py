import os
import requests
from requests.auth import HTTPBasicAuth
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import psycopg2
from psycopg2.extras import RealDictCursor

# Import your existing login verification function
from login import verify_user_login 

app = FastAPI()

# --- DYNAMIC PATH HANDLING ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PATH = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
templates = Jinja2Templates(directory=FRONTEND_PATH)

# --- DATABASE CONFIG ---
DB_PARAMS = {
    "dbname": "testrail_db",
    "user": "yinagant",
    "password": "",  
    "host": "localhost"
}

# --- JIRA CONFIG ---
JIRA_DOMAIN = "schrodinger.atlassian.net"  
JIRA_EMAIL = "aditya.yinaganti@schrodinger.com"      
JIRA_API_TOKEN = "<Your JIRA API TOKEN>"

def fetch_real_jira_updates(team_name=None):
    """Fetches real live ticket updates from Jira. Can optionally filter by a specific team."""
    url = f"https://{JIRA_DOMAIN}/rest/api/3/search/jql"
    
    # If a specific team is requested, only get their tickets. Otherwise, get the main shared ones.
    if team_name:
        jql = f"project = '{team_name}' ORDER BY updated DESC"
    else:
        jql = "project IN (LDIMPORT, SHARED) ORDER BY updated DESC" 
        
    QA_CLOSER_FIELD = "customfield_10142" 
    
    auth = HTTPBasicAuth(JIRA_EMAIL, JIRA_API_TOKEN)
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    payload = {
        "jql": jql,
        "maxResults": 5,
        "fields": ["summary", "status", "project", QA_CLOSER_FIELD]
    }

    try:
        response = requests.post(url, headers=headers, auth=auth, json=payload, timeout=5)
        if response.status_code == 200:
            data = response.json()
            updates = []
            for issue in data.get('issues', []):
                qa_closer_data = issue['fields'].get(QA_CLOSER_FIELD)
                closer_name = qa_closer_data.get('displayName', 'Not Assigned') if isinstance(qa_closer_data, dict) else (qa_closer_data if isinstance(qa_closer_data, str) else "Not Assigned")
                updates.append({
                    "team": issue['fields']['project']['name'],
                    "key": issue['key'],
                    "summary": issue['fields']['summary'],
                    "status": issue['fields']['status']['name'],
                    "url": f"https://{JIRA_DOMAIN}/browse/{issue['key']}",
                    "closer": closer_name
                })
            return updates
        else:
            print(f"Jira Error: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"Failed to connect to Jira: {e}")
        return []

def get_dashboard_data():
    conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM test_feature ORDER BY name;")
    features = cur.fetchall()
    try:
        cur.execute("SELECT * FROM test_team ORDER BY name;")
        teams = cur.fetchall()
    except Exception:
        teams = []
    cur.close()
    conn.close()
    return features, teams

# --- ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
async def login(username: str = Form(...), password: str = Form(...)):
    if verify_user_login(username, password):
        return RedirectResponse(url="/dashboard", status_code=303)
    return HTMLResponse(content="<h2>Login Failed</h2><a href='/'>Try Again</a>", status_code=401)

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    features, teams = get_dashboard_data()
    jira_updates = fetch_real_jira_updates()
    github_link = "https://github.com/schrodinger/livedesign/pulls?q=is%3Aopen+is%3Apr+label%3A%22automation+test%22"
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "features": features, 
        "teams": teams,
        "jira_updates": jira_updates, 
        "github_link": github_link
    })

@app.get("/team/{team_id}", response_class=HTMLResponse)
async def team_dashboard(request: Request, team_id: int):
    """Loads a dedicated dashboard for a specific team."""
    conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
    cur = conn.cursor()

    # Sidebar features
    cur.execute("SELECT * FROM test_feature ORDER BY name;")
    all_features = cur.fetchall()

    # Get the specific team details
    cur.execute("SELECT * FROM test_team WHERE team_id = %s;", (team_id,))
    team_data = cur.fetchone()

    # Get ONLY the features belonging to this specific team
    cur.execute("SELECT * FROM test_feature WHERE team_id = %s ORDER BY name;", (team_id,))
    team_features = cur.fetchall()

    cur.close()
    conn.close()

    if not team_data:
        return RedirectResponse(url="/dashboard")

    # Fetch Jira updates specifically for this team
    jira_updates = fetch_real_jira_updates(team_data['name'])

    return templates.TemplateResponse("team.html", {
        "request": request,
        "features": all_features,
        "team": team_data,
        "team_features": team_features,
        "jira_updates": jira_updates
    })

@app.post("/trigger_regression")
async def trigger_regression(environment: str = Form(...), ld_version: str = Form(...), run_id: str = Form(...)):
    run_name = f"Regression Pass {run_id} ({environment})"
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO test_run (ld_version, run_id, name, environment) 
            VALUES (%s, %s, %s, %s) 
            ON CONFLICT (ld_version, run_id) 
            DO UPDATE SET name = EXCLUDED.name, environment = EXCLUDED.environment;
        """, (ld_version, int(run_id), run_name, environment))
        
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"DB Error: {e}")
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/feature/{feature_id}", response_class=HTMLResponse)
async def feature_checklist(request: Request, feature_id: int):
    conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM test_feature ORDER BY name;")
    features = cur.fetchall()
    
    cur.execute("SELECT * FROM test_feature WHERE feature_id = %s;", (feature_id,))
    feature_data = cur.fetchone()
    owner = feature_data.get('owner', 'Unassigned') if feature_data else 'Unassigned'
    
    cur.execute("""
        SELECT case_id, sub_feature, description, is_archived 
        FROM test_cases WHERE feature_id = %s ORDER BY case_id;
    """, (feature_id,))
    test_cases = cur.fetchall()

    cur.execute("SELECT ld_version, run_id FROM test_run ORDER BY ld_version DESC, run_id DESC;")
    runs_data = cur.fetchall()
    
    versions_map = {}
    for row in runs_data:
        v = row['ld_version']
        r = row['run_id']
        if v not in versions_map:
            versions_map[v] = []
        versions_map[v].append(r)

    ld_versions = list(versions_map.keys())
    cur.close()
    conn.close()

    return templates.TemplateResponse("checklist.html", {
        "request": request, "features": features, "current_feature": feature_data,
        "owner": owner, "test_cases": test_cases, "ld_versions": ld_versions,
        "versions_map": versions_map
    })

@app.post("/submit_checklist")
async def submit_checklist(request: Request):
    form_data = await request.form()
    ld_version = form_data.get("ld_version")
    run_id = form_data.get("run_id")
    feature_id = form_data.get("feature_id")

    conn = psycopg2.connect(**DB_PARAMS)
    cur = conn.cursor()

    for key, value in form_data.items():
        if key.startswith("status_"):
            case_id = key.split("_")[1]
            status = value
            jira_link = form_data.get(f"jira_{case_id}", "")

            cur.execute("""
                INSERT INTO test_result (ld_version, run_id, case_id, status, jira_link)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ld_version, run_id, case_id) 
                DO UPDATE SET status = EXCLUDED.status, jira_link = EXCLUDED.jira_link;
            """, (ld_version, run_id, case_id, status, jira_link))

    conn.commit()
    cur.close()
    conn.close()
    return RedirectResponse(url=f"/feature/{feature_id}", status_code=303)

@app.get("/api/results")
async def get_test_results(ld_version: str, run_id: str, feature_id: int):
    try:
        conn = psycopg2.connect(**DB_PARAMS, cursor_factory=RealDictCursor)
        cur = conn.cursor()
        
        cur.execute("""
            SELECT tr.case_id, tr.status, tr.jira_link 
            FROM test_result tr
            JOIN test_cases tc ON tr.case_id = tc.case_id
            WHERE tr.ld_version = %s AND tr.run_id = %s AND tc.feature_id = %s;
        """, (ld_version, run_id, feature_id))
        
        results = cur.fetchall()
        cur.close()
        conn.close()
        return {str(row['case_id']): {"status": row['status'], "jira_link": row['jira_link']} for row in results}
    except Exception as e:
        print(f"Error fetching results: {e}")
        return {}

@app.post("/add_test_case")
async def add_test_case(feature_id: int = Form(...), sub_feature: str = Form(...), description: str = Form(...)):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("INSERT INTO test_cases (feature_id, sub_feature, description, is_archived) VALUES (%s, %s, %s, FALSE);", (feature_id, sub_feature, description))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
    return RedirectResponse(url=f"/feature/{feature_id}", status_code=303)

@app.post("/archive_test_case/{case_id}")
async def archive_test_case(case_id: int, feature_id: int = Form(...)):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cur = conn.cursor()
        cur.execute("UPDATE test_cases SET is_archived = TRUE WHERE case_id = %s;", (case_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception:
        pass
    return RedirectResponse(url=f"/feature/{feature_id}", status_code=303)

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
