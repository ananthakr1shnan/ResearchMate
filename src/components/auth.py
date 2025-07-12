"""
Authentication and authorization utilities
"""

import jwt
import bcrypt
import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps

# Import Flask components only when available
try:
    from flask import request, jsonify, session, redirect, url_for
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    request = None
    jsonify = None
    session = None
    redirect = None
    url_for = None

class AuthManager:
    def __init__(self, secret_key: str = None):
        self.secret_key = secret_key or os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
        self.users_file = 'data/users.json'
        self.active_sessions = {}  # Track active sessions for security
        self.session_file = 'data/active_sessions.json'
        self.ensure_users_file()
    
    def ensure_users_file(self):
        """Ensure users file exists"""
        os.makedirs('data', exist_ok=True)
        if not os.path.exists(self.users_file):
            with open(self.users_file, 'w') as f:
                json.dump({}, f)
    
    def hash_password(self, password: str) -> str:
        """Hash password with bcrypt"""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    
    def load_users(self) -> Dict[str, Any]:
        """Load users from file"""
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_users(self, users: Dict[str, Any]):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(users, f, indent=2)
    
    def create_user(self, username: str, email: str, password: str) -> Dict[str, Any]:
        """Create a new user"""
        users = self.load_users()
        
        if username in users:
            return {'success': False, 'error': 'Username already exists'}
        
        # Check if email already exists
        for user_data in users.values():
            if user_data.get('email') == email:
                return {'success': False, 'error': 'Email already registered'}
        
        # Create user
        user_id = f"user_{len(users) + 1}"
        users[username] = {
            'user_id': user_id,
            'email': email,
            'password_hash': self.hash_password(password),
            'created_at': datetime.now().isoformat(),
            'is_active': True
        }
        
        self.save_users(users)
        return {'success': True, 'user_id': user_id}
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials"""
        users = self.load_users()
        
        if username not in users:
            return {'success': False, 'error': 'Invalid username or password'}
        
        user = users[username]
        if not self.verify_password(password, user['password_hash']):
            return {'success': False, 'error': 'Invalid username or password'}
        
        if not user.get('is_active', True):
            return {'success': False, 'error': 'Account is disabled'}
        
        # Generate JWT token with shorter expiration for security
        token = jwt.encode({
            'user_id': user['user_id'],
            'username': username,
            'exp': datetime.utcnow() + timedelta(hours=8)  # 8 hours instead of 7 days
        }, self.secret_key, algorithm='HS256')
        
        # Track active session
        self.add_active_session(user['user_id'], token)
        
        return {
            'success': True,
            'token': token,
            'user_id': user['user_id'],
            'username': username
        }
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token and check active session"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            user_id = payload.get('user_id')
            
            # Check if session is still active
            if not self.is_session_active(user_id, token):
                return None
            
            # Update session activity
            self.update_session_activity(user_id)
            
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def get_current_user(self, request_obj) -> Optional[Dict[str, Any]]:
        """Get current user from request"""
        if not FLASK_AVAILABLE or not request_obj:
            return None
            
        # Try Authorization header first
        auth_header = request_obj.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            return self.verify_token(token)
        
        # Try session
        if session:
            token = session.get('auth_token')
            if token:
                return self.verify_token(token)
        
        return None
    
    def create_default_admin(self) -> Dict[str, Any]:
        """Create default admin user if it doesn't exist"""
        users = self.load_users()
        
        admin_username = "admin"
        admin_user_id = "admin_user"
        
        # Check if admin already exists (by username or user_id)
        if admin_username in users:
            return {'success': True, 'message': 'Admin user already exists'}
        
        # Check if user_id already exists
        for user_data in users.values():
            if user_data.get('user_id') == admin_user_id:
                return {'success': True, 'message': 'Admin user ID already exists'}
        
        # Create admin user
        users[admin_username] = {
            'user_id': admin_user_id,
            'email': 'admin@researchmate.local',
            'password_hash': self.hash_password('admin123'),  # Default password
            'created_at': datetime.now().isoformat(),
            'is_active': True,
            'is_admin': True
        }
        
        self.save_users(users)
        return {
            'success': True, 
            'message': 'Default admin user created',
            'username': admin_username,
            'password': 'admin123',
            'note': 'Please change the default password after first login'
        }
    
    def load_active_sessions(self) -> Dict[str, Any]:
        """Load active sessions from file"""
        try:
            if os.path.exists(self.session_file):
                with open(self.session_file, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_active_sessions(self, sessions: Dict[str, Any]):
        """Save active sessions to file"""
        try:
            with open(self.session_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except:
            pass
    
    def add_active_session(self, user_id: str, token: str):
        """Add an active session"""
        sessions = self.load_active_sessions()
        sessions[user_id] = {
            'token': token,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat()
        }
        self.save_active_sessions(sessions)
    
    def remove_active_session(self, user_id: str):
        """Remove an active session"""
        sessions = self.load_active_sessions()
        if user_id in sessions:
            del sessions[user_id]
            self.save_active_sessions(sessions)
    
    def is_session_active(self, user_id: str, token: str) -> bool:
        """Check if a session is active"""
        sessions = self.load_active_sessions()
        if user_id not in sessions:
            return False
        
        session = sessions[user_id]
        if session.get('token') != token:
            return False
        
        # Check if session is expired (8 hours)
        created_at = datetime.fromisoformat(session['created_at'])
        if datetime.now() - created_at > timedelta(hours=8):
            self.remove_active_session(user_id)
            return False
        
        return True
    
    def logout_user(self, user_id: str):
        """Logout user and invalidate session"""
        self.remove_active_session(user_id)
        return {'success': True, 'message': 'Logged out successfully'}
    
    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        sessions = self.load_active_sessions()
        current_time = datetime.now()
        
        expired_sessions = []
        for user_id, session in sessions.items():
            created_at = datetime.fromisoformat(session['created_at'])
            if current_time - created_at > timedelta(hours=8):
                expired_sessions.append(user_id)
        
        for user_id in expired_sessions:
            del sessions[user_id]
        
        if expired_sessions:
            self.save_active_sessions(sessions)
        
        return len(expired_sessions)
    
    def update_session_activity(self, user_id: str):
        """Update last activity time for a session"""
        sessions = self.load_active_sessions()
        if user_id in sessions:
            sessions[user_id]['last_activity'] = datetime.now().isoformat()
            self.save_active_sessions(sessions)

# Global auth manager
auth_manager = AuthManager()

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not FLASK_AVAILABLE:
            return f(*args, **kwargs)
            
        user = auth_manager.get_current_user(request)
        if not user:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Authentication required'}), 401
            else:
                return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current authenticated user"""
    if not FLASK_AVAILABLE:
        return None
    return auth_manager.get_current_user(request)
