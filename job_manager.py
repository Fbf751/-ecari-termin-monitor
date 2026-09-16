import secrets
from datetime import datetime, timedelta
from typing import Optional
from .models import MonitorJob, MonitorRequest

class JobManager:
    def __init__(self):
        self.jobs: dict[str, MonitorJob] = {}

    def create_job(self, config: MonitorRequest) -> MonitorJob:
        now = datetime.utcnow()
        job = MonitorJob(
            job_id=secrets.token_urlsafe(12),
            config=config,
            created_at=now,
            expires_at=now + timedelta(minutes=config.duration_minutes),
        )
        self.jobs[job.job_id] = job
        return job

    def get(self, job_id: str) -> Optional[MonitorJob]:
        return self.jobs.get(job_id)

    def delete(self, job_id: str):
        self.jobs.pop(job_id, None)

    def public_status(self, job: MonitorJob):
        return {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at.isoformat(),
            "expires_at": job.expires_at.isoformat(),
            "checks": job.checks,
            "appointments_found": job.appointments_found,
            "last_check": job.last_check.isoformat() if job.last_check else None,
            "last_error": job.last_error,
        }
