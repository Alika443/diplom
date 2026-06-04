import os
from datetime import datetime, date
from fastapi import FastAPI, Request, Depends, Form, responses, Query, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Импортируем базу и модели
from app.database import engine, Base, get_db
from app.models import Project, Task, User 

from fastapi import Response
from fastapi.responses import RedirectResponse

# Импортируем логику безопасности
from app.core.security import get_password_hash, verify_password, create_access_token
from app.services.auth_services import get_current_user
from app.models.user import User 

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI()

# НАСТРОЙКА ШАБЛОНОВ
current_dir = os.path.dirname(os.path.abspath(__file__)) # папка app
project_root = os.path.dirname(current_dir) # корень проекта
templates_path = os.path.join(project_root, "templates")
templates = Jinja2Templates(directory=templates_path)

# МАРШРУТЫ (ROUTES)

# СТРАНИЦЫ АВТОРИЗАЦИИ (ОТОБРАЖЕНИЕ ФОРМ)

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


# ОБРАБОТКА ДАННЫХ ИЗ ФОРМ (POST-ЗАПРОСЫ)

@app.post("/register")
async def handle_register(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):

    print(f"--- ДАННЫЕ ИЗ ФОРМЫ РЕГИСТРАЦИИ ---")
    print(f"Username: {username}, Email: {email}")
    print(f"Password: {password} (Тип: {type(password)}, Длина: {len(str(password))})")
    # Проверяем, нет ли уже пользователя с таким email
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        return templates.TemplateResponse("register.html", {
            "request": request, 
            "error": "Пользователь с таким email уже зарегистрирован"
        })
    
    # Хэшируем пароль перед записью в базу
    clean_password = str(password).strip()
    hashed_pwd = get_password_hash(clean_password)
    
    # Создаем нового пользователя
    new_user = User(username=username, email=email, hashed_password=hashed_pwd)
    db.add(new_user)
    db.commit()
    
    # После успешной регистрации отправляем на страницу входа
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)


@app.post("/login")
async def handle_login(
    response: Response,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Ищем пользователя по email
    user = db.query(User).filter(User.email == email).first()
    
    # Если не нашли или хэш пароля не совпал
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {
            "request": request, 
            "error": "Неверный email или пароль"
        })
    
    # Создаем JWT-токен, зашифровав туда ID пользователя
    access_token = create_access_token(data={"user_id": user.id})
    
    # Создаем редирект на главную страницу
    redirect = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    
    # Записываем токен в Cookies браузера
    redirect.set_cookie(
        key="access_token", 
        value=access_token, 
        httponly=True, # Защита от кражи токена через JavaScript скрипты
        max_age=86400  # Время жизни куки в секундах (1 день)
    )
    return redirect


@app.get("/logout")
async def handle_logout():
    # При выходе просто удаляем куку с токеном из браузера
    redirect = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    redirect.delete_cookie(key="access_token")
    return redirect

from datetime import date

from datetime import date

