import os
from datetime import datetime, date
from fastapi import FastAPI, Request, Depends, Form, responses
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Импортируем базу и модели
from app.database import engine, Base, get_db
from app.models import Project, Task, User 

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- НАСТРОЙКА ШАБЛОНОВ ---
current_dir = os.path.dirname(os.path.abspath(__file__)) # папка app
project_root = os.path.dirname(current_dir) # корень проекта
templates_path = os.path.join(project_root, "templates")
templates = Jinja2Templates(directory=templates_path)

# --- МАРШРУТЫ (ROUTES) ---

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    # 1. Считаем общую статистику для верхних карточек
    total_projects = db.query(Project).count()
    active_tasks_count = db.query(Task).filter(Task.status != "Done").count()
    total_users = db.query(User).count()
    
    # 2. Подготавливаем списки для основной части экрана
    today = date.today()
    
    # Последние 5 проектов
    recent_projects = db.query(Project).order_by(Project.id.desc()).limit(5).all()
    
    # Задачи на сегодня (невыполненные)
    tasks_today = db.query(Task).filter(Task.status != "Done").limit(5).all()
    
    # Ближайшие дедлайны (проекты, у которых дедлайн сегодня или позже)
    upcoming_deadlines = db.query(Project).filter(
        Project.deadline >= today
    ).order_by(Project.deadline.asc()).limit(3).all()
    
    # 3. Отправляем ВСЕ данные в один шаблон одним ответом
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": {
            "projects": total_projects,
            "tasks": active_tasks_count,
            "users": total_users,
            "urgent": active_tasks_count
        },
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
async def tasks_page(request: Request, db: Session = Depends(get_db)):
    # Загружаем задачи и проекты (для выпадающего списка в форме)
    tasks = db.query(Task).all()
    projects = db.query(Project).all() 
    return templates.TemplateResponse("tasks.html", {
        "request": request,
        "tasks": tasks,
        "projects": projects
    })


@app.post("/tasks/create")
async def create_task(
    title: str = Form(...),
    project_id: str = Form(None),  # Приходит как строка из формы
    deadline: str = Form(None),
    db: Session = Depends(get_db)
):
    # Преобразуем project_id в число или None
    p_id = int(project_id) if project_id and project_id.isdigit() else None
    
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
        deadline=task_deadline,
        status="To Do"  # Статус по умолчанию
    )
    
    db.add(new_task)
    db.commit()
    
    # После создания возвращаемся на страницу задач
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