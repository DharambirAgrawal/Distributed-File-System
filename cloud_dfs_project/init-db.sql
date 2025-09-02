-- Initialize the database with any required extensions or initial data
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extension for UUID generation (if needed in future)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create a schema for the DFS application (optional)
-- CREATE SCHEMA IF NOT EXISTS dfs;

-- Any additional initialization can be added here
-- For example, creating indexes, additional tables, or sample data

-- Log that initialization is complete
DO $$
BEGIN
    RAISE NOTICE 'DFS Database initialization completed successfully!';
END $$;
