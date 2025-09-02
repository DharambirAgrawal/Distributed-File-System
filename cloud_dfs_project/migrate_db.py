#!/usr/bin/env python3
"""
Database Migration Script
Adds user authentication to existing DFS database
"""
import os
import sys
from sqlalchemy import create_engine, text
from app import create_app
from app.models import db, User, File

def run_migration():
    """Run database migration to add user authentication"""
    print("🔄 Starting database migration...")
    
    # Create Flask app
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we're using the correct database URL
            print(f"📊 Database URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
            
            # Create connection for raw SQL commands
            with db.engine.connect() as connection:
                
                # Check if users table exists
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = 'public' 
                        AND table_name = 'users'
                    );
                """))
                users_table_exists = result.fetchone()[0]
                
                # Check if user_id column exists in files table
                result = connection.execute(text("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.columns 
                        WHERE table_schema = 'public' 
                        AND table_name = 'files' 
                        AND column_name = 'user_id'
                    );
                """))
                user_id_column_exists = result.fetchone()[0]
            
            print(f"📋 Users table exists: {users_table_exists}")
            print(f"📋 User_id column exists: {user_id_column_exists}")
            
            migrations_needed = []
            
            with db.engine.connect() as connection:
                # Begin transaction
                trans = connection.begin()
                
                try:
                    # Create users table if it doesn't exist
                    if not users_table_exists:
                        migrations_needed.append("Create users table")
                        print("📝 Creating users table...")
                        connection.execute(text("""
                            CREATE TABLE users (
                                id SERIAL PRIMARY KEY,
                                username VARCHAR(80) UNIQUE NOT NULL,
                                email VARCHAR(120) UNIQUE NOT NULL,
                                password_hash VARCHAR(255) NOT NULL,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                is_active BOOLEAN DEFAULT TRUE
                            );
                        """))
                        print("✅ Users table created successfully")
                    
                    # Add user_id column to files table if it doesn't exist
                    if not user_id_column_exists:
                        migrations_needed.append("Add user_id column to files table")
                        print("📝 Adding user_id column to files table...")
                        
                        # Add the column as nullable first
                        connection.execute(text("""
                            ALTER TABLE files 
                            ADD COLUMN user_id INTEGER;
                        """))
                        
                        # Add foreign key constraint
                        connection.execute(text("""
                            ALTER TABLE files 
                            ADD CONSTRAINT fk_files_user_id 
                            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
                        """))
                        
                        print("✅ User_id column added successfully")
                        
                        # Check if there are existing files without user_id
                        result = connection.execute(text("SELECT COUNT(*) FROM files WHERE user_id IS NULL;"))
                        orphaned_files = result.fetchone()[0]
                        
                        if orphaned_files > 0:
                            print(f"⚠️  Found {orphaned_files} existing files without user association")
                            print("📝 Creating default admin user for existing files...")
                            
                            # Create default admin user
                            from werkzeug.security import generate_password_hash
                            admin_password_hash = generate_password_hash('admin123')
                            
                            connection.execute(text("""
                                INSERT INTO users (username, email, password_hash)
                                VALUES ('admin', 'admin@dfs.local', :password_hash)
                                ON CONFLICT (username) DO NOTHING;
                            """), parameters={'password_hash': admin_password_hash})
                            
                            # Get admin user ID
                            result = connection.execute(text("SELECT id FROM users WHERE username = 'admin';"))
                            admin_id = result.fetchone()[0]
                            
                            # Assign existing files to admin user
                            connection.execute(text("""
                                UPDATE files 
                                SET user_id = :admin_id 
                                WHERE user_id IS NULL;
                            """), parameters={'admin_id': admin_id})
                            
                            print(f"✅ Assigned {orphaned_files} existing files to admin user")
                            print("🔑 Admin credentials - Username: admin, Password: admin123")
                    
                    # Commit transaction
                    trans.commit()
                    
                except Exception as e:
                    trans.rollback()
                    raise e
            
            if not migrations_needed:
                print("✅ Database is already up to date!")
            else:
                print(f"✅ Migration completed successfully!")
                print(f"📋 Applied migrations: {', '.join(migrations_needed)}")
            
            # Verify the migration
            print("\n🔍 Verifying migration...")
            with db.engine.connect() as connection:
                result = connection.execute(text("SELECT COUNT(*) FROM users;"))
                user_count = result.fetchone()[0]
                
                result = connection.execute(text("SELECT COUNT(*) FROM files;"))
                file_count = result.fetchone()[0]
                
                result = connection.execute(text("SELECT COUNT(*) FROM files WHERE user_id IS NOT NULL;"))
                files_with_users = result.fetchone()[0]
            
            print(f"📊 Total users: {user_count}")
            print(f"📊 Total files: {file_count}")
            print(f"📊 Files with user association: {files_with_users}")
            
            if file_count > 0 and files_with_users == file_count:
                print("✅ All files have user associations!")
            elif file_count == 0:
                print("ℹ️  No files in database yet")
            else:
                print("⚠️  Some files are missing user associations")
                
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            print(f"🔍 Error type: {type(e).__name__}")
            return False
    
    return True

if __name__ == "__main__":
    success = run_migration()
    if success:
        print("\n🎉 Database migration completed successfully!")
        print("🚀 You can now start the application with user authentication")
        sys.exit(0)
    else:
        print("\n💥 Database migration failed!")
        sys.exit(1)
