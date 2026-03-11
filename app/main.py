from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Указываем, где лежат шаблоны
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # Передаем request (обязательно для Jinja2 в FastAPI)
    return templates.TemplateResponse("index.html", {"request": request})

# Заглушки для остальных страниц, чтобы ссылки не выдавали 404
@app.get("/projects", response_class=HTMLResponse)
async def projects_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request}) # Пока просто пустая база

@app.get("/tasks", response_class=HTMLResponse)
async def tasks_page(request: Request):
    return templates.TemplateResponse("base.html", {"request": request})