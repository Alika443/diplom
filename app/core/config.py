import os

class Settings:
    SECRET_KEY: str = "SUPER_SECRET_KEY_FOR_PROJECT_HUB_DIPlOM_2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # Токен будет жить 1 день

settings = Settings()