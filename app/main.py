from fastapi import FastAPI
from celery.result import AsyncResult
from app.tasks import infer
from app.schemas import InferRequest, TaskStatus

import logging

logger = logging.getLogger("uvicorn")

app = FastAPI()


# @app.post("/send-email/", response_model=TaskStatus)
# async def send_email_endpoint(request: EmailRequest):
#     task = send_email.delay(request.recipient, request.subject, request.body)
#     return {"task_id": task.id, "status": "Task queued"}


# @app.post("/process-file/", response_model=TaskStatus)
# async def process_file_endpoint(request: FileRequest):
#     task = process_file.delay(request.file_path)
#     return {"task_id": task.id, "status": "Task queued"}


@app.post("/infer/", response_model=TaskStatus)
async def infer_endpoint(request: InferRequest):
    task = infer.delay(request.sents)
    return {"task_id": task.id, "status": "Task queued"}


@app.get("/task-status/{task_id}", response_model=TaskStatus)
async def get_task_status(task_id: str):
    task = AsyncResult(task_id, app=infer.app)
    if task.state == "PENDING":
        response = {"task_id": task_id, "status": "Pending..."}
    elif task.state != "FAILURE":
        result = task.info if not isinstance(task.info, str) else task.info
        response = {
            "task_id": task_id,
            "status": task.state,
            "result": result,
        }
    else:
        response = {"task_id": task_id, "status": "Failed"}

    return response
