import base64
import json
from typing import Optional
import httpx

class AzureClient:
    def __init__(self, settings):
        self.face_key = settings.azure_face_key
        self.face_endpoint = settings.azure_face_endpoint.rstrip('/') if settings.azure_face_endpoint else None
        self.speech_key = settings.azure_speech_key
        self.speech_region = settings.azure_speech_region
        self.person_group_id = settings.person_group_id
        self._client = httpx.AsyncClient(timeout=20.0)

    async def create_person_if_needed(self, user):
        # Create person group if not exists, then person
        pg_url = f"{self.face_endpoint}/face/v1.0/persongroups/{self.person_group_id}"
        headers = {"Ocp-Apim-Subscription-Key": self.face_key}
        # create person group (idempotent - check status code)
        await self._safe_create(pg_url, headers, json={"name": self.person_group_id})
        # create person
        create_person_url = f"{self.face_endpoint}/face/v1.0/persongroups/{self.person_group_id}/persons"
        r = await self._client.post(create_person_url, headers=headers, json={"name": user.email})
        r.raise_for_status()
        return r.json()['personId']

    async def add_face_to_person(self, person_id: str, image_bytes: bytes):
        url = f"{self.face_endpoint}/face/v1.0/persongroups/{self.person_group_id}/persons/{person_id}/persistedFaces"
        headers = {"Ocp-Apim-Subscription-Key": self.face_key, 'Content-Type': 'application/octet-stream'}
        r = await self._client.post(url, headers=headers, content=image_bytes)
        r.raise_for_status()
        return r.json()

    async def train_person_group(self):
        url = f"{self.face_endpoint}/face/v1.0/persongroups/{self.person_group_id}/train"
        headers = {"Ocp-Apim-Subscription-Key": self.face_key}
        r = await self._client.post(url, headers=headers)
        r.raise_for_status()
        return True

    async def verify_face_to_person(self, image_bytes: bytes, person_id: str) -> float:
        # detect
        detect_url = f"{self.face_endpoint}/face/v1.0/detect"
        headers = {"Ocp-Apim-Subscription-Key": self.face_key, 'Content-Type':'application/octet-stream'}
        r = await self._client.post(detect_url, headers=headers, content=image_bytes)
        r.raise_for_status()
        faces = r.json()
        if not faces:
            return 0.0
        face_id = faces[0]['faceId']
        verify_url = f"{self.face_endpoint}/face/v1.0/verify"
        payload = {"faceId": face_id, "personId": person_id, "personGroupId": self.person_group_id}
        r2 = await self._client.post(verify_url, headers={"Ocp-Apim-Subscription-Key": self.face_key}, json=payload)
        r2.raise_for_status()
        res = r2.json()
        # res contains isIdentical and confidence
        return res.get('confidence', 0.0)

    async def create_speaker_profile(self) -> str:
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/spid/v1.0/verificationProfiles"
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key, 'Content-Type':'application/json'}
        r = await self._client.post(url, headers=headers, json={"locale":"en-US"})
        r.raise_for_status()
        return r.json()['profileId']

    async def enroll_speaker_profile(self, profile_id: str, audio_bytes: bytes):
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/spid/v1.0/verificationProfiles/{profile_id}/enroll"
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key, 'Content-Type':'audio/wav'}
        r = await self._client.post(url, headers=headers, content=audio_bytes)
        r.raise_for_status()
        return r.json()

    async def verify_speaker_profile(self, profile_id: str, audio_bytes: bytes) -> bool:
        url = f"https://{self.speech_region}.api.cognitive.microsoft.com/spid/v1.0/verify?verificationProfileId={profile_id}"
        headers = {"Ocp-Apim-Subscription-Key": self.speech_key, 'Content-Type':'audio/wav'}
        r = await self._client.post(url, headers=headers, content=audio_bytes)
        if r.status_code != 200:
            return False
        res = r.json()
        # res.result usually 'Accept' or 'Reject'
        return res.get('result') == 'Accept'

    async def _safe_create(self, url, headers, json=None):
        # helper to create PG if not exists - ignore if already exists
        r = await self._client.put(url, headers=headers, json=json or {})
        if r.status_code not in (200, 201, 202):
            # 409 if exists or other errors
            pass
        return r
