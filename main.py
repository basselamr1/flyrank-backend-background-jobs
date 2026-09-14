import datetime
import uuid
from fastapi import FastAPI, HTTPException, status
import inngest
import logging
import inngest.fast_api
from pydantic import BaseModel

app = FastAPI()

inngest_client = inngest.Inngest(
    app_id = "report-api",
    logger = logging.getLogger("uvicorn")
)

reports = {}

class Report(BaseModel):
    topic: str

@inngest_client.create_function(
    fn_id="say-hello",
    trigger=inngest.TriggerEvent(event="test/hello")
) 
async def say_hello(ctx: inngest.Context) -> str:
    ctx.logger.info(ctx.event)
    await ctx.step.sleep("wait 5 seconds", datetime.timedelta(seconds = 5))
    return "Hello from the background!"

@app.get('/health', status_code= status.HTTP_200_OK)
async def check_health():
    return {"status": "ok"}

@app.post('/reports', status_code=status.HTTP_202_ACCEPTED)
async def add_reports(report: Report):
    report_id = str(uuid.uuid4())
    reports[report_id] = {"id": report_id, "topic": report.topic, "status": "pending"}
    await inngest_client.send(inngest.Event(name = "report/requested", data= {"id": report_id, "topic": report.topic}))
    return {"id": report_id, "status": "pending"}

@inngest_client.create_function(
    fn_id="make-report",
    trigger=inngest.TriggerEvent(event="report/requested")
)
async def make_report(ctx: inngest.Context) -> None:
    report_id = ctx.event.data["id"]
    topic = ctx.event.data['topic']

    await ctx.step.sleep("do-the-slow-work", datetime.timedelta(seconds=8))

    def build_report()-> None:
        reports[report_id] = {
            "id": report_id,
            "topic": topic, 
            "status": "done",
            "result": f"The report for {topic} is ready."
        }
    await ctx.step.run("build-report", build_report)

@app.get("/reports/{report_id}")
async def get_report(report_id: str):
    report = reports.get(report_id)
    if report is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found",
        )
    return report

inngest.fast_api.serve(app, inngest_client, [say_hello, make_report],)

