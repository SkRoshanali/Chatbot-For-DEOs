from pymongo import MongoClient
from werkzeug.security import generate_password_hash
import pyotp

client = MongoClient('mongodb://localhost:27017/')
db = client['deo_chatbot']

# Drop old users
db.users.drop()

users = [
    {'username': 'deo_cse', 'password': 'cse123',   'role': 'DEO',   'dept': 'CSE'},
    {'username': 'hod_cse', 'password': 'hod123',   'role': 'HOD',   'dept': 'CSE'},
    {'username': 'admin',   'password': 'admin123', 'role': 'Admin', 'dept': 'ALL'},
]

for u in users:
    secret = pyotp.random_base32()
    db.users.insert_one({
        'username':   u['username'],
        'password':   generate_password_hash(u['password']),
        'role':       u['role'],
        'dept':       u['dept'],
        'otp_secret': secret
    })
    print(f"Created: {u['username']} | Secret: {secret}")

print("\nDone. Now run: python app.py")
