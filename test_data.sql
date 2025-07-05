-- Test data for production database
-- Creates committees and hearings tables if they don't exist, then populates test data

-- Create committees table
CREATE TABLE IF NOT EXISTS committees (
    committee_code VARCHAR(10) PRIMARY KEY,
    committee_name VARCHAR(255) NOT NULL,
    chamber VARCHAR(10) NOT NULL,
    total_members INTEGER,
    majority_party VARCHAR(20),
    minority_party VARCHAR(20),
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create hearings table
CREATE TABLE IF NOT EXISTS hearings (
    hearing_id VARCHAR(100) PRIMARY KEY,
    committee_code VARCHAR(10) NOT NULL,
    title VARCHAR(500) NOT NULL,
    date DATE,
    url VARCHAR(500),
    status VARCHAR(20) DEFAULT 'discovered',
    audio_available BOOLEAN DEFAULT FALSE,
    transcript_available BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert test committees
INSERT INTO committees (committee_code, committee_name, chamber, total_members, majority_party, minority_party, metadata)
VALUES 
    ('SCOM', 'Senate Committee on Commerce, Science, and Transportation', 'Senate', 28, 'Democrat', 'Republican', '{"description": "Committee with jurisdiction over commerce, science, and transportation", "website": "https://www.commerce.senate.gov", "isvp_compatible": true}'),
    ('SSCI', 'Senate Select Committee on Intelligence', 'Senate', 21, 'Democrat', 'Republican', '{"description": "Select committee overseeing intelligence community", "website": "https://www.intelligence.senate.gov", "isvp_compatible": true}'),
    ('SSJU', 'Senate Committee on the Judiciary', 'Senate', 22, 'Democrat', 'Republican', '{"description": "Committee with jurisdiction over federal judiciary", "website": "https://www.judiciary.senate.gov", "isvp_compatible": true}')
ON CONFLICT (committee_code) DO UPDATE SET
    committee_name = EXCLUDED.committee_name,
    chamber = EXCLUDED.chamber,
    total_members = EXCLUDED.total_members,
    majority_party = EXCLUDED.majority_party,
    minority_party = EXCLUDED.minority_party,
    metadata = EXCLUDED.metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Insert test hearings
INSERT INTO hearings (hearing_id, committee_code, title, date, url, status, audio_available, transcript_available, metadata)
VALUES 
    ('SCOM-2025-06-25-executive-session-12', 'SCOM', 'Executive Session 12', '2025-06-25', 'https://www.commerce.senate.gov/2025/6/executive-session-12', 'discovered', true, false, '{"duration": "44:42", "committee": "Commerce, Science, and Transportation", "session_type": "Executive Session", "description": "Executive session to consider nominations and other business"}'),
    ('SSCI-2025-06-20-intelligence-briefing', 'SSCI', 'Intelligence Community Briefing', '2025-06-20', 'https://www.intelligence.senate.gov/hearings/intelligence-community-briefing', 'discovered', true, false, '{"duration": "2:15:30", "committee": "Intelligence", "session_type": "Briefing", "description": "Classified briefing on current intelligence matters"}'),
    ('SSJU-2025-06-15-judicial-nominations', 'SSJU', 'Judicial Nominations Hearing', '2025-06-15', 'https://www.judiciary.senate.gov/meetings/judicial-nominations-hearing', 'discovered', true, false, '{"duration": "3:45:20", "committee": "Judiciary", "session_type": "Confirmation Hearing", "description": "Hearing to consider federal judicial nominees"}')
ON CONFLICT (hearing_id) DO UPDATE SET
    committee_code = EXCLUDED.committee_code,
    title = EXCLUDED.title,
    date = EXCLUDED.date,
    url = EXCLUDED.url,
    status = EXCLUDED.status,
    audio_available = EXCLUDED.audio_available,
    transcript_available = EXCLUDED.transcript_available,
    metadata = EXCLUDED.metadata,
    updated_at = CURRENT_TIMESTAMP;

-- Verify the data
SELECT 'Committees' as table_name, COUNT(*) as count FROM committees
UNION ALL
SELECT 'Hearings' as table_name, COUNT(*) as count FROM hearings;