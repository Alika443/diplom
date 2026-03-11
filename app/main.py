import os
from fastapi import FastAPI, Request, Depends, Form, responses
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import engine, Base, get_db
from app.models.project import Project 

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI()

# Путь к шаблонам (лучше сделать его абсолютным, чтобы Windows не путалась)
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

# Указываем, где лежат шаблоны
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
templates_path = os.path.join(base_dir, "templates")
templates = Jinja2Templates(directory=templates_path)

print(f"DEBUG: Путь к шаблонам: {templates_path}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Передаем request (обязательно для Jinja2 в FastAPI)
    return templates.TemplateResponse("index.html", {"request": request})

# Заглушки для остальных страниц, чтобы ссылки не выдавали 404
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.project import Project

@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request, db: Session = Depends(get_db)):
    try:
        # Получаем проекты из базы
        projects = db.query(Project).all()
        # Отправляем их в файл project.html
        return templates.TemplateResponse("projects.html", {
            "request": request, 
            "projects": projects
        })
    except Exception as e:
        return HTMLResponse(content=f"Ошибка: {e}", status_code=500)

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})

    from fastapi import Form, responses # Добавьте Form и responses в импорты

@app.post("/projects/create")
async def create_project(
    title: str = Form(...), 
    description: str = Form(None), 
    db: Session = Depends(get_db)
):
    # Создаем объект проекта
    new_project = Project(title=title, description=description)
    
    # Сохраняем в базу данных
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    
    # После сохранения возвращаемся обратно на страницу проектов
    return responses.RedirectResponse(url="/projects", status_code=303)