@app.get("/", response_class=HTMLResponse)
async def index_page(
    request: Request, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Если пользователь не залогинен — отправляем на вход
    if not current_user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
        
    # 2. Извлекаем ВСЕ данные из базы (без фильтрации по owner_id)
    from app.models.task import Task
    from app.models.project import Project
    from app.models.user import User

    user_tasks = db.query(Task).all()
    user_projects = db.query(Project).all()
    total_users_count = db.query(User).count()

    # Все возможные активные статусы, которые есть на твоих скринах
    active_statuses = ["В работе", "In Progress", "Нужно сделать", "To Do", "Приостановлено"]

    # 3. Собираем словарь stats (теперь используем список active_statuses)
    stats = {
        "projects": len(user_projects),
        "total_projects": len(user_projects),
        "tasks": len([t for t in user_tasks if t.status in active_statuses]),
        "total_tasks": len([t for t in user_tasks if t.status in active_statuses]),
        "users": total_users_count,
        "urgent": len([t for t in user_tasks if t.deadline and t.status not in ["Завершено", "Done"]])
    }

    # 4. Вытаскиваем списки для таблиц дашборда (БЕЗ фильтрации по owner_id)
    # Последние проекты
    recent_projects = db.query(Project).order_by(Project.id.desc()).limit(5).all()
    
    # Чтобы блок "Задачи на сегодня" не пустовал, покажем просто последние невыполненные задачи
    tasks_today = [t for t in user_tasks if t.status not in ["Завершено", "Done"]][:5]
    
    # Ближайшие дедлайны (все невыполненные задачи из базы, у которых заполнен дедлайн)
    upcoming_deadlines = db.query(Task).filter(
        Task.status.notin_(["Завершено", "Done"]),
        Task.deadline != None
    ).order_by(Task.deadline.asc()).limit(5).all()

    
    # 5. Отдаем всё в шаблон index.html
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user": current_user,
        "stats": stats,
        "recent_projects": recent_projects,
        "tasks_today": tasks_today,
        "upcoming_deadlines": upcoming_deadlines
    })


@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, db: Session = Depends(get_db)):
    try:
        projects = db.query(Project).all()
        return templates.TemplateResponse("projects.html", {
            "request": request, 
            "projects": projects
        })
    except Exception as e:
        return HTMLResponse(content=f"Ошибка в проектах: {e}", status_code=500)


@app.post("/projects/create")
async def create_project(
    title: str = Form(...), 
    description: str = Form(None), 
    db: Session = Depends(get_db)
):
    new_project = Project(title=title, description=description)
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return responses.RedirectResponse(url="/projects", status_code=303)

@app.post("/projects/delete/{project_id}")
async def delete_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        db.delete(project)
        db.commit()
    return responses.RedirectResponse(url="/projects", status_code=303)

@app.post("/projects/update/{project_id}")
async def update_project(
    project_id: int, 
    title: str = Form(...), 
    status: str = Form(...),
    deadline: str = Form(None),
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.title = title
        project.status = status
        if deadline:
            try:
                project.deadline = datetime.strptime(deadline, '%Y-%m-%d')
            except ValueError:
                pass 
        db.commit()
    return responses.RedirectResponse(url="/projects", status_code=303)

@app.post("/projects/update-status/{project_id}")
async def update_status(
    project_id: int, 
    status: str = Form(...), 
    db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if project:
        project.status = status
        db.commit()
    return responses.RedirectResponse(url="/projects", status_code=303)

@app.get("/search")
async def search(request: Request, q: str = "", type: str = "all", db: Session = Depends(get_db)):
    projects = []
    tasks = []
    users = []

    if type == "all" or type == "projects":
        projects = db.query(Project).filter(Project.title.ilike(f"%{q}%")).all()
    
    if type == "all" or type == "tasks":
        tasks = db.query(Task).filter(Task.title.ilike(f"%{q}%")).all()

    if type == "all" or type == "users":
        users = db.query(User).filter(User.username.ilike(f"%{q}%")).all()

    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "query": q,
        "search_type": type,
        "projects": projects,
        "tasks": tasks,
        "users": users
    })


@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request, status: str = None, db: Session = Depends(get_db)):
    users = db.query(User).all()
    tasks = db.query(Task).all()
    users = db.query(User).all() 
    projects = db.query(Project).all()
    try:
        query = db.query(Task)
        
        # Если передан статус, фильтруем задачи
        if status:
            query = query.filter(Task.status == status)
            
        tasks = query.all()
        projects = db.query(Project).all()
        
        return templates.TemplateResponse("tasks.html", {
            "request": request,
            "tasks": tasks,
            "users": users,
            "projects": projects,
            "current_status": status # Передаем текущий фильтр в шаблон
        })
    except Exception as e:
        return HTMLResponse(content=f"Ошибка: {e}", status_code=500)



