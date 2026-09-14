import datetime
from fastapi import FastAPI, status
import inngest
import logging
import inngest.fast_api

app = FastAPI()

inngest_client = inngest.Inngest(
    app_id = "report-api",
    logger = logging.getLogger("uvicorn")
)

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

inngest.fast_api.serve(app, inngest_client, [say_hello],)

