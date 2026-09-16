from pathlib import Path
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .job_manager import JobManager
from .models import MonitorRequest
from src.monitor_engine import MonitorEngine

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="eCARI Termin Monitor")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "templates")
job_manager = JobManager()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/monitor/start")
async def start_monitor(
    halter_nummer: str = Form(...),
    geburtsdatum: str = Form(...),
    date_from: str = Form(""),
    date_to: str = Form(""),
    location: str = Form(""),
    telegram_token: str = Form(""),
    telegram_chat_id: str = Form(""),
    duration_minutes: int = Form(120),
    interval_minutes: int = Form(12),
):
    duration_minutes = max(10, min(duration_minutes, 1440))
    interval_minutes = max(5, min(interval_minutes, 60))

    config = MonitorRequest(
        halter_nummer=halter_nummer.strip(),
        geburtsdatum=geburtsdatum.strip(),
        date_from=date_from.strip(),
        date_to=date_to.strip(),
        location=location.strip(),
        telegram_token=telegram_token.strip(),
        telegram_chat_id=telegram_chat_id.strip(),
        duration_minutes=duration_minutes,
        interval_minutes=interval_minutes,
    )

    job = job_manager.create_job(config)

    try:
        appointments = MonitorEngine(job).run_check()
        return {
            "success": True,
            "job": job_manager.public_status(job),
            "test_appointments": [
                {"date": a.date, "time": a.time, "location": a.location}
                for a in appointments
            ],
        }
    except Exception:
        job.status = "error"
        job.last_error = "internal_error"
        job.config.halter_nummer = ""
        job.config.geburtsdatum = ""
        job.config.telegram_token = ""
        job.config.telegram_chat_id = ""
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": "Monitor konnte nicht gestartet werden."},
        )

@app.get("/api/monitor/{job_id}")
async def monitor_status(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        return JSONResponse(
            status_code=404,
            content={"error": "Monitor nicht gefunden oder abgelaufen."},
        )
    return job_manager.public_status(job)

@app.post("/api/monitor/{job_id}/stop")
async def stop_monitor(job_id: str):
    job = job_manager.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "Monitor nicht gefunden."})

    job.config.halter_nummer = ""
    job.config.geburtsdatum = ""
    job.config.telegram_token = ""
    job.config.telegram_chat_id = ""
    job.status = "stopped"
    job_manager.delete(job_id)

    return {"success": True, "message": "Monitor beendet."}
