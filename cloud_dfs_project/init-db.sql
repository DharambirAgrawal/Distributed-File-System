-- Initialize the database for Distributed File System
-- This file is executed when the PostgreSQL container starts for the first time

-- Create extension for UUID generation (if needed)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(80) UNIQUE NOT NULL,
    email VARCHAR(120) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);

-- Create files table
CREATE TABLE IF NOT EXISTS files (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_size BIGINT NOT NULL,
    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    chunk_count INTEGER NOT NULL,
    file_hash VARCHAR(255),
    content_type VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    metadata TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_files_user_id ON files(user_id);
CREATE INDEX IF NOT EXISTS idx_files_filename ON files(filename);
CREATE INDEX IF NOT EXISTS idx_files_upload_date ON files(upload_date);

-- Create a default admin user (password: admin123 - change in production!)
INSERT INTO users (username, email, password_hash, created_at, is_active) 
VALUES ('admin', 'admin@dfs.local', 'scrypt:32768:8:1$LM4o6yY0CkdUhLaE$74b5de2b9b5f45f4e3c8d1a6e9f5b8c3d2a7e9f4b5c8d1a6e9f5b8c3d2a7e9f4b5c8d1a6e9f5b8c3d2a7e9f4', CURRENT_TIMESTAMP, TRUE)
ON CONFLICT (username) DO NOTHING;

-- Log that initialization is complete
DO $$
BEGIN
    RAISE NOTICE 'DFS Database initialization completed successfully!';
    RAISE NOTICE 'Tables created: users, files';
    RAISE NOTICE 'Default admin user created (change password in production!)';
END $$;
