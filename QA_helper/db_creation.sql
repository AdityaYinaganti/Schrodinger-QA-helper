-- 1. ACCESS CONTROL
CREATE TABLE test_user (
    user_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE test_team (
    team_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_by_user_id INT REFERENCES test_user(user_id)
);

-- 2. THE TEST REPOSITORY (Library)
CREATE TABLE test_feature (
    feature_id SERIAL PRIMARY KEY,
    team_id INT REFERENCES test_team(team_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    owner VARCHAR(100), -- NEW: Added so the dashboard UI can display the feature owner
    jira_epic VARCHAR(50)
);

CREATE TABLE test_cases (
    case_id SERIAL PRIMARY KEY,
    feature_id INT REFERENCES test_feature(feature_id) ON DELETE CASCADE,
    sub_feature VARCHAR(255),
    description TEXT,
    expected_outcome TEXT,
    created_by INT REFERENCES test_user(user_id),
    is_archived BOOLEAN DEFAULT FALSE, -- Retained: Allows soft-deleting in the UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. METADATA 
-- (Note: These tables are preserved for future complex joins, though our current 
-- app architecture writes text directly to test_run and test_result for speed).
CREATE TABLE test_environment (
    env_id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE test_status (
    status_id SERIAL PRIMARY KEY,
    label VARCHAR(20) NOT NULL,
    is_final BOOLEAN DEFAULT FALSE
);

-- 4. TEST EXECUTION (Runs & Results)
CREATE TABLE test_run (
    ld_version VARCHAR(50) NOT NULL,  -- UPDATED: Now part of the Primary Key
    run_id INT NOT NULL,              -- UPDATED: Changed from SERIAL to INT to allow custom inputs
    name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),          -- UPDATED: Stores the env string directly
    team_id INT REFERENCES test_team(team_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ld_version, run_id)  -- NEW: Composite Primary Key
);

CREATE TABLE test_result (
    result_id SERIAL PRIMARY KEY,
    ld_version VARCHAR(50) NOT NULL,  -- NEW: Required to link to test_run
    run_id INT NOT NULL,
    case_id INT REFERENCES test_cases(case_id) ON DELETE CASCADE,
    user_id INT REFERENCES test_user(user_id),
    status VARCHAR(20),               -- UPDATED: Changed from status_id to store "Pass"/"Fail" directly
    jira_link VARCHAR(255),           -- UPDATED: Renamed defect_id to jira_link to match app logic
    actual_result TEXT,
    
    -- NEW: Composite Foreign Key linking back to test_run
    FOREIGN KEY (ld_version, run_id) REFERENCES test_run(ld_version, run_id) ON DELETE CASCADE,
    
    -- NEW: Ensures a specific test case only has ONE result per specific Run Pass
    UNIQUE(ld_version, run_id, case_id) 
);