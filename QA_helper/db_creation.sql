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
    owner VARCHAR(100), -- Dashboard UI can display the feature owner
    jira_epic VARCHAR(50)
);

CREATE TABLE test_cases (
    case_id SERIAL PRIMARY KEY,
    feature_id INT REFERENCES test_feature(feature_id) ON DELETE CASCADE,
    sub_feature VARCHAR(255),
    description TEXT,
    expected_outcome TEXT,
    created_by INT REFERENCES test_user(user_id),
    is_archived BOOLEAN DEFAULT FALSE, -- Allows soft-deleting in the UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 3. METADATA 
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
    ld_version VARCHAR(50) NOT NULL,  
    run_id INT NOT NULL,              
    name VARCHAR(255) NOT NULL,
    environment VARCHAR(50),          
    team_id INT REFERENCES test_team(team_id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (ld_version, run_id)  -- Composite Primary Key allowing identical run IDs across versions
);

CREATE TABLE test_result (
    result_id SERIAL PRIMARY KEY,
    ld_version VARCHAR(50) NOT NULL,  
    run_id INT NOT NULL,
    case_id INT REFERENCES test_cases(case_id) ON DELETE CASCADE,
    user_id INT REFERENCES test_user(user_id),
    status VARCHAR(20),               -- Stores plain text 'Pass', 'Fail', 'Not Run'
    jira_link VARCHAR(255),           
    actual_result TEXT,
    
    -- Composite Foreign Key linking back to test_run
    FOREIGN KEY (ld_version, run_id) REFERENCES test_run(ld_version, run_id) ON DELETE CASCADE,
    
    -- Ensures a specific test case only has ONE result per specific Run Pass
    UNIQUE(ld_version, run_id, case_id) 
);

-- 5. AUTOMATION TRACKING 
CREATE TABLE table_automation (
    automation_id SERIAL PRIMARY KEY,
    case_id INT REFERENCES test_cases(case_id) ON DELETE CASCADE,
    test_type VARCHAR(50),          -- e.g., 'Selenium' or 'API'
    test_name VARCHAR(255),         -- e.g., 'test_export_panel'
    automation_link VARCHAR(255),   -- e.g., 'https://github.com/...'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
