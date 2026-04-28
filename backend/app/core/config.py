import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY    = os.getenv("SECRET_KEY",    "traitlytics-secret-2024")
    JWT_SECRET    = os.getenv("JWT_SECRET",    "traitlytics-jwt-secret")
    JWT_EXPIRY    = int(os.getenv("JWT_EXPIRY", 86400))

    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
    POSTGRES_DB   = os.getenv("POSTGRES_DB",   "traitlytics")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "tl_user")
    POSTGRES_PASS = os.getenv("POSTGRES_PASS", "tl_pass")

    @property
    def DATABASE_URL(self):
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASS}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_TTL  = 300

    TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

config = Config()