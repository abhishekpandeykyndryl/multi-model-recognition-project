# A compact Flask implementation which mirrors the FastAPI behavior.
from flask import Flask, request, jsonify
import os, base64, bcrypt, uuid, datetime, requests
import jwt

app = Flask(__name__)
AZ_FACE_KEY = os.getenv('AZURE_FACE_KEY')
AZ_FACE_ENDPOINT = os.getenv('AZURE_FACE_ENDPOINT')
AZ_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZ_SPEECH_REGION = os.getenv('AZURE_SPEECH_REGION')
JWT_SECRET = os.getenv('JWT_SECRET','changeme')

USERS = {}

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data['email']
    pwd = data['password']
    if email in USERS:
        return jsonify({'error':'exists'}), 400
    pwd_hash = bcrypt.hashpw(pwd.encode('utf8'), bcrypt.gensalt())
    USERS[email] = {'id': str(uuid.uuid4()), 'email': email, 'password_hash': pwd_hash}
    return jsonify({'ok': True})

# ... (for brevity, the Flask file follows similar flows as FastAPI but sync via requests library) ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
