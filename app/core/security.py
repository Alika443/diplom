from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from app.core.config import settings

# Настраиваем контекст для хэширования паролей по алгоритму bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Хэширует чистый пароль для сохранения в базу данных"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хэшем из базы"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    """Генерирует зашифрованный JWT-токен на основе переданных данных (например, user_id)"""
    to_encode = data.copy()
    
    # Считаем время, когда токен просрочится
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    # Кодируем данные в JWT-строку
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt