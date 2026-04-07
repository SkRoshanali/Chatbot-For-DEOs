from pymongo import MongoClient
import pyotp
import qrcode

client = MongoClient('mongodb://localhost:27017/')
db = client['deo_chatbot']

users = db.users.find({}, {'username': 1, 'otp_secret': 1})

for user in users:
    secret = user['otp_secret']
    totp   = pyotp.TOTP(secret)
    uri    = totp.provisioning_uri(name=user['username'], issuer_name='DEO Chatbot')

    print(f"\n{'='*50}")
    print(f"User    : {user['username']}")
    print(f"Secret  : {secret}")
    print(f"URI     : {uri}")

    # Save QR code as image
    img = qrcode.make(uri)
    filename = f"qr_{user['username']}.png"
    img.save(filename)
    print(f"QR Code : saved as {filename}")

print(f"\n{'='*50}")
print("Open the PNG files to scan with Google Authenticator.")
