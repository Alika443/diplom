from fastapi import Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
import jwt
from app.core.config import settings
from app.database import get_db
from app.models.user import User  

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    """
    Зависимость для защиты страниц. Извлекает токен из куки 'access_token',
    проверяет его и возвращает объект текущего пользователя из БД.
    """
    # 1. Пытаемся достать токен из Cookies
    token = request.cookies.get("access_token")
    
    # Если токена нет, выбрасываем ошибку авторизации
    if not token:
         return None

    try:
        # 2. Декодируем токен с помощью секретного ключа
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: int = payload.get("user_id")
        
        if user_id is None:
            return None
            
    except (jwt.PyJWTError, AttributeError):
        return None

    # 3. Ищем пользователя в базе данных
    user = db.query(User).filter(User.id == user_id).first()
    return user