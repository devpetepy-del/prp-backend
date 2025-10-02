from passlib.context import CryptContext
from .settings import settings
from fastapi.security import HTTPBearer

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = settings.secret_key
ALGORITHM = "HS256"
EXPIRE_MINUTES = settings.access_token_expire_minutes