from datetime import datetime,timedelta
from app.models import MonitorRequest,MonitorJob
from src.monitor_engine import MonitorEngine

def main():
    config=MonitorRequest(
        "TEST123","01.01.1990","2026-10-01","2026-12-31",
        "Zürich","","",30,1
    )
    now=datetime.utcnow()
    job=MonitorJob("test-job",config,now,now+timedelta(minutes=30))
    engine=MonitorEngine(job)

    print("=== eCARI TESTMONITOR ===")
    appointments=engine.run_check()
    print(f"Gefundene neue Termine: {len(appointments)}")
    for a in appointments:
        print(f"- {a.date} {a.time} {a.location}")

    appointments=engine.run_check()
    print(f"Neue Termine beim zweiten Check: {len(appointments)}")

if __name__=="__main__":
    main()
