from pydantic import BaseSettings

class Settings(BaseSettings):
    azure_face_key: str | None = None
    azure_face_endpoint: str | None = None
    azure_speech_key: str | None = None
    azure_speech_region: str | None = None
    person_group_id: str = 'myapp-group'
    jwt_secret: str = 'changeme'

    class Config:
        env_file = '.env'

def get_settings() -> Settings:
    return Settings()
