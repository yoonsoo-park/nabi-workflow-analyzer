-- File: scripts/setup_db.sql
-- Description: Initial SQL script for setting up the n8n_workflow_analyzer PostgreSQL database.
-- Note: Database creation itself (e.g., 'CREATE DATABASE n8n_analyzer_db;') is typically done
-- via psql command `createdb n8n_analyzer_db` or through a database management tool by a superuser.

-- 1. (Optional) Create a dedicated user for the application
-- Replace 'your_username' and 'your_password' with secure credentials.
-- CREATE USER n8n_app_user WITH PASSWORD 'your_secure_password';

-- Grant connect access to the (assumed to be created) database:
-- GRANT CONNECT ON DATABASE n8n_analyzer_db TO n8n_app_user;


-- 2. Define initial table schemas (these will likely evolve)

-- Example: Table to store basic workflow information
CREATE TABLE IF NOT EXISTS workflows (
    id SERIAL PRIMARY KEY,            -- Unique identifier for the workflow entry in this DB
    n8n_workflow_id VARCHAR(255) UNIQUE, -- The actual ID from the n8n workflow JSON
    name TEXT,                        -- Name of the workflow
    file_path TEXT UNIQUE,            -- Path to the source JSON file
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Add other metadata fields as needed, e.g., active status, tags from JSON
    raw_json JSONB                    -- Store the original JSON, if desired
);

-- Example: Table to store information about each node in a workflow
CREATE TABLE IF NOT EXISTS workflow_nodes (
    id SERIAL PRIMARY KEY,
    workflow_db_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE, -- Foreign key to workflows table
    n8n_node_id VARCHAR(255),         -- The 'id' field from the node JSON (e.g., "SET_ITEM_1")
    node_type VARCHAR(255),           -- The 'type' field (e.g., "n8n-nodes-base.set")
    name TEXT,                        -- User-defined name of the node
    parameters JSONB,                 -- Node-specific parameters
    position_x INTEGER,
    position_y INTEGER,
    -- Add other node-specific fields as needed
    UNIQUE (workflow_db_id, n8n_node_id) -- Ensure node ID is unique within a workflow
);

-- Example: Table to store connections between nodes
CREATE TABLE IF NOT EXISTS workflow_connections (
    id SERIAL PRIMARY KEY,
    workflow_db_id INTEGER REFERENCES workflows(id) ON DELETE CASCADE,
    source_node_n8n_id VARCHAR(255),    -- n8n_node_id of the source node
    source_port_name VARCHAR(255),      -- e.g., "main", "port1"
    target_node_n8n_id VARCHAR(255),    -- n8n_node_id of the target node
    target_port_name VARCHAR(255)       -- e.g., "main", "input1"
    -- Foreign keys to workflow_nodes can be added for integrity if n8n_node_ids are globally unique
    -- or if a composite key (workflow_db_id, n8n_node_id) is used for nodes.
);

-- Add more tables as needed for patterns, analysis results, etc.

-- Grant permissions to the application user for the created tables
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE workflows TO n8n_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE workflow_nodes TO n8n_app_user;
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE workflow_connections TO n8n_app_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO n8n_app_user; -- For SERIAL primary keys

-- Placeholder for future migrations or more detailed schema definitions.
COMMENT ON TABLE workflows IS 'Stores top-level information about each n8n workflow processed.';
COMMENT ON TABLE workflow_nodes IS 'Stores details about each node within an n8n workflow.';
COMMENT ON TABLE workflow_connections IS 'Stores information about connections between nodes in workflows.';

-- End of initial setup script.