@app.post("/tasks/create")
async def create_task(
    title: str = Form(...),
    project_id: str = Form(None),
    owner_id: str = Form(None),    # 1. Добавляем получение ID исполнителя
    deadline: str = Form(None),
    db: Session = Depends(get_db)
):
    # Преобразуем project_id в число или None
    p_id = int(project_id) if project_id and project_id.isdigit() else None
    
    # 2. Преобразуем owner_id в число или None
    o_id = int(owner_id) if owner_id and owner_id.isdigit() else None
    
    # Преобразуем строку даты в объект date
    task_deadline = None
    if deadline:
        try:
            task_deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Создаем новую задачу
    new_task = Task(
        title=title,
        project_id=p_id,
        owner_id=o_id,            # 3. ПЕРЕДАЕМ ИСПОЛНИТЕЛЯ В БАЗУ
        deadline=task_deadline,
        status="To Do"
    )
    
    db.add(new_task)
    db.commit()
    
    return responses.RedirectResponse(url="/tasks", status_code=303)

@app.post("/tasks/create")
async def create_task(
    title: str = Form(...),
    project_id: int = Form(None),
    deadline: str = Form(None),
    db: Session = Depends(get_db)
):
    # Преобразуем строку даты в объект date, если она передана
    task_deadline = None
    if deadline:
        task_deadline = datetime.strptime(deadline, '%Y-%m-%d').date()
    
    new_task = Task(
        title=title,
        project_id=project_id if project_id else None,
        deadline=task_deadline,
        owner_id=o_id,
        status="To Do" # Начальный статус
    )
    
    db.add(new_task)
    db.commit()
    return responses.RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/update-status/{task_id}")
async def update_task_status(
    task_id: int, 
    status: str = Form(...), 
    db: Session = Depends(get_db)
):
    # Ищем задачу в базе
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        task.status = status
        db.commit()
    
    # Возвращаемся обратно на страницу задач
    return responses.RedirectResponse(url="/tasks", status_code=303)


@app.post("/tasks/delete/{task_id}")
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
    return responses.RedirectResponse(url="/tasks", status_code=303)


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Session = Depends(get_db)):
    users = db.query(User).all()
    stats = {}
    
    for user in users:
    # Считаем задачи
        t_count = db.query(Task).filter(Task.owner_id == user.id).count()
    
    # Считаем уникальные проекты, в которых у пользователя есть задачи
        p_count = db.query(Task.project_id).filter(Task.owner_id == user.id).distinct().count()
    
    stats[user.id] = {
        "tasks": t_count,
        "projects": p_count
    }

    return templates.TemplateResponse("users.html", {
        "request": request, 
        "users": users, 
        "stats": stats
    })


@app.post("/users/create")
async def create_user(username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    # Здесь должна быть логика хеширования пароля, но для теста пока так
    new_user = User(username=username, email=email, hashed_password=password) 
    db.add(new_user)
    db.commit()
    return responses.RedirectResponse(url="/users", status_code=303)



@app.get("/search", response_class=HTMLResponse)
async def global_search(request: Request, q: str = Query(""), db: Session = Depends(get_db)):
    results = {"projects": [], "tasks": [], "users": []}
    
    # Очищаем запрос от пробелов
    search_query = q.strip() if q else ""
    
    if search_query:
        print(f"\n--- ВЫПОЛНЯЕТСЯ ПОИСК: '{search_query}' ---")
        
        # Ищем в моделях 
        results["projects"] = db.query(models.project.Project).filter(models.project.Project.title.ilike(f"%{search_query}%")).all()
        results["tasks"] = db.query(models.task.Task).filter(models.task.Task.title.ilike(f"%{search_query}%")).all()
        results["users"] = db.query(models.user.User).filter(models.user.User.username.ilike(f"%{search_query}%")).all()
        
        print(f"Найдено: Задач({len(results['tasks'])}), Проектов({len(results['projects'])})")
    
    return templates.TemplateResponse("search_results.html", {
        "request": request,
        "query": search_query,
        "results": results
    })
    