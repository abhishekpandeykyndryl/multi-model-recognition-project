import os
import base64
import io
import uuid
import datetime
from typing import Optional
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import jwt
import bcrypt
import httpx
from .deps import get_settings
from .models import UserInDB, SimpleDB
from .azure_client import AzureClient

settings = get_settings()
app = FastAPI(title="azure-mfa-fastapi")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB = SimpleDB()  # in-memory DB for demo; replace with real DB
azure = AzureClient(settings)

JWT_SECRET = settings.jwt_secret
JWT_ALG = "HS256"

class RegisterRequest(BaseModel):
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: Optional[str] = None

@app.post('/register')
async def register(req: RegisterRequest):
    if DB.get_by_email(req.email):
        raise HTTPException(status_code=400, detail='user_exists')
    pwd_hash = bcrypt.hashpw(req.password.encode('utf8'), bcrypt.gensalt())
    user = UserInDB(id=str(uuid.uuid4()), email=req.email, password_hash=pwd_hash)
    DB.save(user)
    return {"ok": True, "user_id": user.id}

@app.post('/enroll/face')
async def enroll_face(email: str = Form(...), file: UploadFile = File(...)):
    user = DB.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail='no_user')
    content = await file.read()
    # call Azure Face REST to create person (if not exists) and add face
    person_id = await azure.create_person_if_needed(user)
    await azure.add_face_to_person(person_id, content)
    await azure.train_person_group()
    user.azure_person_id = person_id
    user.is_enrolled_face = True
    DB.save(user)
    return {"ok": True, "person_id": person_id}

@app.post('/enroll/voice')
async def enroll_voice(email: str = Form(...), file: UploadFile = File(...)):
    user = DB.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail='no_user')
    content = await file.read()
    profile_id = await azure.create_speaker_profile()
    await azure.enroll_speaker_profile(profile_id, content)
    user.azure_speaker_profile_id = profile_id
    user.is_enrolled_voice = True
    DB.save(user)
    return {"ok": True, "profile_id": profile_id}

@app.post('/login')
async def login(email: str = Form(...), password: str = Form(...), face: UploadFile | None = File(None), voice: UploadFile | None = File(None)):
    user = DB.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail='no_user')
    password_ok = bcrypt.checkpw(password.encode('utf8'), user.password_hash)

    face_score = 0.0
    voice_ok = False

    if face and user.azure_person_id:
        face_bytes = await face.read()
        face_score = await azure.verify_face_to_person(face_bytes, user.azure_person_id)

    if voice and user.azure_speaker_profile_id:
        voice_bytes = await voice.read()
        voice_ok = await azure.verify_speaker_profile(user.azure_speaker_profile_id, voice_bytes)

    # policy: password required + (face_score >= 0.7 OR voice_ok)
    if not password_ok:
        raise HTTPException(status_code=401, detail='bad_password')
    if not (face_score >= 0.7 or voice_ok):
        raise HTTPException(status_code=401, detail={'face_score': face_score, 'voice_ok': voice_ok})

    token = jwt.encode({"sub": user.id, "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, JWT_SECRET, algorithm=JWT_ALG)
    return {"token": token, "face_score": face_score, "voice_ok": voice_ok}

# simple health
@app.get('/health')
async def health():
    return {"ok": True}
