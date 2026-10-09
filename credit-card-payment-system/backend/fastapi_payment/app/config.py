import os
from pathlib import Path
from dotenv import load_dotenv

env_file = next(
    (
        parent / ".env"
        for parent in Path(__file__).resolve().parents
        if (parent / ".env").is_file()
    ),
    None,
)
if env_file is not None:
    load_dotenv(env_file)

DJANGO_INTERNAL_URL = os.getenv("DJANGO_INTERNAL_URL", "http://localhost:8000")
DJANGO_INTERNAL_SECRET = os.getenv("DJANGO_INTERNAL_SECRET", "")
JWT_SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "")
if len(JWT_SECRET_KEY) < 32:
	raise RuntimeError("DJANGO_SECRET_KEY must contain at least 32 characters.")
JWT_ALGORITHM = "HS256"
CORS_ALLOWED_ORIGINS = [
	origin.strip()
	for origin in os.getenv(
		"CORS_ALLOWED_ORIGINS",
		"http://localhost:5173,http://127.0.0.1:5173",
	).split(",")
	if origin.strip()
]
