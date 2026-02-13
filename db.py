import os
import datetime
import json
import uuid
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from bson.objectid import ObjectId

# --- JSON Database Fallback ---
class JsonDatabase:
    def __init__(self, filename='local_db.json'):
        self.filename = filename
        self.fallback_filename = os.path.join('/tmp', filename)
        
        # Try to initialize the file
        try:
            if not os.path.exists(self.filename):
                self._save({'users': [], 'history': []})
        except (PermissionError, OSError):
            print(f"Write permission denied for {self.filename}. Using fallback: {self.fallback_filename}")
            self.filename = self.fallback_filename
            if not os.path.exists(self.filename):
                self._save({'users': [], 'history': []})

    def _load(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
             # If file doesn't exist (even fallback), return empty structure
             return {'users': [], 'history': []}
        except Exception as e:
            print(f"Error loading database: {e}")
            return {'users': [], 'history': []}
            
    def _save(self, data):
        try:
            with open(self.filename, 'w') as f:
                json.dump(data, f, indent=4, default=str)
        except (PermissionError, OSError):
             # If we haven't switched to fallback yet, do it now
             if self.filename != self.fallback_filename:
                 print(f"Write failed. Switching to fallback: {self.fallback_filename}")
                 self.filename = self.fallback_filename
                 # Try saving again to fallback
                 with open(self.filename, 'w') as f:
                    json.dump(data, f, indent=4, default=str)

    # Mimic PyMongo's Collection approach slightly differently
    # We will implement helper methods directly
    
    def insert_user(self, user):
        data = self._load()
        user['_id'] = str(uuid.uuid4())
        data['users'].append(user)
        self._save(data)
        return user['_id']
        
    def find_user_by_email(self, email):
        data = self._load()
        for user in data['users']:
            if user.get('email') == email:
                return user
        return None
        
    def find_user_by_id(self, user_id):
        data = self._load()
        for user in data['users']:
            if str(user.get('_id')) == str(user_id):
                return user
        return None
        
    def get_all_users(self):
        return self._load()['users']
        
    def update_user_provider(self, user_id, provider):
        data = self._load()
        for user in data['users']:
            if str(user.get('_id')) == str(user_id):
                user['oauth_provider'] = provider
                self._save(data)
                return True
        return False
        
    def insert_history(self, activity):
        data = self._load()
        # Ensure timestamp is string for JSON
        if isinstance(activity.get('timestamp'), datetime.datetime):
            activity['timestamp'] = activity['timestamp'].isoformat()
        data['history'].append(activity)
        self._save(data)
        
    def get_history_by_user(self, user_id):
        data = self._load()
        return [h for h in data['history'] if str(h.get('user_id')) == str(user_id)]
        
    def get_all_history(self):
        return self._load()['history']

# --- MongoDB Setup with Fallback ---
MONGO_URI = os.environ.get('MONGODB_URI', 'mongodb://localhost:27017/file_automation_db')
USE_MONGO = False
db_client = None

try:
    # Try to connect with a short timeout
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
    client.server_info() # Trigger connection check
    db_client = client.get_default_database()
    USE_MONGO = True
    print("Connected to MongoDB.")
except Exception as e:
    print(f"MongoDB not available ({e}). Using local JSON fallback.")
    db_client = JsonDatabase()
    USE_MONGO = False

# --- User Operations ---
def create_user(email, name, password, role='user'):
    if USE_MONGO:
        if db_client.users.find_one({'email': email}):
            return False, "Email already exists"
        user = {
            'email': email,
            'name': name,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.datetime.utcnow(),
            'oauth_provider': None
        }
        result = db_client.users.insert_one(user)
        return str(result.inserted_id), "User created"
    else:
        if db_client.find_user_by_email(email):
            return False, "Email already exists"
        user = {
            'email': email,
            'name': name,
            'password': generate_password_hash(password),
            'role': role,
            'created_at': datetime.datetime.utcnow().isoformat(),
            'oauth_provider': None
        }
        user_id = db_client.insert_user(user)
        return user_id, "User created"

def get_user_by_email(email):
    if USE_MONGO:
        return db_client.users.find_one({'email': email})
    else:
        return db_client.find_user_by_email(email)

def get_user_by_id(user_id):
    if USE_MONGO:
        try:
            return db_client.users.find_one({'_id': ObjectId(user_id)})
        except:
            return None
    else:
        return db_client.find_user_by_id(user_id)

def verify_user(email, password):
    user = get_user_by_email(email)
    if user and user.get('password') and check_password_hash(user['password'], password):
        return user
    return None

def get_all_users():
    if USE_MONGO:
        return list(db_client.users.find())
    else:
        # Convert JSON strings back to datetime objects if needed
        users = db_client.get_all_users()
        for u in users:
            if isinstance(u.get('created_at'), str):
                try:
                    u['created_at'] = datetime.datetime.fromisoformat(u['created_at'])
                except:
                    pass
        return users

def create_oauth_user(email, name, provider):
    user = get_user_by_email(email)
    
    if user:
        if not user.get('oauth_provider'):
            if USE_MONGO:
                db_client.users.update_one({'_id': user['_id']}, {'$set': {'oauth_provider': provider}})
            else:
                db_client.update_user_provider(user['_id'], provider)
        return user
    else:
        # Create new user
        all_users = get_all_users()
        is_first_user = len(all_users) == 0
        role = 'admin' if is_first_user else 'user'
        
        if USE_MONGO:
            new_user = {
                'email': email,
                'name': name,
                'password': None,
                'role': role,
                'created_at': datetime.datetime.utcnow(),
                'oauth_provider': provider
            }
            result = db_client.users.insert_one(new_user)
            new_user['_id'] = result.inserted_id
            return new_user
        else:
            new_user = {
                'email': email,
                'name': name,
                'password': None,
                'role': role,
                'created_at': datetime.datetime.utcnow().isoformat(),
                'oauth_provider': provider
            }
            user_id = db_client.insert_user(new_user)
            new_user['_id'] = user_id
            return new_user

# --- History Operations ---
def log_activity(user_id, action, details, filename=''):
    activity = {
        'user_id': str(user_id),
        'action': action,
        'details': details,
        'filename': filename,
        'timestamp': datetime.datetime.utcnow()
    }
    
    if USE_MONGO:
        db_client.history.insert_one(activity)
    else:
        db_client.insert_history(activity)

def get_user_history(user_id):
    if USE_MONGO:
        return list(db_client.history.find({'user_id': str(user_id)}).sort('timestamp', -1))
    else:
        history = db_client.get_history_by_user(user_id)
        # Sort and convert timestamps
        for h in history:
            if isinstance(h.get('timestamp'), str):
                try:
                    h['timestamp'] = datetime.datetime.fromisoformat(h['timestamp'])
                except:
                    pass
        return sorted(history, key=lambda x: x.get('timestamp', ''), reverse=True)

def get_all_history():
    if USE_MONGO:
        history = list(db_client.history.find().sort('timestamp', -1))
    else:
        history = db_client.get_all_history()
        for h in history:
            if isinstance(h.get('timestamp'), str):
                try:
                    h['timestamp'] = datetime.datetime.fromisoformat(h['timestamp'])
                except:
                    pass
        history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # Join with user table to get names
    for item in history:
        user = get_user_by_id(item['user_id'])
        item['user_name'] = user['name'] if user else "Unknown"
        item['user_email'] = user['email'] if user else "Unknown"
    return history
