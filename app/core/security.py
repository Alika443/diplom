from datetime import datetime, timedelta
import jwt
import bcrypt
from app.core.config import settings

def get_password_hash(password: str) -> str:
    """Хэширует чистый пароль для сохранения в базу данных"""
    # Переводим строку пароля в байты
    password_bytes = password.encode('utf-8')
    # Генерируем соль и хэшируем
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    # Возвращаем обратно в виде строки для хранения в БД
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверяет, совпадает ли введенный пароль с хэшем из базы"""
    try:
        # Переводим обе строки в байты и сравниваем их через bcrypt
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def create_access_token(data: dict) -> str:
    """Генерирует зашифрованный JWT-токен"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt