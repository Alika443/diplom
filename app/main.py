import os
from datetime import datetime
from fastapi import FastAPI, Request, Depends, Form, responses
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Импортируем базу и модели
from app.database import engine, Base, get_db
# Убедись, что в app/models/__init__.py прописаны импорты этих классов
from app.models import Project, Task, User 

# Создаем таблицы в БД
Base.metadata.create_all(bind=engine)

app = FastAPI()

# --- НАСТРОЙКА ШАБЛОНОВ ---
# Определяем путь к папке templates относительно текущего файла
current_dir = os.path.dirname(os.path.abspath(__file__)) # папка app
project_root = os.path.dirname(current_dir) # корень проекта
templates_path = os.path.join(project_root, "templates")
templates = Jinja2Templates(directory=templates_path)

# --- МАРШРУТЫ (ROUTES) ---

@app.get("/")
def read_root(request: Request, db: Session = Depends(get_db)):
    # Считаем данные для карточек
    total_projects = db.query(Project).count()
    # Обрати внимание: Task должен быть импортирован выше!
    active_tasks = db.query(Task).filter(Task.status != "Done").count()
    total_users = db.query(User).count()
    
    # Срочные задачи (например, те, что не выполнены)
    urgent_tasks = active_tasks 
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": {
            "projects": total_projects,
            "tasks": active_tasks,
            "users": total_users,
            "urgent": urgent_tasks
        }
    })

    total_projects = db.query(Project).count()
    active_tasks = db.query(Task).count()
    total_users = db.query(User).count()

    # Получаем последние 5 проектов, отсортированных по ID (или дате, если она есть)
    recent_projects = db.query(Project).order_by(Project.id.desc()).limit(5).all()
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "stats": {
            "projects": total_projects,
            "tasks": active_tasks,
            "users": total_users,
            "urgent": active_tasks
        },
        "recent_projects": recent_projects
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

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    # Здесь можно будет позже сделать вывод задач по аналогии с проектами
    return templates.TemplateResponse("base.html", {"request": request})

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
                pass # Если дата пришла в неверном формате
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