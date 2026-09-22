from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import github_api

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="eCARI Termin Monitor")

app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

templates = Jinja2Templates(directory=BASE_DIR / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={},
    )


@app.get("/api/settings")
async def get_settings():
    try:
        config = github_api.get_config()
        return {"success": True, "exam_category": config.get("exam_category", "B")}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)},
        )


@app.post("/api/settings")
async def update_settings(exam_category: str = Form(...)):
    try:
        result = github_api.update_exam_category(exam_category.strip())
        return {"success": True, **result}
    except ValueError as e:
        return JSONResponse(status_code=400, content={"success": False, "error": str(e)})
    except Exception as e:
        return JSONResponse(status_code=500, content={"success": False, "error": str(e)})
