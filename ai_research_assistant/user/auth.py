import bcrypt
from db.database import get_db_cursor, coerce_datetime

class UserAuth:
    @staticmethod
    def hash_password(password):
        """Hash a password using bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_password(password, hashed):
        """Verify a password against its hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    @staticmethod
    def create_user(username, password):
        """Create a new user"""
        try:
            # Check if user already exists
            with get_db_cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
                if cursor.fetchone():
                    return False, "Username already exists"
                
                # Create new user
                password_hash = UserAuth.hash_password(password)
                cursor.execute(
                    "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                    (username, password_hash)
                )
                user_id = cursor.fetchone()['id']
                return True, user_id
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def authenticate_user(username, password):
        """Authenticate a user"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT id, password_hash FROM users WHERE username = %s",
                    (username,)
                )
                user = cursor.fetchone()
                if user:
                    user['created_at'] = coerce_datetime(user.get('created_at'))
                
                if user and UserAuth.verify_password(password, user['password_hash']):
                    return True, user['id']
                return False, "Invalid username or password"
        except Exception as e:
            return False, str(e)
    
    @staticmethod
    def get_user_by_id(user_id):
        """Get user information by ID"""
        try:
            with get_db_cursor() as cursor:
                cursor.execute(
                    "SELECT id, username, created_at FROM users WHERE id = %s",
                    (user_id,)
                )
                user = cursor.fetchone()
                if user:
                    user['created_at'] = coerce_datetime(user.get('created_at'))
                return user
        except Exception as e:
            return None